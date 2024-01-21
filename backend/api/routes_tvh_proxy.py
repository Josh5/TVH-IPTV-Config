#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

import requests

from backend.api import blueprint
from flask import jsonify, current_app, render_template_string, Response

from backend.channels import read_config_all_channels
from backend.epgs import generate_epg_channel_id

device_xml_template = """<?xml version="1.0" encoding="UTF-8"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
    <specVersion>
        <major>1</major>
        <minor>0</minor>
    </specVersion>
    <URLBase>{{ data.BaseURL }}</URLBase>
    <device>
        <deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>
        <friendlyName>{{ data.FriendlyName }}</friendlyName>
        <manufacturer>{{ data.Manufacturer }}</manufacturer>
        <modelName>{{ data.ModelNumber }}</modelName>
        <modelNumber>{{ data.ModelNumber }}</modelNumber>
        <serialNumber></serialNumber>
        <UDN>uuid:{{ data.DeviceID }}</UDN>
    </device>
</root>"""


def _get_tvh_settings():
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    tvh_host = settings['settings']['tvheadend']['host']
    tvh_port = settings['settings']['tvheadend']['port']
    tvh_username = settings['settings']['tvheadend']['username']
    tvh_password = settings['settings']['tvheadend']['password']
    # Configure some connection URLs
    tvh_api_url = f"http://{tvh_host}:{tvh_port}/api"
    tvh_http_url = f"http://{tvh_host}:{tvh_port}"
    if tvh_username:
        tvh_http_url = f"http://{tvh_username}:{tvh_password}@{tvh_host}:{tvh_port}"
    stream_profile = 'pass'
    stream_priority = 300
    return {
        "tvh_host":        tvh_host,
        "tvh_port":        tvh_port,
        "tvh_username":    tvh_username,
        "tvh_password":    tvh_password,
        "tvh_api_url":     tvh_api_url,
        "tvh_http_url":    tvh_http_url,
        "stream_profile":  stream_profile,
        "stream_priority": stream_priority,
    }


def _get_channels():
    tvh_settings = _get_tvh_settings()
    return_channels = []
    channels_config = read_config_all_channels()
    for channel in channels_config:
        if channel['enabled']:
            return_channels.append(channel)
    return return_channels


def _get_discover_data():
    tvh_settings = _get_tvh_settings()
    tic_web_host = os.environ.get("APP_HOST_IP", "127.0.0.1")
    tic_web_port = os.environ.get("APP_PORT", "9985")
    tuner_count = 2
    device_id = '12345678'

    return {
        'FriendlyName':    'TVH-IPTV-Config',
        'Manufacturer':    'Tvheadend',
        'ModelNumber':     'HDTC-2US',
        'FirmwareName':    'bin_2.2.0',
        'TunerCount':      tuner_count,
        'FirmwareVersion': '2.2.0',
        'DeviceID':        device_id,
        'DeviceAuth':      'tic',
        'BaseURL':         f'http://{tic_web_host}:{tic_web_port}',
        'LineupURL':       f'http://{tic_web_host}:{tic_web_port}/lineup.json',
    }


def _get_lineup_list():
    use_tvh_source = True
    tvh_settings = _get_tvh_settings()
    lineup_list = []
    for channel_details in _get_channels():
        # current_app.logger.info(channel_details)
        channel_id = generate_epg_channel_id(channel_details["number"], channel_details["name"])
        # TODO: Add support for fetching a stream from this application without using TVH as a proxy
        if use_tvh_source and channel_details.get('tvh_uuid'):
            channel_url = f'{tvh_settings["tvh_http_url"]}/stream/channel/{channel_details["tvh_uuid"]}'
            path_args = f'?profile={tvh_settings["stream_profile"]}&weight={tvh_settings["stream_priority"]}'
            url = f'{channel_url}{path_args}'
            lineup_list.append(
                {
                    'GuideNumber': channel_id,
                    'GuideName':   channel_details['name'],
                    'URL':         url
                }
            )
    return lineup_list


@blueprint.route('/discover.json', methods=['GET'])
def discover():
    discover_data = _get_discover_data()
    return jsonify(discover_data)


@blueprint.route('/lineup.json', methods=['GET'])
def lineup():
    lineup_list = _get_lineup_list()
    return jsonify(lineup_list)


@blueprint.route('/lineup_status.json', methods=['GET'])
def status():
    return jsonify(
        {
            'ScanInProgress': 0,
            'ScanPossible':   0,
            'Source':         "Cable",
            'SourceList':     ['Cable']
        }
    )


@blueprint.route('/lineup.post', methods=['GET', 'POST'])
def lineup_post():
    return ''


@blueprint.route('/device.xml', methods=['GET'])
def device():
    discover_data = _get_discover_data()
    xml_content = render_template_string(device_xml_template, data=discover_data)
    return Response(xml_content, mimetype='application/xml')
