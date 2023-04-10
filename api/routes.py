#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from lib.epg import read_channels_config, update_custom_epg, remove_channel_from_channels_config
from lib.tvheadend import read_tvh_config, configure_channel_muxes, map_all_services
from tvh_iptv_config.api import blueprint
from flask import request, jsonify, redirect, send_from_directory, current_app

frontend_dir = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), 'frontend')
static_assets = os.path.join(frontend_dir, 'dist', 'spa')


@blueprint.route('/')
def index():
    return redirect('/tvh-ui/tvheadend')


@blueprint.route('/tic-web')
def serve_index():
    return send_from_directory(static_assets, 'index.html')


@blueprint.route('/tic-web/<path:path>')
def serve_static(path):
    return send_from_directory(static_assets, path)


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
    tvh_config = read_tvh_config(config)
    return jsonify(
        {
            "success": True,
            "data":    tvh_config
        }
    )


@blueprint.route('/tic-api/channels/get', methods=['GET'])
def api_get_channels():
    config = current_app.config['APP_CONFIG']
    channels_config = read_channels_config(config)
    return jsonify(
        {
            "success": True,
            "data":    channels_config
        }
    )


@blueprint.route('/tic-api/channels/publish', methods=['POST'])
def api_publish_channels():
    config = current_app.config['APP_CONFIG']
    # Configure TVH with muxes
    configure_channel_muxes(config)
    # Map all services
    # TODO: Create a thread that watches for new services every 60 seconds and maps them automatically
    map_all_services(config)
    return jsonify(
        {
            "success": True,
        }
    )


@blueprint.route('/tic-api/channels/settings/<channel_number>', methods=['GET'])
def api_get_config_channels(channel_number):
    config = current_app.config['APP_CONFIG']
    channel_config = read_channels_config(config, channel_number=channel_number)
    return jsonify(
        {
            "success": True,
            "data":    channel_config
        }
    )


@blueprint.route('/tic-api/channels/settings/<channel_number>/save', methods=['POST'])
def api_set_config_channels(channel_number):
    config = current_app.config['APP_CONFIG']
    # Save settings
    config.update_settings(request.json)
    config.save_settings()
    # # Update custom epg
    # update_custom_epg(config)
    # TODO: Trigger an update of the EPG config in TVheadend
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/settings/<channel_number>/delete', methods=['DELETE'])
def api_delete_config_channels(channel_number):
    config = current_app.config['APP_CONFIG']
    # Remove channel
    remove_channel_from_channels_config(config, channel_number)
    # Save settings
    config.save_settings()
    return jsonify(
        {
            "success": True
        }
    )
