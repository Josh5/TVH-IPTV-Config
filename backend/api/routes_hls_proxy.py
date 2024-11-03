#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import asyncio
import base64
import os
import time

from quart import current_app, Response

from backend.api import blueprint
import aiohttp
from urllib.parse import urlparse

# Test:
#       > mkfifo /tmp/ffmpegpipe
#       > ffmpeg -probesize 10M -analyzeduration 0 -fpsprobesize 0 -i "<URL>" -c copy -y -f mpegts /tmp/ffmpegpipe
#       > vlc /tmp/ffmpegpipe
#
#   Or:
#       > ffmpeg -probesize 10M -analyzeduration 0 -fpsprobesize 0 -i "<URL>" -c copy -y -f mpegts - | vlc -
#

hls_proxy_prefix = os.environ.get('HLS_PROXY_PREFIX', '/')
if not hls_proxy_prefix.startswith("/"):
    hls_proxy_prefix = "/" + hls_proxy_prefix

hls_proxy_host_ip = os.environ.get('HLS_PROXY_HOST_IP')
hls_proxy_port = os.environ.get('HLS_PROXY_PORT')


class InMemoryCache:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InMemoryCache, cls).__new__(cls)
            cls._instance.cache = {}
            cls._instance.expiration_times = {}
        return cls._instance

    async def get(self, key):
        async with self._lock:
            return self.cache.get(key)

    async def set(self, key, value, expiration_time=None):
        if expiration_time is None:
            expiration_time = 30
        async with self._lock:
            self.cache[key] = value
            # Set expiration time; use default if not provided
            self.expiration_times[key] = time.time() + expiration_time

    async def exists(self, key):
        async with self._lock:
            current_time = time.time()
            # Check if the key exists in both cache and expiration_times, and if it hasn't expired
            if key in self.cache and key in self.expiration_times and (current_time <= self.expiration_times[key]):
                return True
            return False

    async def delete(self, key):
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                del self.expiration_times[key]

    async def evict_expired_items(self):
        async with self._lock:
            current_time = time.time()
            keys_to_delete = [key for key, expiration_time in self.expiration_times.items() if
                              current_time > expiration_time]
            for key in keys_to_delete:
                del self.cache[key]
                del self.expiration_times[key]


cache = InMemoryCache()


async def periodic_cache_cleanup():
    while True:
        await cache.evict_expired_items()
        await asyncio.sleep(60)  # Evict every minute


async def prefetch_segments(segment_urls):
    async with aiohttp.ClientSession() as session:
        for url in segment_urls:
            if not await cache.exists(url):
                current_app.logger.info("[CACHE] Saved URL '%s' to cache", url)
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            await cache.set(url, content, expiration_time=30)  # Cache for 30 seconds
                except Exception as e:
                    current_app.logger.error("Failed to prefetch URL '%s': %s", url, e)


def generate_base64_encoded_url(url_to_encode, extension):
    full_url_encoded = base64.b64encode(url_to_encode.encode('utf-8')).decode('utf-8')
    host_base_url = ''
    host_base_url_prefix = 'http'
    host_base_url_port = ''
    if hls_proxy_port:
        if hls_proxy_port == '443':
            host_base_url_prefix = 'https'
        host_base_url_port = f':{hls_proxy_port}'
    if hls_proxy_host_ip:
        host_base_url = f'{host_base_url_prefix}://{hls_proxy_host_ip}{host_base_url_port}{hls_proxy_prefix}/'
    return f'{host_base_url}{full_url_encoded}.{extension}'


async def fetch_and_update_playlist(decoded_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(decoded_url) as resp:
            if resp.status != 200:
                return None

            # Get actual URL after any redirects
            parsed_response_url = urlparse(str(resp.url))
            response_url = f"{parsed_response_url.scheme}://{parsed_response_url.hostname}"

            # Read the original playlist content
            playlist_content = await resp.text()

            # Update child URLs in the playlist
            updated_playlist = update_child_urls(playlist_content, response_url)
            return updated_playlist


def get_key_uri_from_ext_x_key(line):
    """
    Extract the URI value from an #EXT-X-KEY line.
    """
    parts = line.split(',')
    for part in parts:
        if part.startswith('URI='):
            return part.split('=', 1)[1].strip('"')
    return None


def update_child_urls(playlist_content, source_url):
    current_app.logger.debug(f"Original Playlist Content:\n{playlist_content}")

    updated_lines = []
    lines = playlist_content.splitlines()
    segment_urls = []

    # Generate the source base URL
    parsed_source_base_url = urlparse(source_url)
    source_base_url = f"{parsed_source_base_url.scheme}://{parsed_source_base_url.hostname}"

    for line in lines:
        stripped_line = line.strip()

        # Ignore empty lines
        if not stripped_line:
            continue

        # Lines starting with # are preserved as is
        if line.startswith("#EXT-X-KEY"):
            key_uri = get_key_uri_from_ext_x_key(line)
            if key_uri:
                new_key_uri = generate_base64_encoded_url(key_uri, 'key')
                updated_lines.append(line.replace(key_uri, new_key_uri))
                segment_urls.append(key_uri)
            else:
                updated_lines.append(line)
            continue
        elif stripped_line.startswith('#'):
            updated_lines.append(line)
            continue

        # Encode regular URL lines
        extension = 'ts'
        if stripped_line.endswith('m3u8'):
            extension = 'm3u8'
        url_to_encode = f"{source_base_url}/{stripped_line}"
        updated_lines.append(generate_base64_encoded_url(url_to_encode, extension))

        # Add any ts files to list of segments to pre-fetch
        if extension == 'ts':
            segment_urls.append(url_to_encode)

    # Start prefetching segments in the background
    asyncio.create_task(prefetch_segments(segment_urls))

    # Join the updated lines into a single string
    modified_playlist = "\n".join(updated_lines)
    current_app.logger.debug(f"Modified Playlist Content:\n{modified_playlist}")
    return modified_playlist


@blueprint.route(f'{hls_proxy_prefix.lstrip("/")}/<encoded_url>.m3u8', methods=['GET'])
async def proxy_m3u8(encoded_url):
    # Decode the Base64 encoded URL
    decoded_url = base64.b64decode(encoded_url).decode('utf-8')

    updated_playlist = await fetch_and_update_playlist(decoded_url)
    if updated_playlist is None:
        current_app.logger.error("Failed to fetch the original playlist '%s'", decoded_url)
        return Response("Failed to fetch the original playlist.", status=404)

    current_app.logger.info(f"[MISS] Serving m3u8 URL '%s' without cache", decoded_url)
    return Response(updated_playlist, content_type='application/vnd.apple.mpegurl')


@blueprint.route(f'{hls_proxy_prefix.lstrip("/")}/<encoded_url>.key', methods=['GET'])
async def proxy_key(encoded_url):
    # Decode the Base64 encoded URL
    decoded_url = base64.b64decode(encoded_url).decode('utf-8')

    # Check if the .key file is already cached
    if await cache.exists(decoded_url):
        current_app.logger.info(f"[HIT] Serving key URL from cache: %s", decoded_url)
        cached_content = await cache.get(decoded_url)
        return Response(cached_content, content_type='application/octet-stream')

    # If not cached, fetch the file and cache it
    current_app.logger.info(f"[MISS] Serving key URL '%s' without cache", decoded_url)
    async with aiohttp.ClientSession() as session:
        async with session.get(decoded_url) as resp:
            if resp.status != 200:
                current_app.logger.error("Failed to fetch key file '%s'", decoded_url)
                return Response("Failed to fetch the file.", status=404)
            content = await resp.read()
            await cache.set(decoded_url, content, expiration_time=30)  # Cache for 30 seconds
            return Response(content, content_type='application/octet-stream')


@blueprint.route(f'{hls_proxy_prefix.lstrip("/")}/<encoded_url>.ts', methods=['GET'])
async def proxy_ts(encoded_url):
    # Decode the Base64 encoded URL
    decoded_url = base64.b64decode(encoded_url).decode('utf-8')

    # Check if the .ts file is already cached
    if await cache.exists(decoded_url):
        current_app.logger.info(f"[HIT] Serving ts URL from cache: %s", decoded_url)
        cached_content = await cache.get(decoded_url)
        return Response(cached_content, content_type='video/mp2t')

    # If not cached, fetch the file and cache it
    current_app.logger.info(f"[MISS] Serving ts URL '%s' without cache", decoded_url)
    async with aiohttp.ClientSession() as session:
        async with session.get(decoded_url) as resp:
            if resp.status != 200:
                current_app.logger.error("Failed to fetch ts file '%s'", decoded_url)
                return Response("Failed to fetch the file.", status=404)
            content = await resp.read()
            await cache.set(decoded_url, content, expiration_time=30)  # Cache for 30 seconds
            return Response(content, content_type='video/mp2t')
