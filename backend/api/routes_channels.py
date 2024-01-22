#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import io

from backend.api import blueprint
from flask import request, jsonify, current_app, send_file

from backend.channels import read_config_all_channels, add_new_channel, read_config_one_channel, update_channel, \
    delete_channel, add_bulk_channels, queue_background_channel_update_tasks, read_channel_logo


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
    queue_background_channel_update_tasks(config)
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
    queue_background_channel_update_tasks(config)
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
    queue_background_channel_update_tasks(config)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/settings/multiple/add', methods=['POST'])
def api_add_multiple_channels():
    config = current_app.config['APP_CONFIG']
    add_bulk_channels(config, request.json.get('channels', []))
    queue_background_channel_update_tasks(config)
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


@blueprint.route('/tic-api/channels/<channel_id>/logo/<file_placeholder>', methods=['GET'])
def api_get_channel_logo(channel_id, file_placeholder):
    image_base64_string, mime_type = read_channel_logo(channel_id)
    # Convert to a BytesIO object for sending file
    image_io = io.BytesIO(image_base64_string)
    image_io.seek(0)
    # Return file blob
    return send_file(image_io, mimetype=mime_type, download_name='image')
