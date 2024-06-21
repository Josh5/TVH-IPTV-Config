#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import asyncio
import os

from quart import request, jsonify, redirect, send_from_directory, current_app

from backend.api import blueprint

from backend.api.tasks import TaskQueueBroker
from backend.auth import digest_auth_required, check_auth
from backend.config import is_tvh_process_running_locally, get_local_tvh_proc_admin_password
from backend.tvheadend.tvh_requests import configure_tvh


@blueprint.route('/')
def index():
    return redirect('/tic-web/')


@blueprint.route('/tic-web/')
@digest_auth_required
async def serve_index():
    response = await send_from_directory(current_app.config['ASSETS_ROOT'], 'index.html')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@blueprint.route('/tic-web/<path:path>')
@digest_auth_required
async def serve_static(path):
    response = await send_from_directory(current_app.config['ASSETS_ROOT'], path)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@blueprint.route('/tic-web/epg.xml')
def serve_epg_static():
    config = current_app.config['APP_CONFIG']
    return send_from_directory(os.path.join(config.config_path), 'epg.xml')


@blueprint.route('/tic-api/ping')
async def ping():
    return jsonify(
        {
            "success": True,
            "data":    "pong"
        }
    ), 200


@blueprint.route('/tic-api/check-auth')
async def api_check_auth():
    if await check_auth():
        return jsonify(
            {
                "success": True,
            }
        ), 200
    return jsonify(
        {
            "success": False,
        }
    ), 401


@blueprint.route('/tic-api/require-auth')
@digest_auth_required
async def api_require_auth():
    return jsonify(
        {
            "success": True,
        }
    ), 200


@blueprint.route('/tic-api/get-background-tasks', methods=['GET'])
@digest_auth_required
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
@digest_auth_required
async def api_toggle_background_tasks_status():
    task_broker = await TaskQueueBroker.get_instance()
    await task_broker.toggle_status()
    return jsonify(
        {
            "success": True
        }
    ), 200


@blueprint.route('/tic-api/tvh-running', methods=['GET'])
@digest_auth_required
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
@digest_auth_required
async def api_save_config():
    json_data = await request.get_json()
    config = current_app.config['APP_CONFIG']

    # Update auth for AIO container
    if await is_tvh_process_running_locally():
        admin_username = 'admin'
        if json_data.get('settings', {}).get('first_run'):
            json_data['settings']['admin_password'] = admin_username
        # Force admin login
        json_data['settings']['enable_admin_user'] = True
        # Update TVH password also
        if json_data.get('settings', {}).get('admin_password'):
            if not json_data.get('settings', {}).get('tvheadend'):
                json_data['settings']['tvheadend'] = {}
            json_data['settings']['tvheadend']['username'] = admin_username
            json_data['settings']['tvheadend']['password'] = json_data['settings']['admin_password']
        # Force the creation of a client user
        json_data['settings']['create_client_user'] = True
        client_username = json_data.get('settings', {}).get('client_username')
        if not client_username or client_username == '':
            json_data['settings']['client_username'] = 'client'
        client_password = json_data.get('settings', {}).get('client_password')
        if not client_password or client_password == '':
            json_data['settings']['client_password'] = 'client'

    # Mark first run as complete
    json_data['settings']['first_run'] = False

    # Save the config
    config.update_settings(json_data)
    config.save_settings()

    # Store settings for TVH service
    if json_data.get('settings', {}).get('tvheadend'):
        try:
            await configure_tvh(config)
            pass
        except Exception as e:
            current_app.logger.exception(f"Error while configuring TVH: %s", e)
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
@digest_auth_required
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
@digest_auth_required
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
