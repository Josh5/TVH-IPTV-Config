#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from backend.api import blueprint
from flask import request, jsonify, current_app

from backend.channels import read_config_all_channels, add_new_channel, read_config_one_channel, update_channel, \
    publish_channel_muxes, map_all_services, delete_channel, cleanup_old_channels
from backend.epgs import build_custom_epg, run_tvh_epg_grabbers


@blueprint.route('/tic-api/channels/get', methods=['GET'])
def api_get_channels():
    channels_config = read_config_all_channels()
    return jsonify(
        {
            "success": True,
            "data":    channels_config
        }
    )


@blueprint.route('/tic-api/channels/new', methods=['POST'])
def api_add_new_channel():
    config = current_app.config['APP_CONFIG']
    add_new_channel(config, request.json)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/settings/<channel_id>', methods=['GET'])
def api_get_channel_config(channel_id):
    channel_config = read_config_one_channel(channel_id)
    return jsonify(
        {
            "success": True,
            "data":    channel_config
        }
    )


@blueprint.route('/tic-api/channels/settings/<channel_id>/save', methods=['POST'])
def api_set_config_channels(channel_id):
    config = current_app.config['APP_CONFIG']
    update_channel(config, channel_id, request.json)
    # # Update custom epg
    # update_custom_epg(config)
    # TODO: Trigger an update of the EPG config in TVheadend
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/settings/multiple/save', methods=['POST'])
def api_set_config_multiple_channels():
    config = current_app.config['APP_CONFIG']
    for channel_id in request.json.get('channels', {}):
        channel = request.json['channels'][channel_id]
        update_channel(config, channel_id, channel)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/settings/<channel_id>/delete', methods=['DELETE'])
def api_delete_config_channels(channel_id):
    config = current_app.config['APP_CONFIG']
    delete_channel(config, channel_id)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/publish', methods=['POST'])
def api_publish_channels():
    config = current_app.config['APP_CONFIG']
    # Generate 'epg.xml' file in .tvh_iptv_config directory
    build_custom_epg(config)
    # Trigger an update in TVH to fetch the latest EPG
    run_tvh_epg_grabbers(config)
    # Configure TVH with muxes
    publish_channel_muxes(config)
    # Map all services
    # TODO: Create a thread that watches for new services every 60 seconds and maps them automatically
    map_all_services(config)
    # Clear out old channels
    cleanup_old_channels(config)
    return jsonify(
        {
            "success": True,
        }
    )
