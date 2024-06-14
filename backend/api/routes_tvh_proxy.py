#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from backend.api import blueprint
from quart import jsonify, current_app, render_template_string, Response

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


async def _get_tvh_settings():
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    tvh_host = settings['settings']['tvheadend']['host']
    tvh_port = settings['settings']['tvheadend']['port']
    tvh_username = settings['settings']['tvheadend']['username']
    tvh_password = settings['settings']['tvheadend']['password']
    # Configure TVH-IPTV-Config base URL (proto/host/port)
    tic_base_url = settings['settings']['app_url']
    # Configure some connection URLs
    tvh_api_url = f"http://{tvh_host}:{tvh_port}/api"
    tvh_http_url = f"http://{tvh_host}:{tvh_port}"
    if tvh_username:
        tvh_http_url = f"http://{tvh_username}:{tvh_password}@{tvh_host}:{tvh_port}"
    stream_profile = 'pass'
    stream_priority = 300
    return {
        "tic_base_url":    tic_base_url,
        "tvh_host":        tvh_host,
        "tvh_port":        tvh_port,
        "tvh_username":    tvh_username,
        "tvh_password":    tvh_password,
        "tvh_api_url":     tvh_api_url,
        "tvh_http_url":    tvh_http_url,
        "stream_profile":  stream_profile,
        "stream_priority": stream_priority,
    }


async def _get_channels(playlist_id):
    return_channels = []
    from backend.channels import read_config_all_channels
    channels_config = read_config_all_channels(filter_playlist_ids=[int(playlist_id)])
    for channel in channels_config:
        if channel['enabled']:
            return_channels.append(channel)
    return return_channels


async def _get_playlist_connection_count(playlist_id):
    from backend.playlists import read_config_one_playlist
    playlist_config = read_config_one_playlist(playlist_id)
    return playlist_config.get('connections', 1)


async def _get_discover_data(playlist_id=0):
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    tvh_settings = await _get_tvh_settings()
    device_name = f'TVH-IPTV-Config-{playlist_id}'
    tuner_count = await _get_playlist_connection_count(playlist_id)
    device_id = f'tic-12345678-{playlist_id}'
    device_auth = f'tic-{playlist_id}'
    base_url = f'{tvh_settings["tic_base_url"]}/tic-api/hdhr_device/{playlist_id}'
    return {
        'FriendlyName':    device_name,
        'Manufacturer':    'Tvheadend',
        'ModelNumber':     'HDTC-2US',
        'FirmwareName':    'bin_2.2.0',
        'TunerCount':      tuner_count,
        'FirmwareVersion': '2.2.0',
        'DeviceID':        device_id,
        'DeviceAuth':      device_auth,
        'BaseURL':         base_url,
        'LineupURL':       f'{base_url}/lineup.json',
    }


async def _get_lineup_list(playlist_id):
    use_tvh_source = True
    tvh_settings = await _get_tvh_settings()
    lineup_list = []
    from backend.epgs import generate_epg_channel_id
    for channel_details in await _get_channels(playlist_id):
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


@blueprint.route('/tic-api/hdhr_device/<playlist_id>/discover.json', methods=['GET'])
async def discover_json(playlist_id):
    discover_data = await _get_discover_data(playlist_id=playlist_id)
    return jsonify(discover_data)


@blueprint.route('/tic-api/hdhr_device/<playlist_id>/lineup.json', methods=['GET'])
async def lineup_json(playlist_id):
    lineup_list = await _get_lineup_list(playlist_id)
    return jsonify(lineup_list)


@blueprint.route('/tic-api/hdhr_device/<playlist_id>/lineup_status.json', methods=['GET'])
async def lineup_status_json(playlist_id=None):
    return jsonify(
        {
            'ScanInProgress': 0,
            'ScanPossible':   0,
            'Source':         "Cable",
            'SourceList':     ['Cable']
        }
    )


@blueprint.route('/tic-api/hdhr_device/<playlist_id>/lineup.post', methods=['GET', 'POST'])
async def lineup_post(playlist_id=None):
    return ''


@blueprint.route('/tic-api/hdhr_device/<playlist_id>/device.xml', methods=['GET'])
async def device_xml(playlist_id):
    discover_data = await _get_discover_data(playlist_id)
    xml_content = await render_template_string(device_xml_template, data=discover_data)
    return Response(xml_content, mimetype='application/xml')
