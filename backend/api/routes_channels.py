#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import io

from backend.api import blueprint
from quart import request, jsonify, current_app, send_file

from backend.auth import digest_auth_required
from backend.channels import read_config_all_channels, add_new_channel, read_config_one_channel, update_channel, \
    delete_channel, add_bulk_channels, queue_background_channel_update_tasks, read_channel_logo


@blueprint.route('/tic-api/channels/get', methods=['GET'])
@digest_auth_required
async def api_get_channels():
    channels_config = await read_config_all_channels()
    return jsonify(
        {
            "success": True,
            "data":    channels_config
        }
    )


@blueprint.route('/tic-api/channels/new', methods=['POST'])
@digest_auth_required
async def api_add_new_channel():
    json_data = await request.get_json()
    config = current_app.config['APP_CONFIG']
    await add_new_channel(config, json_data)
    await queue_background_channel_update_tasks(config)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/settings/<channel_id>', methods=['GET'])
@digest_auth_required
async def api_get_channel_config(channel_id):
    channel_config = read_config_one_channel(channel_id)
    return jsonify(
        {
            "success": True,
            "data":    channel_config
        }
    )


@blueprint.route('/tic-api/channels/settings/<channel_id>/save', methods=['POST'])
@digest_auth_required
async def api_set_config_channels(channel_id):
    json_data = await request.get_json()
    config = current_app.config['APP_CONFIG']
    update_channel(config, channel_id, json_data)
    await queue_background_channel_update_tasks(config)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/settings/multiple/save', methods=['POST'])
@digest_auth_required
async def api_set_config_multiple_channels():
    json_data = await request.get_json()
    config = current_app.config['APP_CONFIG']
    for channel_id in json_data.get('channels', {}):
        channel = json_data['channels'][channel_id]
        update_channel(config, channel_id, channel)
    await queue_background_channel_update_tasks(config)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/settings/multiple/add', methods=['POST'])
@digest_auth_required
async def api_add_multiple_channels():
    json_data = await request.get_json()
    config = current_app.config['APP_CONFIG']
    await add_bulk_channels(config, json_data.get('channels', []))
    await queue_background_channel_update_tasks(config)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/settings/<channel_id>/delete', methods=['DELETE'])
@digest_auth_required
async def api_delete_config_channels(channel_id):
    config = current_app.config['APP_CONFIG']
    delete_channel(config, channel_id)
    return jsonify(
        {
            "success": True
        }
    )


@blueprint.route('/tic-api/channels/<channel_id>/logo/<file_placeholder>', methods=['GET'])
async def api_get_channel_logo(channel_id, file_placeholder):
    image_base64_string, mime_type = read_channel_logo(channel_id)
    # Convert to a BytesIO object for sending file
    image_io = io.BytesIO(image_base64_string)
    image_io.seek(0)
    # Return file blob
    return await send_file(image_io, mimetype=mime_type)
