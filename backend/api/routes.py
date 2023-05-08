#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from backend.api import blueprint
from flask import request, jsonify, redirect, send_from_directory, current_app

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
def api_get_background_tasks():
    task_broker = TaskQueueBroker.get_instance()
    task_broker.get_pending_tasks()
    return jsonify(
        {
            "success": True,
            "data":    {
                "current_task":  task_broker.get_currently_running_task(),
                "pending_tasks": task_broker.get_pending_tasks(),
            },
        }
    )


@blueprint.route('/tic-api/save-settings', methods=['POST'])
def api_save_config():
    config = current_app.config['APP_CONFIG']
    config.update_settings(request.json)
    config.save_settings()
    configure_tvh(config)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/tvheadend/get-settings')
def api_get_config_tvheadend():
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    return jsonify(
        {
            "success": True,
            "data":    {
                "tvheadend":                settings.get('settings', {}).get('tvheadend', {}),
                "enable_stream_buffer":     settings.get('settings', {}).get('enable_stream_buffer', True),
                "default_ffmpeg_pipe_args": settings.get('settings', {}).get('default_ffmpeg_pipe_args', '[URL]'),

            }
        }
    )
