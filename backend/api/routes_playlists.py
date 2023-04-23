#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from backend.playlists import read_config_all_playlists, add_new_playlist, read_config_one_playlist, update_playlist, \
    delete_playlist, import_playlist_data, read_stream_details_from_all_playlists
from backend.api import blueprint
from flask import request, jsonify, current_app

frontend_dir = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'frontend')
static_assets = os.path.join(frontend_dir, 'dist', 'spa')


@blueprint.route('/tic-api/playlists/get', methods=['GET'])
def api_get_playlists_list():
    all_playlist_configs = read_config_all_playlists()
    return jsonify(
        {
            "success": True,
            "data":    all_playlist_configs
        }
    )


@blueprint.route('/tic-api/playlists/new', methods=['POST'])
def api_add_new_playlist():
    config = current_app.config['APP_CONFIG']
    add_new_playlist(config, request.json)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/playlists/settings/<playlist_id>', methods=['GET'])
def api_get_playlist_config(playlist_id):
    playlist_config = read_config_one_playlist(playlist_id)
    return jsonify(
        {
            "success": True,
            "data":    playlist_config
        }
    )


@blueprint.route('/tic-api/playlists/settings/<playlist_id>/save', methods=['POST'])
def api_set_config_playlists(playlist_id):
    config = current_app.config['APP_CONFIG']
    update_playlist(config, playlist_id, request.json)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/playlists/<playlist_id>/delete', methods=['DELETE'])
def api_delete_playlist(playlist_id):
    config = current_app.config['APP_CONFIG']
    delete_playlist(config, playlist_id)
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


@blueprint.route('/tic-api/playlists/streams', methods=['GET'])
def api_get_all_playlist_streams():
    playlist_streams = read_stream_details_from_all_playlists()
    return jsonify(
        {
            "success": True,
            "data":    playlist_streams
        }
    )


@blueprint.route('/tic-api/playlists/channels', methods=['GET'])
def api_get_all_playlist_channels():
    playlist_streams = read_channel_details_from_all_playlists()
    return jsonify(
        {
            "success": True,
            "data":    playlist_streams
        }
    )
