#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: proxy.py
# Project: TVH-IPTV-Config
# File Created: Thursday, 6th June 2024 11:49:30 pm
# Author: Josh.5 (jsunnex@gmail.com)
# -----
# Last Modified: Friday, 7th June 2024 12:58:25 am
# Modified By: Josh.5 (jsunnex@gmail.com)
###
import logging
from flask import Flask, request, Response, stream_with_context
import requests
from urllib.parse import urljoin, urlencode, urlparse, parse_qs, unquote

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

def add_proxy_arg(url, base_url):
    # Parse the URL to remove query params
    url_parts = list(urlparse(url))
    path = url_parts[2]  # Extract path
    # Check the file extension
    if path.endswith('.m3u8'):
        extension = 'm3u8'
    elif path.endswith('.ts'):
        extension = 'ts'
    else:
        extension = 'unknown'
    # Join all query parameters into the 'url' parameter
    full_url = urljoin(base_url, url)
    query = { 'url': full_url }
    encoded_remote_url = urlencode(query, doseq=True)
    return f'proxy.{extension}?{encoded_remote_url}'

@app.route('/proxy.m3u8', methods=['GET'])
@app.route('/proxy.ts', methods=['GET'])
def proxy():
    app.logger.debug(f"Query parameters: {request.args}")

    upstream_url = request.args.get('url')
    if not upstream_url:
        app.logger.error(f"Missing 'url' query parameter. Received query parameters: {request.args}")
        return Response(f"Missing 'url' query parameter. Received query parameters: {request.args}", status=400)

    # Decode the URL
    upstream_url = unquote(upstream_url)
    app.logger.debug(f"Decoded upstream URL: {upstream_url}")

    app.logger.debug(f"Request for {upstream_url} received")

    # Parse the provided URL
    parsed_url = urlparse(upstream_url)
    path = parsed_url.path
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    app.logger.debug(f"Base URL: {base_url}, Path: {path}")

    # Forward the headers, except for Host
    headers = {key: value for key, value in request.headers if key != 'Host'}
    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    # Log headers and request details
    app.logger.debug(f"Headers: {headers}")
    app.logger.debug(f"Request method: {request.method}")
    app.logger.debug(f"Request path: {request.path}")
    app.logger.debug(f"Request data: {request.get_data()}")
    app.logger.debug(f"Request cookies: {request.cookies}")

    # Forward the request
    resp = requests.request(
        method=request.method,
        url=upstream_url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        stream=True if path.endswith('.ts') else False,
        allow_redirects=True
    )

    # Log the upstream response
    app.logger.debug(f"Upstream response status: {resp.status_code}")
    app.logger.debug(f"Upstream response headers: {resp.headers}")

    # Determine the new base URL from the final response URL after redirects
    final_url = resp.url
    new_base_url = '/'.join(final_url.split('/')[:-1]) + '/'
    app.logger.debug(f"New base URL: {new_base_url}")

    # Modify the playlist content to append the base URL as a query parameter
    if path.endswith(".m3u8"):
        content = resp.text
        app.logger.debug(f"Original Playlist Content:\n{content}")
        lines = content.splitlines()
        updated_lines = []
        for line in lines:
            if line.startswith("#"):
                updated_lines.append(line)
            elif line.strip() == "":  # Preserve blank lines
                updated_lines.append("")
            else:
                updated_lines.append(add_proxy_arg(line, new_base_url))
        content = "\n".join(updated_lines)
        app.logger.debug(f"Modified Playlist Content:\n{content}")
        response = Response(content, resp.status_code, mimetype='application/vnd.apple.mpegurl')
    elif path.endswith(".ts"):
        @stream_with_context
        def generate():
            for chunk in resp.iter_content(chunk_size=4096):
                yield chunk
        response = Response(generate(), resp.status_code, content_type=resp.headers['Content-Type'])
    else:
        response = Response(resp.content, resp.status_code)

    for key, value in resp.headers.items():
        if key.lower() not in ['content-length', 'transfer-encoding', 'content-encoding']:
            response.headers[key] = value
    
    return response

@app.route('/ping', methods=['GET'])
def ping():
    app.logger.debug("Ping request received")
    return "pong", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9987)
