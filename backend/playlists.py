#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
from pprint import pprint

from backend import db
from backend.ffmpeg import ffprobe_file
from backend.models import Playlist, PlaylistStreams
from backend.tvheadend.tvh_requests import get_tvh, network_template
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


def add_new_playlist(config, data):
    playlist = Playlist(
        enabled=data.get('enabled'),
        name=data.get('name'),
        url=data.get('url'),
        connections=data.get('connections'),
    )
    # This is a new entry. Add it to the session before commit
    db.session.add(playlist)
    db.session.commit()
    # Publish changes to TVH
    publish_playlist_networks(config)


def update_playlist(config, playlist_id, data):
    playlist = db.session.query(Playlist).where(Playlist.id == playlist_id).one()
    playlist.enabled = data.get('enabled')
    playlist.name = data.get('name')
    playlist.url = data.get('url')
    playlist.connections = data.get('connections')
    db.session.commit()
    # Publish changes to TVH
    publish_playlist_networks(config)


def delete_playlist(config, playlist_id):
    playlist = db.session.query(Playlist).where(Playlist.id == playlist_id).one()
    net_uuid = playlist.tvh_uuid
    # Remove from TVH
    delete_playlist_network_in_tvh(config, net_uuid)
    # Remove cached copy of playlist
    cache_files = [
        os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.m3u"),
        os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.yml"),
    ]
    for f in cache_files:
        if os.path.isfile(f):
            os.remove(f)
    # Remove from DB
    db.session.delete(playlist)
    db.session.commit()


def store_playlist_streams(playlist_id, playlist_data):
    items = []
    for key in playlist_data:
        data = playlist_data[key]
        items.append(
            PlaylistStreams(
                playlist_id=playlist_id,
                name=data['name'],
                url=data['url'],
                channel_id=data.get('attributes', {}).get('channel-id'),
                group_title=data.get('attributes', {}).get('group-title'),
                tvg_chno=data.get('attributes', {}).get('tvg-chno'),
                tvg_id=data.get('attributes', {}).get('tvg-id'),
                tvg_logo=data.get('attributes', {}).get('tvg-logo'),
            )
        )
    # Delete all existing playlist channels
    stmt = PlaylistStreams.__table__.delete().where(PlaylistStreams.playlist_id == playlist_id)
    db.session.execute(stmt)
    # Save all new
    db.session.bulk_save_objects(items)
    db.session.commit()


def fetch_playlist_streams(playlist_id):
    return_list = {}
    for result in db.session.query(PlaylistStreams).where(PlaylistStreams.playlist_id == playlist_id).all():
        return_list[result.name] = {
            'name':        result.name,
            'url':         result.url,
            'channel_id':  result.channel_id,
            'group_title': result.group_title,
            'tvg_chno':    result.tvg_chno,
            'tvg_id':      result.tvg_id,
            'tvg_logo':    result.tvg_logo,
        }
    return return_list


def import_playlist_data(config, playlist_id):
    playlist = read_config_one_playlist(playlist_id)
    # Download playlist data and save to YAML cache file
    from lib.playlist import download_playlist_file
    m3u_file = os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.m3u")
    download_playlist_file(playlist['url'], m3u_file)
    # Parse the M3U file and cache the data in a YAML file for faster parsing
    playlist_data = parse_playlist(m3u_file)
    store_playlist_streams(playlist_id, playlist_data)


def import_playlist_data_for_all_playlists(config):
    for playlist in db.session.query(Playlist).all():
        import_playlist_data(config, playlist.id)


def read_stream_details_from_all_playlists():
    playlist_streams = {
        'streams': []
    }
    for result in db.session.query(PlaylistStreams).all():
        playlist_streams['streams'].append({
            'id':            result.id,
            'playlist_id':   result.playlist_id,
            'playlist_name': result.playlist.name,
            'name':          result.name,
            'url':           result.url,
            'channel_id':    result.channel_id,
            'group_title':   result.group_title,
            'tvg_chno':      result.tvg_chno,
            'tvg_id':        result.tvg_id,
            'tvg_logo':      result.tvg_logo,
        })
    return playlist_streams


def delete_playlist_network_in_tvh(config, net_uuid):
    tvh = get_tvh(config)
    tvh.delete_network(net_uuid)


def publish_playlist_networks(config):
    tvh = get_tvh(config)

    # Loop over configured playlists
    existing_uuids = []
    net_priority = 0
    for result in db.session.query(Playlist).all():
        net_priority += 1
        net_uuid = result.tvh_uuid
        playlist_name = result.name
        max_streams = result.connections
        network_name = f"playlist_{result.id}_{result.name}"
        if net_uuid:
            found = False
            for net in tvh.list_cur_networks():
                if net.get('uuid') == net_uuid:
                    found = True
            if not found:
                net_uuid = None
        if not net_uuid:
            # No network exists, create one
            # Check if network exists with this playlist name
            net_uuid = tvh.create_network(playlist_name, network_name, max_streams, net_priority)
        # Update network
        net_conf = network_template.copy()
        net_conf['uuid'] = net_uuid
        net_conf['enabled'] = result.enabled
        net_conf['networkname'] = playlist_name
        net_conf['pnetworkname'] = network_name
        net_conf['max_streams'] = max_streams
        net_conf['priority'] = net_priority
        tvh.idnode_save(net_conf)
        # Save network UUID against playlist in settings
        result.tvh_uuid = net_uuid
        db.session.commit()
        # Append to list of current network UUIDs
        existing_uuids.append(net_uuid)

    #  TODO: Remove any networks that are not managed. DONT DO THIS UNTIL THINGS ARE ALL WORKING!


def probe_playlist_stream(playlist_stream_id):
    playlist_stream = db.session.query(PlaylistStreams).where(PlaylistStreams.id == playlist_stream_id).one()
    probe_data = ffprobe_file(playlist_stream.url)
    return probe_data
