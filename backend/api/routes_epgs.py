#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from lib.epg import read_epgs_config, read_channels_from_all_epgs, read_channels_from_epg_cache, import_epg_data
from backend.api import blueprint
from flask import request, jsonify, current_app


@blueprint.route('/tic-api/epgs/get', methods=['GET'])
def api_get_epgs():
    config = current_app.config['APP_CONFIG']
    epgs_config = read_epgs_config(config)
    return jsonify(
        {
            "success": True,
            "data":    epgs_config
        }
    )


@blueprint.route('/tic-api/epgs/channels', methods=['GET'])
def api_get_all_epg_channels():
    config = current_app.config['APP_CONFIG']
    epgs_channels = read_channels_from_all_epgs(config)
    return jsonify(
        {
            "success": True,
            "data":    epgs_channels
        }
    )


@blueprint.route('/tic-api/epgs/channels/<epg_id>', methods=['GET'])
def api_get_channels_from_epg(epg_id):
    config = current_app.config['APP_CONFIG']
    epgs_channels = read_channels_from_epg_cache(config, epg_id)
    return jsonify(
        {
            "success": True,
            "data":    epgs_channels
        }
    )


@blueprint.route('/tic-api/epgs/settings/<epg_id>', methods=['GET'])
def api_get_config_epgs(epg_id):
    config = current_app.config['APP_CONFIG']
    epgs_config = read_epgs_config(config, epg_id=epg_id)
    return jsonify(
        {
            "success": True,
            "data":    epgs_config
        }
    )


@blueprint.route('/tic-api/epgs/settings/<epg_id>/save', methods=['POST'])
def api_set_config_epgs(epg_id):
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


@blueprint.route('/tic-api/epgs/update/<epg_id>', methods=['POST'])
def api_update_epg(epg_id):
    config = current_app.config['APP_CONFIG']
    import_epg_data(config, epg_id)
    return jsonify(
        {
            "success": True,
        }
    )
