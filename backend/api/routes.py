#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import asyncio
import os

from quart import request, jsonify, redirect, send_from_directory, current_app

from backend.api import blueprint

from backend.api.tasks import TaskQueueBroker
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
    )


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
    )


@blueprint.route('/tic-api/toggle-pause-background-tasks', methods=['GET'])
async def api_toggle_background_tasks_status():
    task_broker = await TaskQueueBroker.get_instance()
    await task_broker.toggle_status()
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/save-settings', methods=['POST'])
async def api_save_config():
    json_data = await request.get_json()
    config = current_app.config['APP_CONFIG']
    config.update_settings(json_data)
    config.save_settings()
    await configure_tvh(config)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/get-settings')
def api_get_config_tvheadend():
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    return jsonify(
        {
            "success": True,
            "data":    settings.get('settings', {})
        }
    )
