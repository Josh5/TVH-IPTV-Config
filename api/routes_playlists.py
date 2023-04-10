#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from lib.epg import prune_playlist_from_channel_sources
from lib.playlist import read_playlist_config, read_streams_from_all_playlists, import_playlist_data, delete_playlist
from lib.tvheadend import configure_playlist_networks
from tvh_iptv_config.api import blueprint
from flask import request, jsonify, current_app

# epg = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'frontend')
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'frontend')
static_assets = os.path.join(frontend_dir, 'dist', 'spa')


@blueprint.route('/tic-api/playlists/get', methods=['GET'])
def api_get_playlists():
    config = current_app.config['APP_CONFIG']
    playlist_config = read_playlist_config(config)
    return jsonify(
        {
            "success": True,
            "data":    playlist_config
        }
    )


@blueprint.route('/tic-api/playlists/streams', methods=['GET'])
def api_get_all_playlist_streams():
    config = current_app.config['APP_CONFIG']
    playlist_streams = read_streams_from_all_playlists(config)
    return jsonify(
        {
            "success": True,
            "data":    playlist_streams
        }
    )


@blueprint.route('/tic-api/playlists/settings/<playlist_id>', methods=['GET'])
def api_get_config_playlists(playlist_id):
    config = current_app.config['APP_CONFIG']
    playlist_config = read_playlist_config(config, playlist_id=playlist_id)
    return jsonify(
        {
            "success": True,
            "data":    playlist_config
        }
    )


@blueprint.route('/tic-api/playlists/settings/<playlist_id>/save', methods=['POST'])
def api_set_config_playlists(playlist_id):
    config = current_app.config['APP_CONFIG']
    # Save settings
    config.update_settings(request.json)
    config.save_settings()
    # Update playlists
    configure_playlist_networks(config)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/playlists/update/<playlist_id>', methods=['POST'])
def api_update_playlist(playlist_id):
    config = current_app.config['APP_CONFIG']
    import_playlist_data(config, playlist_id)
    return jsonify(
        {
            "success": True,
        }
    )


@blueprint.route('/tic-api/playlists/settings/<playlist_id>/delete', methods=['DELETE'])
def api_delete_config_playlists(playlist_id):
    config = current_app.config['APP_CONFIG']
    # Remove playlist from channels
    prune_playlist_from_channel_sources(config, playlist_id)
    # Remove playlist from settings
    delete_playlist(config, playlist_id)
    # Save settings
    config.save_settings()
    return jsonify(
        {
            "success": True
        }
    )
