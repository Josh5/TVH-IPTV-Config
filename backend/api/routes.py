#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from backend.api import blueprint
from flask import request, jsonify, redirect, send_from_directory, current_app


@blueprint.route('/')
def index():
    return redirect('/tic-web/')


@blueprint.route('/tic-web/')
def serve_index():
    return send_from_directory(current_app.config['ASSETS_ROOT'], 'index.html')


@blueprint.route('/tic-web/<path:path>')
def serve_static(path):
    return send_from_directory(current_app.config['ASSETS_ROOT'], path)


@blueprint.route('/tvh-admin/')
def serve_tvh_admin():
    return send_from_directory(current_app.config['TVH_ADMIN_ROOT'], 'index.html')


@blueprint.route('/tvh-admin/<path:path>')
def serve_tvh_admin_static(path):
    return send_from_directory(current_app.config['TVH_ADMIN_ROOT'], path)


@blueprint.route('/status.xml', defaults={'path': ''}, methods=['GET'])
@blueprint.route('/api/', defaults={'path': ''}, methods=['GET'])
@blueprint.route('/api/<path:path>', methods=['GET'])
def proxy_get(path):
    tvh_url = "http://localhost:9981"
    from backend.tvheadend.tvh_requests import get_tvh
    tvh = get_tvh(current_app.config['APP_CONFIG'])
    return tvh.proxy_get(f'{tvh_url}/api/{path}')


@blueprint.route('/tic-web/epg.xml')
def serve_epg_static():
    config = current_app.config['APP_CONFIG']
    print(os.path.join(config.config_path))
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


@blueprint.route('/tic-api/save-settings', methods=['POST'])
def api_save_config():
    config = current_app.config['APP_CONFIG']
    config.update_settings(request.json)
    config.save_settings()
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
            "data":    settings.get('settings', {}).get('tvheadend', {})
        }
    )
