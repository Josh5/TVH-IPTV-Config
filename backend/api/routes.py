#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import asyncio
import os

from quart import request, jsonify, redirect, send_from_directory, current_app

from backend.api import blueprint

from backend.api.tasks import TaskQueueBroker
from backend.config import is_tvh_process_running_locally, get_local_tvh_proc_admin_password
from backend.tvheadend.tvh_requests import configure_tvh


@blueprint.route('/')
def index():
    return redirect('/tic-web/')


@blueprint.route('/tic-web/')
def serve_index():
    return send_from_directory(current_app.config['ASSETS_ROOT'], 'index.html')


@blueprint.route('/tic-web/<path:path>')
def serve_static(path):
    return send_from_directory(current_app.config['ASSETS_ROOT'], path)


@blueprint.route('/tic-web/epg.xml')
def serve_epg_static():
    config = current_app.config['APP_CONFIG']
    return send_from_directory(os.path.join(config.config_path), 'epg.xml')


@blueprint.route('/tic-api/ping')
def ping():
    config = current_app.config['APP_CONFIG']
    return jsonify(
        {
            "success": True,
            "data":    "pong"
        }
    ), 200


@blueprint.route('/tic-api/get-background-tasks', methods=['GET'])
async def api_get_background_tasks():
    task_broker = await TaskQueueBroker.get_instance()
    await task_broker.get_pending_tasks()
    return jsonify(
        {
            "success": True,
            "data":    {
                "task_queue_status": await task_broker.get_status(),
                "current_task":      await task_broker.get_currently_running_task(),
                "pending_tasks":     await task_broker.get_pending_tasks(),
            },
        }
    ), 200


@blueprint.route('/tic-api/toggle-pause-background-tasks', methods=['GET'])
async def api_toggle_background_tasks_status():
    task_broker = await TaskQueueBroker.get_instance()
    await task_broker.toggle_status()
    return jsonify(
        {
            "success": True
        }
    ), 200


@blueprint.route('/tic-api/tvh-running', methods=['GET'])
async def api_check_if_tvh_running_status():
    running = await is_tvh_process_running_locally()
    return jsonify(
        {
            "success": True,
            "data":    {
                "running": running
            }
        }
    ), 200


@blueprint.route('/tic-api/save-settings', methods=['POST'])
async def api_save_config():
    json_data = await request.get_json()
    config = current_app.config['APP_CONFIG']
    config.update_settings(json_data)
    config.save_settings()
    if json_data.get('settings', {}).get('tvheadend'):
        try:
            await configure_tvh(config)
        except Exception as e:
            current_app.logger.warning(f"Error while configuring TVH: %s", e)
            return jsonify(
                {
                    "success": False
                }
            ), 400
    return jsonify(
        {
            "success": True
        }
    ), 200


@blueprint.route('/tic-api/get-settings')
async def api_get_config_tvheadend():
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    return_data = settings.get('settings', {})
    if await is_tvh_process_running_locally():
        tvh_password = await get_local_tvh_proc_admin_password()
        return_data['tvheadend']['username'] = 'admin'
        return_data['tvheadend']['password'] = tvh_password
    return jsonify(
        {
            "success": True,
            "data":    return_data
        }
    ), 200


@blueprint.route('/tic-api/export-config')
async def api_export_config():
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    # Fetch all playlists
    from backend.playlists import read_config_all_playlists
    all_playlist_configs = await read_config_all_playlists(output_for_export=True)
    # Fetch all epgs
    from backend.epgs import read_config_all_epgs
    all_epg_configs = await read_config_all_epgs(output_for_export=True)
    # Fetch all channels
    from backend.channels import read_config_all_channels
    channels_config = await read_config_all_channels(output_for_export=True)
    return_data = {
        'settings':  settings.get('settings', {}),
        'playlists': all_playlist_configs,
        'epgs':      all_epg_configs,
        'channels':  channels_config,
    }
    return jsonify(
        {
            "success": True,
            "data":    return_data
        }
    ), 200
