import os
import re

import requests as requests
from ipytv import playlist

from lib.config import write_yaml, read_yaml


def download_playlist_file(url, output):
    print(f"Downloading Playlist from url - '{url}'")
    if not os.path.exists(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))
    headers = {
        'User-Agent': 'VLC/3.0.0-git LibVLC/3.0.0-gi',
    }
    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(output, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return output


def parse_playlist(path):
    print(f"Reading M3U from path - '{path}'")
    discovered_streams = {}
    pl = playlist.loadf(path)
    for channel in pl:
        discovered_streams[channel.name] = {
            "name":       channel.name,
            "duration":   channel.duration,
            "url":        channel.url,
            "attributes": channel.attributes,
            "extras":     channel.extras,
        }
    return discovered_streams


def read_data_from_playlist_cache(config, playlist_id):
    return read_yaml(os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.yml"))


def generate_iptv_url(config, url='', service_name=''):
    settings = config.read_settings()
    ffmpeg_args = settings['settings']['default_ffmpeg_pipe_args']
    ffmpeg_args = ffmpeg_args.replace("[URL]", url)
    service_name = re.sub('[^a-zA-Z0-9 \n\.]', '', service_name)
    service_name = re.sub('\s', '-', service_name)
    ffmpeg_args = ffmpeg_args.replace("[SERVICE_NAME]", service_name.lower())
    return f"pipe://ffmpeg {ffmpeg_args}"


def read_playlist_config(config, playlist_id=None):
    settings = config.read_settings()
    if playlist_id is None:
        return settings['playlists']
    for pl_id in settings['playlists']:
        if pl_id == playlist_id:
            print(pl_id)
            return settings['playlists'][pl_id]
    return {}
