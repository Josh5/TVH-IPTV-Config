#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import re
import sqlalchemy.exc

from flask import request

from backend.api import blueprint
from quart import jsonify, current_app, render_template_string, Response

from backend.config import is_tvh_process_running_locally

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


async def _get_tvh_settings(include_auth=True, stream_profile='pass'):
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    # Configure TVH-IPTV-Config base URL (proto/host/port)
    tic_base_url = settings['settings']['app_url']
    protocol_match = re.match(r'^(https?)://', settings['settings']['app_url'])
    tic_base_url_protocol = protocol_match.group(1) if protocol_match else 'http'
    # Create URLs for TVH
    # Note: This host needs to be the externally accessible host that third-party apps can then access TVH with
    tvh_host = settings['settings']['tvheadend']['host']
    tvh_port = settings['settings']['tvheadend']['port']
    tvh_path = settings['settings']['tvheadend']['path']
    tvh_base_url = f"{tvh_host}:{tvh_port}{tvh_path}"
    if await is_tvh_process_running_locally():
        tvh_path = '/tic-tvh'
        app_url = re.sub(r'^https?://', '', settings['settings']['app_url'])
        tvh_base_url = f"{app_url}{tvh_path}"
    # Configure some connection URLs
    tvh_api_url = f"{tic_base_url_protocol}://{tvh_base_url}/api"
    tvh_http_url = f"{tic_base_url_protocol}://{tvh_base_url}"
    if include_auth:
        client_username = settings['settings']['client_username']
        client_password = settings['settings']['client_password']
        if settings['settings']['create_client_user'] and client_username:
            tvh_http_url = f"{tic_base_url_protocol}://{client_username}:{client_password}@{tvh_base_url}"
    # Set stream configuration
    stream_priority = 300
    return {
        "tic_base_url":    tic_base_url,
        "tvh_base_url":    tvh_base_url,
        "tvh_path":        tvh_path,
        "tvh_api_url":     tvh_api_url,
        "tvh_http_url":    tvh_http_url,
        "stream_profile":  stream_profile,
        "stream_priority": stream_priority,
    }


async def _get_channels(playlist_id):
    return_channels = []
    from backend.channels import read_config_all_channels
    channels_config = await read_config_all_channels(filter_playlist_ids=[int(playlist_id)])
    for channel in channels_config:
        if channel['enabled']:
            return_channels.append(channel)
    return return_channels


async def _get_playlist_connection_count(config, playlist_id):
    from backend.playlists import read_config_one_playlist
    try:
        playlist_config = await read_config_one_playlist(config, playlist_id)
        return playlist_config.get('connections', 1)
    except sqlalchemy.exc.NoResultFound:
        # Playlist not found, return default value
        return 1


async def _get_discover_data(playlist_id=0):
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    tvh_settings = await _get_tvh_settings(include_auth=True)
    device_name = f'TVH-IPTV-Config-{playlist_id}'
    tuner_count = await _get_playlist_connection_count(config, playlist_id)
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
    tvh_settings = await _get_tvh_settings(include_auth=True)
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


async def _get_playlist_channels(playlist_id, include_auth=False, stream_profile='pass'):
    use_tvh_source = True
    tvh_settings = await _get_tvh_settings(include_auth=include_auth, stream_profile=stream_profile)
    playlist = [f'#EXTM3U url-tvg="{tvh_settings["tic_base_url"]}/tic-web/epg.xml"']
    from backend.epgs import generate_epg_channel_id
    for channel_details in await _get_channels(playlist_id):
        current_app.logger.warning(channel_details)
        channel_id = generate_epg_channel_id(channel_details["number"], channel_details["name"])
        channel_name = channel_details['name']
        channel_logo_url = channel_details['logo_url']
        channel_uuid = channel_details['tvh_uuid']
        line = f'#EXTINF:-1 tvg-name="{channel_name}" tvg-logo="{channel_logo_url}" tvg-id="{channel_uuid}" tvg-chno="{channel_id}"'
        if channel_details['tags']:
            group_title = channel_details['tags'][0]
            line += f' group-title="{group_title}"'
        playlist.append(line)
        # TODO: Add support for fetching a stream from this application without using TVH as a proxy
        if use_tvh_source and channel_details.get('tvh_uuid'):
            channel_url = f'{tvh_settings["tvh_http_url"]}/stream/channel/{channel_details["tvh_uuid"]}'
            path_args = f'?profile={tvh_settings["stream_profile"]}&weight={tvh_settings["stream_priority"]}'
            url = f'{channel_url}{path_args}'
            playlist.append(url)
    return playlist


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


@blueprint.route('/tic-api/tvh_playlist/<playlist_id>/channels.m3u', methods=['GET'])
async def tvh_playlist_m3u(playlist_id):
    # Check for 'include_auth' GET argument
    include_auth = request.args.get('include_auth') != 'false'
    stream_profile = request.args.get('profile', 'pass')

    # Get the playlist channels
    file_lines = await _get_playlist_channels(playlist_id, include_auth=include_auth, stream_profile=stream_profile)
    # Join the lines to form the m3u content
    m3u_content = "\n".join(file_lines)
    # Create a response object with appropriate headers
    response = Response(m3u_content, mimetype='application/vnd.apple.mpegurl')
    response.headers['Content-Disposition'] = f'attachment; filename="{playlist_id}_channels.m3u"'
    return response
