#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from backend import db
from backend.models import Playlist
from lib.config import write_yaml
from lib.playlist import parse_playlist


def read_config_all_playlists():
    return_list = []
    for result in db.session.query(Playlist).all():
        return_list.append({
            'id':          result.id,
            'enabled':     result.enabled,
            'connections': result.connections,
            'name':        result.name,
            'url':         result.url,
        })
    return return_list


def read_config_one_playlist(playlist_id):
    return_item = {}
    result = db.session.query(Playlist).filter(Playlist.id == playlist_id).one()
    if result:
        return_item = {
            'id':          result.id,
            'enabled':     result.enabled,
            'name':        result.name,
            'url':         result.url,
            'connections': result.connections,
        }
    return return_item


def add_new_playlist(data):
    playlist = Playlist(
        enabled=data.get('enabled'),
        name=data.get('name'),
        url=data.get('url'),
        connections=data.get('connections'),
    )
    # This is a new entry. Add it to the session before commit
    db.session.add(playlist)
    db.session.commit()


def update_playlist(playlist_id, data):
    playlist = db.session.query(Playlist).where(Playlist.id == playlist_id).one()
    playlist.enabled = data.get('enabled')
    playlist.name = data.get('name')
    playlist.url = data.get('url')
    playlist.connections = data.get('connections')
    db.session.commit()


def delete_playlist(config, playlist_id):
    playlist = db.session.query(Playlist).where(Playlist.id == playlist_id).one()
    db.session.delete(playlist)
    db.session.commit()
    # Remove cached copy of playlist
    cache_files = [
        os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.m3u"),
        os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.yml"),
    ]
    for f in cache_files:
        if os.path.isfile(f):
            os.remove(f)


def import_playlist_data(config, playlist_id):
    playlist = read_config_one_playlist(playlist_id)
    # Download playlist data and save to YAML cache file
    from lib.playlist import download_playlist_file
    m3u_file = os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.m3u")
    download_playlist_file(playlist['url'], m3u_file)
    # Parse the M3U file and cache the data in a YAML file for faster parsing
    remote_playlist_data = parse_playlist(m3u_file)
    playlist_yaml_file = os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.yml")
    write_yaml(playlist_yaml_file, remote_playlist_data)
