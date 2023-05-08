#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import logging
import os
import time
from operator import attrgetter
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from backend import db
from backend.ffmpeg import ffprobe_file
from backend.models import Playlist, PlaylistStreams
from backend.tvheadend.tvh_requests import get_tvh, network_template

logger = logging.getLogger('werkzeug.playlists')


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
    try:
        delete_playlist_network_in_tvh(config, net_uuid)
    except Exception as e:
        logger.warning("Failed to remove playlist from TVH by UUID")
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


def store_playlist_streams(config, playlist_id):
    m3u_file = os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.m3u")
    if not os.path.exists(m3u_file):
        # TODO: Add error logging here
        logger.error("No such file '%s'", m3u_file)
        return False
    # Read cache file contents
    with open(m3u_file, encoding="utf8", errors='ignore') as f:
        contents = f.read()
    from ipytv import playlist
    pl = playlist.loads(contents)
    # Delete all existing playlist streams
    stmt = PlaylistStreams.__table__.delete().where(PlaylistStreams.playlist_id == playlist_id)
    db.session.execute(stmt)
    # Add an updated list of streams from the XML file to the DB
    logger.info("Updating list of available streams for playlist #%s from path - '%s'", playlist_id, m3u_file)
    items = []
    for stream in pl:
        items.append(
            PlaylistStreams(
                playlist_id=playlist_id,
                name=stream.name,
                url=stream.url,
                channel_id=stream.attributes.get('channel-id'),
                group_title=stream.attributes.get('group-title'),
                tvg_chno=stream.attributes.get('tvg-chno'),
                tvg_id=stream.attributes.get('tvg-id'),
                tvg_logo=stream.attributes.get('tvg-logo'),
            )
        )
    # Save all new
    db.session.bulk_save_objects(items)
    # Commit all updates to playlist sources
    db.session.commit()
    logger.info("Successfully imported %s streams from path - '%s'", len(items), m3u_file)


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
    logger.info("Downloading updated M3U file for playlist #%s from url - '%s'", playlist_id, playlist['url'])
    start_time = time.time()
    from lib.playlist import download_playlist_file
    m3u_file = os.path.join(config.config_path, 'cache', 'playlists', f"{playlist_id}.m3u")
    download_playlist_file(playlist['url'], m3u_file)
    execution_time = time.time() - start_time
    logger.info("Updated M3U file for playlist #%s was downloaded in '%s' seconds", playlist_id, int(execution_time))
    # Parse the M3U file and cache the data in a YAML file for faster parsing
    logger.info("Importing updated data for playlist #%s", playlist_id)
    start_time = time.time()
    store_playlist_streams(config, playlist_id)
    execution_time = time.time() - start_time
    logger.info("Updated data for playlist #%s was imported in '%s' seconds", playlist_id, int(execution_time))


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


def read_filtered_stream_details_from_all_playlists(request_json):
    results = {
        'streams':          [],
        'records_total':    0,
        'records_filtered': 0,
    }
    query = db.session.query(PlaylistStreams)
    # Get total records count
    results['records_total'] = query.count()
    # Filter results by search value
    search_value = request_json.get('search_value')
    if search_value:
        playlist_rows = (
            db.session.query(Playlist)
            .where(Playlist.name.contains(search_value))
            .all()
        )
        query = query.options(joinedload(PlaylistStreams.playlist)).where(
            or_(PlaylistStreams.name.contains(search_value),
                PlaylistStreams.playlist_id.in_([p.id for p in playlist_rows])))
    # Record filtered records count
    results['records_filtered'] = query.count()
    # Get order by
    order_by_column = request_json.get('order_by')
    if not order_by_column:
        order_by_column = 'name'
    if request_json.get('order_direction', 'desc') == 'asc':
        order_by = attrgetter(order_by_column)(PlaylistStreams).asc()
    else:
        order_by = attrgetter(order_by_column)(PlaylistStreams).desc()
    query = query.order_by(order_by)
    # Limit query results
    length = request_json.get('length', 0)
    start = request_json.get('start', 0)
    if length:
        query = query.limit(length).offset(start)
    # Fetch filtered results
    for result in query.all():
        results['streams'].append({
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
    return results


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
