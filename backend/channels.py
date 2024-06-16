#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import base64
import logging
import os
import re
from mimetypes import guess_type

import requests
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, func, select

from backend.ffmpeg import generate_iptv_url
from backend.models import db, Session, Channel, ChannelTag, Epg, ChannelSource, Playlist, EpgChannels, PlaylistStreams, \
    channels_tags_association_table
from backend.playlists import fetch_playlist_streams
from backend.tvheadend.tvh_requests import get_tvh

logger = logging.getLogger('werkzeug.channels')


async def read_config_all_channels(filter_playlist_ids=None, output_for_export=False):
    if filter_playlist_ids is None:
        filter_playlist_ids = []

    return_list = []

    async with Session() as session:
        async with session.begin():
            query = select(Channel).options(
                joinedload(Channel.tags),
                joinedload(Channel.sources).subqueryload(ChannelSource.playlist)
            ).order_by(Channel.id)

            result = await session.execute(query)
            channels = result.scalars().unique().all()

            for result in channels:
                tags = [tag.name for tag in result.tags]
                sources = []
                for source in result.sources:
                    # If filtering on playlist IDs, then only return sources from that playlist
                    if filter_playlist_ids and source.playlist_id not in filter_playlist_ids:
                        continue
                    if output_for_export:
                        sources.append({
                            'playlist_name': source.playlist.name,
                            'priority':      source.priority,
                            'stream_name':   source.playlist_stream_name,
                        })
                        continue
                    sources.append({
                        'playlist_id':   source.playlist_id,
                        'playlist_name': source.playlist.name,
                        'priority':      source.priority,
                        'stream_name':   source.playlist_stream_name,
                    })
                # Filter out this channel if we have provided a playlist ID filter list and no sources were found
                if filter_playlist_ids and not sources:
                    continue

                if output_for_export:
                    return_list.append({
                        'enabled':  result.enabled,
                        'name':     result.name,
                        'logo_url': result.logo_url,
                        'number':   result.number,
                        'tags':     tags,
                        'guide':    {
                            'epg_name':   result.guide_name,
                            'channel_id': result.guide_channel_id,
                        },
                        'sources':  sources,
                    })
                    continue
                return_list.append({
                    'id':       result.id,
                    'enabled':  result.enabled,
                    'tvh_uuid': result.tvh_uuid,
                    'name':     result.name,
                    'logo_url': result.logo_url,
                    'number':   result.number,
                    'tags':     tags,
                    'guide':    {
                        'epg_id':     result.guide_id,
                        'epg_name':   result.guide_name,
                        'channel_id': result.guide_channel_id,
                    },
                    'sources':  sources,
                })

    return return_list


def read_config_one_channel(channel_id):
    return_item = {}
    result = db.session.query(Channel) \
        .options(joinedload(Channel.tags), joinedload(Channel.sources).subqueryload(ChannelSource.playlist)) \
        .filter(Channel.id == channel_id) \
        .order_by(Channel.id) \
        .one()
    if result:
        tags = []
        for tag in result.tags:
            tags.append(tag.name)
        sources = []
        for source in result.sources:
            sources.append({
                'playlist_id':   source.playlist_id,
                'playlist_name': source.playlist.name,
                'priority':      source.priority,
                'stream_name':   source.playlist_stream_name,
            })
        return_item = {
            'id':       result.id,
            'enabled':  result.enabled,
            'name':     result.name,
            'logo_url': result.logo_url,
            'number':   result.number,
            'tags':     tags,
            'guide':    {
                'epg_id':     result.guide_id,
                'epg_name':   result.guide_name,
                'channel_id': result.guide_channel_id,
            },
            'sources':  sources,
        }
    return return_item


def get_channel_image_path(config, channel_id):
    return os.path.join(config.config_path, 'cache', 'logos', f"channel_logo_{channel_id}")


def download_image_to_base64(image_source):
    # Image source is a URL
    mime_type = guess_type(image_source)[0]
    response = requests.get(image_source)
    response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
    image_base64_string = base64.b64encode(response.content).decode()
    return image_base64_string, mime_type


def parse_image_as_base64(image_source):
    placeholder_base64 = 'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAACiUlEQVR4nO2cy46sMAxEzdX8/y/3XUSKUM+I7sLlF6qzYgE4HJwQEsLxer1MfMe/6gJMQrIAJAtAsgAkC0CyACQLQLIAJAtAsgAkC0CyACQLQLIAJAtAsgAkC0CyACQL4Md5/HEclFH84ziud+gwV+C61H2F905yFvTxDNDOQXjz4p6vddTt0M7Db0OoRN/7cmZi6Nm+iphWblbrlnnm90CsMBe+EmpNTsVk3pM/faXd9oRYzH7WLui2lmlqFeBjF8QD/2LKn/Fxd4jfgy/vPcblV+zrTmiluCDIF1/WqgW/269kInyRZZ3bi+f5Ysr63bI+zFf4EE25LyI0WRcP7FpfxOTiyPrYtXmGr7yR0gfUx9Rh5em+CLKg14sqX5SaWDBhMTe/vLLuvbWW+PInV9lU2MT8qpw3HOereJJ1li+XLMowW6YvZ7PVYvp+Sn61kGVDfHWRZRN8NZJl7X31kmW9fbWTZY19dZRlXX01lWUtffWVZf18tZZlzXy5ZEV/iLGjrA1/LOf7WffMWjTJrxmyrIevMbKsgS+vrJxm6xxubdwI6h9QmpRZi8L8IshKTi675YsyTjkvsxYl+TVVllX44sjKr4k77tq4js76JJeWWW19ET9eHlwNN2n1kbxooPBzyLXxVgDuN/HkzGrli756IGQxQvIqlLfQe5tehpA2q0N+RRDVwBf62nRfNHCmxFfo+o7YrkOyr+j1HRktceFKVvKq7AcsM70+M9FX6jO+avU9K25Nhyj/vw4UX2W9R0v/Y4jfV6WsMzn/ovH+D6aJrDQ8z5knDNFAPH9GugmSBSBZAJIFIFkAkgUgWQCSBSBZAJIFIFkAkgUgWQCSBSBZAJIFIFkA/wGlHK2X7Li2TQAAAABJRU5ErkJggg=='
    try:
        if image_source.startswith('data:image/'):
            mime_type = image_source.split(';')[0].split(':')[1]
            image_base64_string = image_source.split('base64,')[1]
        elif image_source.startswith('http://') or image_source.startswith('https://'):
            image_base64_string, mime_type = download_image_to_base64(image_source)
        else:
            # Handle other cases or raise an error
            raise ValueError("Unsupported image source format")
    except Exception as e:
        logger.error("An error occurred while updating channel image: %s", e)
        # Return the placeholder image
        mime_type = 'image/png'
        image_base64_string = placeholder_base64

    # Prepend the MIME type and base64 header and return
    base64_string_with_header = f"data:{mime_type};base64,{image_base64_string}"
    return base64_string_with_header


def read_base46_image_string(base64_string):
    # Extract the MIME type and decode the base64 string
    try:
        mime_type = base64_string.split(';')[0].split(':')[1]
        image_data = base64.b64decode(base64_string.split(',')[1])
    except Exception as e:
        logger.error("An error occurred while parsing base64 image string: %s", e)
        mime_type = None
        image_data = None
    return image_data, mime_type


def read_channel_logo(channel_id):
    channel = db.session.query(Channel).where(Channel.id == channel_id).one()
    base64_string = channel.logo_base64
    if not base64_string:
        # Revert to using the logo url
        base64_string, mime_type = download_image_to_base64(channel.logo_url)
    image_base64_string, mime_type = read_base46_image_string(base64_string)
    return image_base64_string, mime_type


async def add_new_channel(config, data, commit=True):
    channel = Channel(
        enabled=data.get('enabled'),
        name=data.get('name'),
        logo_url=data.get('logo_url'),
        number=data.get('number'),
    )
    # Add tags
    channel.tags.clear()
    for tag_name in data.get('tags', []):
        channel_tag = db.session.query(ChannelTag).filter(ChannelTag.name == tag_name).one_or_none()
        if not channel_tag:
            channel_tag = ChannelTag(name=tag_name)
            db.session.add(channel_tag)
        channel.tags.append(channel_tag)

    # Programme Guide
    guide_info = data.get('guide', {})
    if guide_info.get('epg_id'):
        channel_guide_source = db.session.query(Epg).filter(Epg.id == guide_info['epg_id']).one()
        channel.guide_id = channel_guide_source.id
        channel.guide_name = channel_guide_source.name
        channel.guide_channel_id = guide_info['channel_id']

    # Sources
    new_sources = []
    for source_info in data.get('sources', []):
        playlist_info = db.session.query(Playlist).filter(Playlist.id == source_info['playlist_id']).one()
        playlist_streams = fetch_playlist_streams(playlist_info.id)
        playlist_stream = playlist_streams.get(source_info['stream_name'])
        channel_source = ChannelSource(
            playlist_id=playlist_info.id,
            playlist_stream_name=source_info['stream_name'],
            playlist_stream_url=playlist_stream['url'],
        )
        new_sources.append(channel_source)
    if new_sources:
        channel.sources.clear()
        channel.sources = new_sources

    # Host an image cache
    # if data.get('logo_url'):
    channel.logo_base64 = parse_image_as_base64(data.get('logo_url'))

    # Publish changes to TVH
    channel_uuid = await publish_channel_to_tvh(config, channel)
    # Save network UUID against playlist in settings
    channel.tvh_uuid = channel_uuid

    # Add new row and commit
    db.session.add(channel)
    if commit:
        db.session.commit()


def update_channel(config, channel_id, data):
    settings = config.read_settings()
    channel = db.session.query(Channel).where(Channel.id == channel_id).one()
    channel.enabled = data.get('enabled')
    channel.name = data.get('name')
    channel.logo_url = data.get('logo_url')
    channel.number = data.get('number')

    # Category Tags
    # -- Remove existing tags
    channel.tags.clear()
    # -- Add tags
    new_tags = []
    for tag_name in data.get('tags', []):
        channel_tag = db.session.query(ChannelTag).filter(ChannelTag.name == tag_name).one_or_none()
        if not channel_tag:
            channel_tag = ChannelTag(name=tag_name)
            db.session.add(channel_tag)
        new_tags.append(channel_tag)
    channel.tags = new_tags

    # Programme Guide
    guide_info = data.get('guide', {})
    if guide_info.get('epg_id'):
        channel_guide_source = db.session.query(Epg).filter(Epg.id == guide_info['epg_id']).one()
        channel.guide_id = channel_guide_source.id
        channel.guide_name = guide_info['epg_name']
        channel.guide_channel_id = guide_info['channel_id']

    # Sources
    new_source_ids = []
    new_sources = []
    priority = len(data.get('sources', []))
    logger.info("Updating channel sources")
    for source_info in data.get('sources', []):
        channel_source = db.session.query(ChannelSource) \
            .filter(and_(ChannelSource.channel_id == channel.id,
                         ChannelSource.playlist_id == source_info['playlist_id'],
                         ChannelSource.playlist_stream_name == source_info['stream_name']
                         )) \
            .one_or_none()
        if not channel_source:
            logger.info("    - Adding new channel source for channel %s 'Playlist:%s - %s'", channel.name,
                        source_info['playlist_id'], source_info['stream_name'])
            playlist_info = db.session.query(Playlist).filter(Playlist.id == source_info['playlist_id']).one()
            playlist_streams = fetch_playlist_streams(playlist_info.id)
            playlist_stream = playlist_streams.get(source_info['stream_name'])
            if playlist_info.use_hls_proxy:
                app_url = settings['settings']['app_url']
                # noinspection HttpUrlsUsage
                playlist_stream['url'] = f'{app_url}/tic-hls-proxy.m3u8?url={playlist_stream['url']}'
            channel_source = ChannelSource(
                playlist_id=playlist_info.id,
                playlist_stream_name=source_info['stream_name'],
                playlist_stream_url=playlist_stream['url'],
            )
        else:
            logger.info("    - Found existing channel source for channel %s 'Playlist:%s - %s'", channel.name,
                        source_info['playlist_id'], source_info['stream_name'])
            new_source_ids.append(channel_source.id)
            # Filter sources to refresh here. Things not added to the new_source_ids list are removed and re-added
            for refresh_source_info in data.get('refresh_sources', []):
                if (refresh_source_info['playlist_id'] == source_info['playlist_id']
                        and refresh_source_info['stream_name'] == source_info['stream_name']):
                    logger.info("    - Channel %s source marked for refresh 'Playlist:%s - %s'", channel.name,
                                source_info['playlist_id'], source_info['stream_name'])
                    playlist_info = db.session.query(Playlist).filter(Playlist.id == source_info['playlist_id']).one()
                    playlist_streams = fetch_playlist_streams(playlist_info.id)
                    playlist_stream = playlist_streams.get(source_info['stream_name'])
                    if playlist_info.use_hls_proxy:
                        app_url = settings['settings']['app_url']
                        # noinspection HttpUrlsUsage
                        playlist_stream['url'] = f'{app_url}/tic-hls-proxy.m3u8?url={playlist_stream['url']}'
                    # Update playlist stream url
                    logger.info("    - Updating channel %s source from '%s' to '%s'", channel.name,
                                channel_source.playlist_stream_url, playlist_stream['url'])
                    channel_source.playlist_stream_url = playlist_stream['url']
                    break
        # Update source priority (higher means higher priority
        channel_source.priority = priority
        priority -= 1
        # Append to list of new sources
        new_sources.append(channel_source)
    # Remove all old entries in the channel_sources table
    current_sources = db.session.query(ChannelSource).filter_by(channel_id=channel.id)
    for source in current_sources:
        if source.id not in new_source_ids:
            if source.tvh_uuid:
                # Delete mux from TVH
                delete_channel_muxes(config, source.tvh_uuid)
            db.session.delete(source)
    if new_sources:
        channel.sources.clear()
        channel.sources = new_sources

    # Commit
    db.session.commit()


async def add_bulk_channels(config, data):
    channel_number = db.session.query(func.max(Channel.number)).scalar()
    if channel_number is None:
        channel_number = 999
    for channel in data:
        # Make this new channel the next highest
        channel_number = channel_number + 1
        # Build new channel data
        new_channel_data = {
            'enabled': True,
            'tags':    [],
            'sources': [],
        }
        # Fetch the playlist channel by ID
        playlist_stream = db.session.query(PlaylistStreams).where(PlaylistStreams.id == channel['stream_id']).one()
        # Auto assign the name
        new_channel_data['name'] = playlist_stream.name
        # Auto assign the image URL
        new_channel_data['logo_url'] = playlist_stream.tvg_logo
        # Auto assign the channel number to the next available number
        new_channel_data['number'] = int(channel_number)
        # Find the best match for an EPG
        epg_match = db.session.query(EpgChannels).filter(EpgChannels.channel_id == playlist_stream.tvg_id).first()
        if epg_match is not None:
            new_channel_data['guide'] = {
                'channel_id': epg_match.channel_id,
                'epg_id':     1,
                'epg_name':   epg_match.name,
            }
        # Apply the stream to the channel
        new_channel_data['sources'].append({
            'playlist_id':   channel['playlist_id'],
            'playlist_name': playlist_stream.playlist.name,
            'stream_name':   playlist_stream.name
        })
        # Create new channel from data.
        # Delay commit of transaction until all new channels are created
        await add_new_channel(config, new_channel_data, commit=False)
    # Commit all new channels
    db.session.commit()


def delete_channel(config, channel_id):
    channel = db.session.query(Channel).where(Channel.id == channel_id).one()
    # Remove all source entries in the channel_sources table
    current_sources = db.session.query(ChannelSource).filter_by(channel_id=channel.id)
    for source in current_sources:
        if source.tvh_uuid:
            # Delete mux from TVH
            delete_channel_muxes(config, source.tvh_uuid)
        db.session.delete(source)
    # Clear out association table. This fixes an issue where if multiple similar entries ended up in that table,
    # no more updates could be made to the channel.
    #   > sqlalchemy.orm.exc.StaleDataError:
    #   > DELETE statement on table 'channels_tags_group' expected to delete 1 row(s); Only 2 were matched.
    stmt = channels_tags_association_table.delete().where(
        channels_tags_association_table.c.channel_id == channel_id
    )
    db.session.execute(stmt)
    # Remove channel from DB
    db.session.delete(channel)
    db.session.commit()


async def publish_channel_to_tvh(config, channel):
    logger.info("Publishing channel to TVH - %s.", channel.name)
    tvh = await get_tvh(config)
    # Check if channel exists with a matching UUID and create it if not
    channel_uuid = channel.tvh_uuid
    existing_channels = await tvh.list_all_channels()
    if channel_uuid:
        found = False
        for tvh_channel in existing_channels:
            if tvh_channel.get('uuid') == channel_uuid:
                found = True
        if not found:
            channel_uuid = None
    if not channel_uuid:
        # No channel exists, create one
        logger.info("   - Creating new channel in TVH")
        channel_uuid = await tvh.create_channel(channel.name, channel.number, channel.logo_url)
    else:
        logger.info("   - Found existing channel in TVH")
    channel_conf = {
        'enabled': True,
        'uuid':    channel_uuid,
        "name":    channel.name,
        "number":  channel.number,
        "icon":    channel.logo_url
    }
    # Check for existing channel tags
    existing_tag_details = {}
    logger.info("   - Fetching details of channel tags in TVH")
    for tvh_channel_tag in await tvh.list_all_managed_channel_tags():
        existing_tag_details[tvh_channel_tag.get('name')] = tvh_channel_tag.get('uuid')
    # Create channel tags in TVH if missing
    channel_tag_uuids = []
    for tag in channel.tags:
        tag_uuid = existing_tag_details.get(tag.name)
        if not tag_uuid:
            # Create channel tag
            logger.info("Creating new channel tag '%s'", tag.name)
            tag_uuid = await tvh.create_channel_tag(tag.name)
        channel_tag_uuids.append(tag_uuid)
    # Apply channel tag UUIDs to chanel conf in TVH
    channel_conf["tags"] = channel_tag_uuids
    # Save channel info in TVH
    await tvh.idnode_save(channel_conf)
    return channel_uuid


async def publish_bulk_channels_to_tvh(config):
    tvh = await get_tvh(config)
    # Loop over configured channels
    managed_uuids = []
    results = db.session.query(Channel) \
        .options(joinedload(Channel.tags), joinedload(Channel.sources).subqueryload(ChannelSource.playlist)) \
        .order_by(Channel.id, Channel.number.asc()) \
        .all()
    # Fetch existing channels
    logger.info("Publishing all channels to TVH")
    for result in results:
        channel_uuid = await publish_channel_to_tvh(config, result)
        # Save network UUID against playlist in settings
        result.tvh_uuid = channel_uuid
        # Generate a local image cache
        result.logo_base64 = parse_image_as_base64(result.logo_url)
        # Save channel details
        db.session.commit()
        # Append to list of current network UUIDs
        managed_uuids.append(channel_uuid)

    #  Remove any channels that are not managed.
    logger.info("Running cleanup task on current TVH channels")
    for existing_channel in await tvh.list_all_channels():
        if existing_channel.get('uuid') not in managed_uuids:
            logger.info("    - Removing channel UUID - %s", existing_channel.get('uuid'))
            await tvh.delete_channel(existing_channel.get('uuid'))


async def publish_channel_muxes(config):
    tvh = await get_tvh(config)
    # Loop over configured channels
    managed_uuids = []
    results = db.session.query(Channel) \
        .options(joinedload(Channel.tags), joinedload(Channel.sources).subqueryload(ChannelSource.playlist)) \
        .order_by(Channel.id, Channel.number.asc()) \
        .all()
    existing_muxes = await tvh.list_all_muxes()
    for result in results:
        if result.enabled:
            logger.info("Configuring MUX for channel '%s'", result.name)
            # Create/update a network in TVH for each enabled playlist line
            for source in result.sources:
                # Write playlist to TVH Network
                net_uuid = source.playlist.tvh_uuid
                if not net_uuid:
                    # Show error
                    logger.info("Playlist is not configured on TVH")
                    continue
                # Check if MUX exists with a matching UUID and create it if not
                mux_uuid = source.tvh_uuid
                run_mux_scan = False
                if mux_uuid:
                    found = False
                    for mux in existing_muxes:
                        if mux.get('uuid') == mux_uuid:
                            found = True
                            if mux.get('scan_result') == 2:
                                # Scan failed last time, re-run it
                                run_mux_scan = True
                    if not found:
                        mux_uuid = None
                if not mux_uuid:
                    logger.info("    - Creating new MUX for channel '%s' with stream '%s'", result.name,
                                source.playlist_stream_url)
                    # No mux exists, create one
                    mux_uuid = await tvh.network_mux_create(net_uuid)
                    logger.info(mux_uuid)
                    run_mux_scan = True
                else:
                    logger.info("    - Updating existing MUX '%s' for channel '%s' with stream '%s'", mux_uuid,
                                result.name, source.playlist_stream_url)
                # Update mux
                service_name = f"{source.playlist.name} - {source.playlist_stream_name}"
                iptv_url = generate_iptv_url(
                    config,
                    url=source.playlist_stream_url,
                    service_name=service_name,
                )
                channel_id = f"{result.number}_{re.sub(r'[^a-zA-Z0-9]', '', result.name)}"
                mux_conf = {
                    'enabled':        1,
                    'uuid':           mux_uuid,
                    'iptv_url':       iptv_url,
                    'iptv_icon':      result.logo_url,
                    'iptv_sname':     result.name,
                    'iptv_muxname':   service_name,
                    'channel_number': result.number,
                    'iptv_epgid':     channel_id,
                    "priority":       source.priority, "spriority": source.priority,
                }
                if run_mux_scan:
                    mux_conf['scan_state'] = 1
                await tvh.idnode_save(mux_conf)
                # Save network UUID against playlist in settings
                source.tvh_uuid = mux_uuid
                db.session.commit()
                # Append to list of current network UUIDs
                managed_uuids.append(mux_uuid)

    #  Remove any muxes that are not managed.
    logger.info("Running cleanup task on current TVH muxes")
    for existing_mux in await tvh.list_all_muxes():
        if existing_mux.get('uuid') not in managed_uuids:
            logger.info("    - Removing mux UUID - %s", existing_mux.get('uuid'))
            await tvh.delete_mux(existing_mux.get('uuid'))


async def delete_channel_muxes(config, mux_uuid):
    tvh = await get_tvh(config)
    await tvh.delete_mux(mux_uuid)


async def map_all_services(config):
    logger.info("Executing TVH Map all service")
    tvh = await get_tvh(config)
    await tvh.map_all_services_to_channels()


async def cleanup_old_channels(config):
    logger.info("Cleaning up old TVH channels")
    tvh = await get_tvh(config)
    for channel in await tvh.list_all_channels():
        if channel.get('name') == "{name-not-set}":
            logger.info("    - Removing channel UUID - %s", channel.get('uuid'))
            await tvh.delete_channel(channel.get('uuid'))


async def queue_background_channel_update_tasks(config):
    settings = config.read_settings()
    # Update TVH
    from backend.api.tasks import TaskQueueBroker
    task_broker = await TaskQueueBroker.get_instance()
    # Configure TVH with the list of channels
    await task_broker.add_task({
        'name':     'Configuring TVH channels',
        'function': publish_bulk_channels_to_tvh,
        'args':     [config],
    }, priority=11)
    # Configure TVH with muxes
    await task_broker.add_task({
        'name':     'Configuring TVH muxes',
        'function': publish_channel_muxes,
        'args':     [config],
    }, priority=12)
    # Map all services
    await task_broker.add_task({
        'name':     'Mapping all TVH services',
        'function': map_all_services,
        'args':     [config],
    }, priority=13)
    # Clear out old channels
    await task_broker.add_task({
        'name':     'Cleanup old TVH channels',
        'function': cleanup_old_channels,
        'args':     [config],
    }, priority=14)
    # Fetch additional EPG data from the internet
    from backend.epgs import update_channel_epg_with_online_data
    if settings['settings'].get('epgs', {}).get('enable_tmdb_metadata'):
        await task_broker.add_task({
            'name':     'Update EPG Data with online metadata',
            'function': update_channel_epg_with_online_data,
            'args':     [config],
        }, priority=21)
    # Generate 'epg.xml' file in .tvh_iptv_config directory
    from backend.epgs import build_custom_epg
    await task_broker.add_task({
        'name':     'Recreating static XMLTV file',
        'function': build_custom_epg,
        'args':     [config],
    }, priority=23)
    # Trigger an update in TVH to fetch the latest EPG
    from backend.epgs import run_tvh_epg_grabbers
    await task_broker.add_task({
        'name':     'Triggering an update in TVH to fetch the latest XMLTV',
        'function': run_tvh_epg_grabbers,
        'args':     [config],
    }, priority=31)
