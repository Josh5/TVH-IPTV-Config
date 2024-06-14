#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from backend.api.tasks import TaskQueueBroker
from backend.channels import queue_background_channel_update_tasks
from backend.playlists import read_config_all_playlists, add_new_playlist, read_config_one_playlist, update_playlist, \
    delete_playlist, import_playlist_data, read_stream_details_from_all_playlists, probe_playlist_stream, \
    read_filtered_stream_details_from_all_playlists
from backend.api import blueprint
from quart import request, jsonify, current_app

frontend_dir = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'frontend')
static_assets = os.path.join(frontend_dir, 'dist', 'spa')


@blueprint.route('/tic-api/playlists/get', methods=['GET'])
async def api_get_playlists_list():
    all_playlist_configs = await read_config_all_playlists()
    return jsonify(
        {
            "success": True,
            "data":    all_playlist_configs
        }
    )


@blueprint.route('/tic-api/playlists/new', methods=['POST'])
async def api_add_new_playlist():
    json_data = await request.get_json()
    config = current_app.config['APP_CONFIG']
    add_new_playlist(config, json_data)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/playlists/settings/<playlist_id>', methods=['GET'])
async def api_get_playlist_config(playlist_id):
    playlist_config = await read_config_one_playlist(playlist_id)
    return jsonify(
        {
            "success": True,
            "data":    playlist_config
        }
    )


@blueprint.route('/tic-api/playlists/settings/<playlist_id>/save', methods=['POST'])
async def api_set_config_playlists(playlist_id):
    json_data = await request.get_json()
    config = current_app.config['APP_CONFIG']
    await update_playlist(config, playlist_id, json_data)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/playlists/<playlist_id>/delete', methods=['DELETE'])
def api_delete_playlist(playlist_id):
    config = current_app.config['APP_CONFIG']
    delete_playlist(config, playlist_id)
    queue_background_channel_update_tasks(config)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/playlists/update/<playlist_id>', methods=['POST'])
async def api_update_playlist(playlist_id):
    config = current_app.config['APP_CONFIG']
    task_broker = await TaskQueueBroker.get_instance()
    await task_broker.add_task({
        'name':     f'Update playlist - ID: {playlist_id}',
        'function': import_playlist_data,
        'args':     [config, playlist_id],
    }, priority=20)
    return jsonify(
        {
            "success": True,
        }
    )


@blueprint.route('/tic-api/playlists/streams', methods=['POST'])
async def api_get_filtered_playlist_streams():
    json_data = await request.get_json()
    results = read_filtered_stream_details_from_all_playlists(json_data)
    return jsonify(
        {
            "success": True,
            "data":    results
        }
    )


@blueprint.route('/tic-api/playlists/streams/all', methods=['GET'])
def api_get_all_playlist_streams():
    playlist_streams = read_stream_details_from_all_playlists()
    return jsonify(
        {
            "success": True,
            "data":    playlist_streams
        }
    )


@blueprint.route('/tic-api/playlists/stream/probe/<playlist_stream_id>', methods=['GET'])
def api_probe_playlist_stream(playlist_stream_id):
    probe = probe_playlist_stream(playlist_stream_id)
    return jsonify(
        {
            "success": True,
            "data":    probe
        }
    )
