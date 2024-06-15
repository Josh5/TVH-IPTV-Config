#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import asyncio
import base64
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from quart import request, current_app, Response, stream_with_context, Quart
from requests.exceptions import InvalidURL

from backend.api import blueprint
import aiohttp
from urllib.parse import urljoin, urlencode, urlparse, unquote

hls_proxy_path = 'tic-hls-proxy'


# Test:
#       > mkfifo /tmp/ffmpegpipe
#       > ffmpeg -probesize 10M -analyzeduration 0 -fpsprobesize 0 -i "<URL>" -c copy -y -f mpegts /tmp/ffmpegpipe
#       > vlc /tmp/ffmpegpipe
#
#   Or:
#       > ffmpeg  -probesize 50M -analyzeduration 0 -fpsprobesize 0 -i "<URL>" -c copy -y -f mpegts - | vlc -
#

class InMemoryCache:
    _instance = None
    _lock = asyncio.Lock()
    _expiration_time = 300  # 5 minutes

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InMemoryCache, cls).__new__(cls)
            cls._instance.cache = {}
            cls._instance.timestamps = {}
        return cls._instance

    async def get(self, key):
        async with self._lock:
            return self.cache.get(key)

    async def set(self, key, value):
        async with self._lock:
            self.cache[key] = value
            self.timestamps[key] = time.time()

    async def exists(self, key):
        async with self._lock:
            return key in self.cache

    async def delete(self, key):
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]

    async def evict_expired_items(self):
        async with self._lock:
            current_time = time.time()
            keys_to_delete = [key for key, timestamp in self.timestamps.items() if
                              current_time - timestamp > self._expiration_time]
            for key in keys_to_delete:
                del self.cache[key]
                del self.timestamps[key]


cache = InMemoryCache()
executor = ThreadPoolExecutor(max_workers=10)


def get_cache_key(url):
    return hashlib.md5(url.encode()).hexdigest()


async def send_from_cache(cache_key, content_type='video/MP2T'):
    cached_data = await cache.get(cache_key)

    @stream_with_context
    async def generate():
        yield cached_data

    return Response(generate(), status=200, content_type=content_type)


def add_proxy_arg(url, base_url):
    url_parts = list(urlparse(url))
    path = url_parts[2]
    if path.endswith('.m3u8'):
        extension = 'm3u8'
    elif path.endswith('.ts'):
        extension = 'ts'
    else:
        extension = 'unknown'
    full_url = urljoin(base_url, url)
    full_url_encoded = base64.urlsafe_b64encode(full_url.encode()).decode()
    return f'{hls_proxy_path}.{extension}?encoded_remote={full_url_encoded}'


async def get_upstream_url():
    current_app.logger.debug(f"Query parameters: {request.args}")

    upstream_url = request.args.get('url')
    key_cache_id = request.args.get('key_cache_id')
    encoded_remote = request.args.get('encoded_remote')
    if key_cache_id:
        return None, key_cache_id, None
    elif encoded_remote:
        try:
            upstream_url = base64.urlsafe_b64decode(encoded_remote).decode()
        except Exception as e:
            current_app.logger.error(f"Failed to decode encoded_remote '%s': %s", encoded_remote, e)
            error_response = [f"Invalid 'encoded_remote' parameter", 400]
            return error_response, None, None
    else:
        if not upstream_url:
            current_app.logger.error(f"Missing 'url' query parameter. Received query parameters: {request.args}")
            error_response = [f"Missing 'url' query parameter. Received query parameters: {request.args}", 400]
            return error_response, None, None

    upstream_url = unquote(upstream_url)
    current_app.logger.debug(f"Decoded upstream URL: {upstream_url}")
    current_app.logger.debug(f"Request for {upstream_url} received")

    # Parse the provided URL
    parsed_url = urlparse(upstream_url)
    path = parsed_url.path
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    current_app.logger.debug(f"Base URL: {base_url}, Path: {path}")

    # Forward the headers, except for Host
    headers = {key: value for key, value in request.headers.items() if key != 'Host'}
    headers[
        'User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    # Log headers and request details
    current_app.logger.debug(f"Headers: {headers}")
    current_app.logger.debug(f"Request method: {request.method}")
    current_app.logger.debug(f"Request path: {request.path}")
    current_app.logger.debug(f"Request data: {await request.get_data()}")
    current_app.logger.debug(f"Request cookies: {request.cookies}")

    return None, upstream_url, headers


async def evict_cache_task():
    await cache.evict_expired_items()


async def cache_url_file(url, headers):
    cache_key = get_cache_key(url)
    if await cache.exists(cache_key):
        return cache_key

    try:
        def fetch(u, h):
            return requests.get(u, headers=h, stream=True, allow_redirects=True)

        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, fetch, url, headers)

        data = bytearray()
        for chunk in resp.iter_content(chunk_size=4096):
            data.extend(chunk)
        await cache.set(cache_key, data)
        current_app.logger.info(f"Saved URL '%s' to cache: %s", url, cache_key)
    except Exception as e:
        current_app.logger.info(f"Failed to cache URL '%s' to cache: %s - %s", url, cache_key, e)

    return cache_key


def get_key_uri_from_ext_x_key(line):
    """
    Extract the URI value from an #EXT-X-KEY line.
    """
    parts = line.split(',')
    for part in parts:
        if part.startswith('URI='):
            return part.split('=', 1)[1].strip('"')
    return None


@blueprint.route(f'/{hls_proxy_path}.m3u8', methods=['GET'])
async def hls_proxy_m3u8():
    error_response, upstream_url, headers = await get_upstream_url()
    if error_response:
        return Response(error_response[0], status=error_response[1])

    async with aiohttp.ClientSession() as session:
        async with session.request(
                method=request.method,
                url=upstream_url,
                headers=headers,
                data=await request.get_data(),
                cookies=request.cookies,
                allow_redirects=True) as resp:

            current_app.logger.debug(f"Upstream response status: {resp.status}")
            current_app.logger.debug(f"Upstream response headers: {resp.headers}")

            final_url = str(resp.url)
            new_base_url = '/'.join(final_url.split('/')[:-1]) + '/'
            current_app.logger.debug(f"New base URL: {new_base_url}")

            content = await resp.text()
            current_app.logger.debug(f"Original Playlist Content:\n{content}")
            lines = content.splitlines()
            updated_lines = []
            for line in lines:
                if line.startswith("#EXT-X-KEY"):
                    key_uri = get_key_uri_from_ext_x_key(line)
                    if key_uri:
                        key_url = urljoin(new_base_url, key_uri)
                        key_cache_id = await cache_url_file(key_url, headers)
                        updated_line = line.replace(key_uri, f'{hls_proxy_path}.key?key_cache_id={key_cache_id}')
                        updated_lines.append(updated_line)
                    else:
                        updated_lines.append(line)
                elif line.startswith("#"):
                    updated_lines.append(line)
                elif line.strip() == "":
                    updated_lines.append("")
                else:
                    parsed_line = urlparse(line)
                    path = parsed_line.path
                    if path.endswith(".ts"):
                        ts_url = urljoin(new_base_url, line)
                        current_app.add_background_task(cache_url_file, ts_url, headers)
                    updated_lines.append(add_proxy_arg(line, new_base_url))
            current_app.add_background_task(evict_cache_task)
            content = "\n".join(updated_lines)
            current_app.logger.debug(f"Modified Playlist Content:\n{content}")
            response = Response(content, resp.status, content_type=resp.headers['Content-Type'])

            for key, value in resp.headers.items():
                if key.lower() not in ['content-length', 'transfer-encoding', 'content-encoding']:
                    response.headers[key] = value

            return response


@blueprint.route(f'/{hls_proxy_path}.key', methods=['GET'])
async def hls_proxy_key():
    key_cache_id = request.args.get('key_cache_id')
    if not key_cache_id:
        current_app.logger.error(f"Missing 'key_cache_id' query parameter. Received query parameters: {request.args}")
        return Response(f"Missing 'key_cache_id' query parameter. Received query parameters: {request.args}",
                        status=400)

    if await cache.exists(key_cache_id):
        current_app.logger.info(f"Serving key URL from cache: %s", key_cache_id)
        return await send_from_cache(key_cache_id, content_type="binary/octet-stream")


@blueprint.route(f'/{hls_proxy_path}.ts', methods=['GET'])
async def hls_proxy_ts():
    error_response, upstream_url, headers = await get_upstream_url()
    if error_response:
        return Response(error_response[0], status=error_response[1])

    cache_key = get_cache_key(upstream_url)

    if await cache.exists(cache_key):
        current_app.logger.info(f"Serving URL '%s' from cache: %s", upstream_url, cache_key)
        return await send_from_cache(cache_key)

    try:
        def fetch(u, h, d, c):
            return requests.request(
                method='GET',
                url=u,
                headers=h,
                data=d,
                cookies=c,
                stream=True,
                allow_redirects=True
            )

        request_data = await request.get_data()
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, fetch, upstream_url, headers, request_data, request.cookies)
    except InvalidURL as e:
        current_app.logger.debug(f"Request was supplied an invalid URL: %s", e)
        return Response(f"Request was supplied an invalid URL", status=400)

    current_app.logger.debug(f"Upstream response status: {resp.status_code}")
    current_app.logger.debug(f"Upstream response headers: {resp.headers}")

    async def generate():
        while True:
            chunk = await loop.run_in_executor(None, lambda: resp.raw.read(4096))
            if not chunk:
                break
            yield chunk

    response = Response(generate(), resp.status_code, content_type=resp.headers['Content-Type'])

    for key, value in resp.headers.items():
        if key.lower() not in ['content-length', 'transfer-encoding', 'content-encoding']:
            response.headers[key] = value

    return response
