#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import base64
import logging
import os
import re
from mimetypes import guess_type

import aiofiles
import aiohttp
import requests
import asyncio
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_, func, select

from backend.ffmpeg import generate_iptv_url
from backend.models import db, Session, Channel, ChannelTag, Epg, ChannelSource, Playlist, EpgChannels, PlaylistStreams, \
    channels_tags_association_table
from backend.playlists import fetch_playlist_streams
from backend.tvheadend.tvh_requests import get_tvh

logger = logging.getLogger('tic.channels')

image_placeholder_base64 = 'iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAACiUlEQVR4nO2cy46sMAxEzdX8/y/3XUSKUM+I7sLlF6qzYgE4HJwQEsLxer1MfMe/6gJMQrIAJAtAsgAkC0CyACQLQLIAJAtAsgAkC0CyACQLQLIAJAtAsgAkC0CyACQL4Md5/HEclFH84ziud+gwV+C61H2F905yFvTxDNDOQXjz4p6vddTt0M7Db0OoRN/7cmZi6Nm+iphWblbrlnnm90CsMBe+EmpNTsVk3pM/faXd9oRYzH7WLui2lmlqFeBjF8QD/2LKn/Fxd4jfgy/vPcblV+zrTmiluCDIF1/WqgW/269kInyRZZ3bi+f5Ysr63bI+zFf4EE25LyI0WRcP7FpfxOTiyPrYtXmGr7yR0gfUx9Rh5em+CLKg14sqX5SaWDBhMTe/vLLuvbWW+PInV9lU2MT8qpw3HOereJJ1li+XLMowW6YvZ7PVYvp+Sn61kGVDfHWRZRN8NZJl7X31kmW9fbWTZY19dZRlXX01lWUtffWVZf18tZZlzXy5ZEV/iLGjrA1/LOf7WffMWjTJrxmyrIevMbKsgS+vrJxm6xxubdwI6h9QmpRZi8L8IshKTi675YsyTjkvsxYl+TVVllX44sjKr4k77tq4js76JJeWWW19ET9eHlwNN2n1kbxooPBzyLXxVgDuN/HkzGrli756IGQxQvIqlLfQe5tehpA2q0N+RRDVwBf62nRfNHCmxFfo+o7YrkOyr+j1HRktceFKVvKq7AcsM70+M9FX6jO+avU9K25Nhyj/vw4UX2W9R0v/Y4jfV6WsMzn/ovH+D6aJrDQ8z5knDNFAPH9GugmSBSBZAJIFIFkAkgUgWQCSBSBZAJIFIFkAkgUgWQCSBSBZAJIFIFkA/wGlHK2X7Li2TQAAAABJRU5ErkJggg=='


async def read_config_all_channels(filter_playlist_ids=None, output_for_export=False):
    if filter_playlist_ids is None:
        filter_playlist_ids = []

    return_list = []

    async with Session() as session:
        async with session.begin():
            result = await session.execute(
                select(Channel)
                .options(
                    joinedload(Channel.tags),
                    joinedload(Channel.sources).subqueryload(ChannelSource.playlist)
                ).order_by(Channel.id)
            )
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


async def download_image_to_base64(image_source, timeout=10):
    # Image source is a URL
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62'
            }
            async with session.get(image_source, headers=headers) as response:
                response.raise_for_status()
                image_data = await response.read()
                mime_type = response.headers.get('Content-Type',
                                                 'image/jpeg')  # Fallback to JPEG if no content-type header

                image_base64_string = base64.b64encode(image_data).decode()
    except Exception as e:
        logger.error("An error occurred while downloading image: %s", e)
        mime_type = 'image/png'
        image_base64_string = image_placeholder_base64

    return image_base64_string, mime_type


async def parse_image_as_base64(image_source):
    try:
        if image_source.startswith('data:image/'):
            mime_type = image_source.split(';')[0].split(':')[1]
            image_base64_string = image_source.split('base64,')[1]
        elif image_source.startswith('http://') or image_source.startswith('https://'):
            image_base64_string, mime_type = await download_image_to_base64(image_source, timeout=3)
        else:
            # Handle other cases or raise an error
            raise ValueError("Unsupported image source format")
    except Exception as e:
        logger.error("An error occurred while updating channel image: %s", e)
        # Return the placeholder image
        mime_type = 'image/png'
        image_base64_string = image_placeholder_base64

    # Prepend the MIME type and base64 header and return
    base64_string_with_header = f"data:{mime_type};base64,{image_base64_string}"
    return base64_string_with_header


async def read_base46_image_string(base64_string):
    # Extract the MIME type and decode the base64 string
    try:
        mime_type = base64_string.split(';')[0].split(':')[1]
        image_data = base64.b64decode(base64_string.split(',')[1])
    except Exception as e:
        logger.error("An error occurred while parsing base64 image string: %s", e)
        mime_type = None
        image_data = None
    return image_data, mime_type


async def read_channel_logo(channel_id):
    channel = db.session.query(Channel).where(Channel.id == channel_id).one()
    base64_string = channel.logo_base64
    if not base64_string:
        # Revert to using the logo url
        base64_string, mime_type = await download_image_to_base64(channel.logo_url)
    image_base64_string, mime_type = await read_base46_image_string(base64_string)
    return image_base64_string, mime_type


async def add_new_channel(config, data, commit=True):
    settings = config.read_settings()
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
        # Modify stream if using HLS proxy
        if playlist_info.use_hls_proxy:
            if not playlist_info.use_custom_hls_proxy:
                app_url = settings['settings']['app_url']
                playlist_url = playlist_stream['url']
                extension = 'ts'
                if playlist_url.endswith('m3u8'):
                    extension = 'm3u8'
                encoded_playlist_url = base64.b64encode(playlist_url.encode('utf-8')).decode('utf-8')
                # noinspection HttpUrlsUsage
                playlist_stream['url'] = f'{app_url}/tic-hls-proxy/{encoded_playlist_url}.{extension}'
            else:
                hls_proxy_path = playlist_info.hls_proxy_path
                playlist_url = playlist_stream['url']
                encoded_playlist_url = base64.b64encode(playlist_url.encode('utf-8')).decode('utf-8')
                hls_proxy_path = hls_proxy_path.replace("[URL]", playlist_url)
                hls_proxy_path = hls_proxy_path.replace("[B64_URL]", encoded_playlist_url)
                playlist_stream['url'] = hls_proxy_path
        channel_source = ChannelSource(
            playlist_id=playlist_info.id,
            playlist_stream_name=source_info['stream_name'],
            playlist_stream_url=playlist_stream['url'],
        )
        new_sources.append(channel_source)
    if new_sources:
        channel.sources.clear()
        channel.sources = new_sources

    # Publish changes to TVH
    async with await get_tvh(config) as tvh:
        channel_uuid = await publish_channel_to_tvh(tvh, channel)
        # Save network UUID against playlist in settings
        channel.tvh_uuid = channel_uuid

        # Add new row and commit
        db.session.add(channel)
        if commit:
            db.session.commit()


async def update_channel(config, channel_id, data):
    settings = config.read_settings()
    async with Session() as session:
        async with session.begin():
            query = await session.execute(
                select(Channel).where(Channel.id == channel_id)
                .options(selectinload(Channel.tags), selectinload(Channel.sources))
            )
            channel = query.scalar_one()
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
                query = await session.execute(select(ChannelTag).filter(ChannelTag.name == tag_name))
                channel_tag = query.scalar_one_or_none()
                if not channel_tag:
                    channel_tag = ChannelTag(name=tag_name)
                    session.add(channel_tag)
                new_tags.append(channel_tag)
            channel.tags = new_tags

            # Programme Guide
            guide_info = data.get('guide', {})
            if guide_info.get('epg_id'):
                query = await session.execute(select(Epg).filter(Epg.id == guide_info['epg_id']))
                channel_guide_source = query.scalar_one()
                channel.guide_id = channel_guide_source.id
                channel.guide_name = guide_info['epg_name']
                channel.guide_channel_id = guide_info['channel_id']

            # Sources
            new_source_ids = []
            new_sources = []
            priority = len(data.get('sources', []))
            logger.info("Updating channel sources")
            for source_info in data.get('sources', []):
                query = await session.execute(select(ChannelSource)
                                              .filter(and_(ChannelSource.channel_id == channel.id,
                                                           ChannelSource.playlist_id == source_info['playlist_id'],
                                                           ChannelSource.playlist_stream_name == source_info[
                                                               'stream_name']
                                                           )))
                channel_source = query.scalar_one_or_none()
                if not channel_source:
                    logger.info("    - Adding new channel source for channel %s 'Playlist:%s - %s'", channel.name,
                                source_info['playlist_id'], source_info['stream_name'])

                    query = await session.execute(select(Playlist).filter(Playlist.id == source_info['playlist_id']))
                    playlist_info = query.scalar_one()
                    playlist_streams = fetch_playlist_streams(playlist_info.id)
                    playlist_stream = playlist_streams.get(source_info['stream_name'])
                    if playlist_info.use_hls_proxy:
                        if not playlist_info.use_custom_hls_proxy:
                            app_url = settings['settings']['app_url']
                            playlist_url = playlist_stream['url']
                            extension = 'ts'
                            if playlist_url.endswith('m3u8'):
                                extension = 'm3u8'
                            encoded_playlist_url = base64.b64encode(playlist_url.encode('utf-8')).decode('utf-8')
                            # noinspection HttpUrlsUsage
                            playlist_stream['url'] = f'{app_url}/tic-hls-proxy/{encoded_playlist_url}.{extension}'
                        else:
                            hls_proxy_path = playlist_info.hls_proxy_path
                            playlist_url = playlist_stream['url']
                            encoded_playlist_url = base64.b64encode(playlist_url.encode('utf-8')).decode('utf-8')
                            hls_proxy_path = hls_proxy_path.replace("[URL]", playlist_url)
                            hls_proxy_path = hls_proxy_path.replace("[B64_URL]", encoded_playlist_url)
                            playlist_stream['url'] = hls_proxy_path
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
                            query = await session.execute(
                                select(Playlist).filter(
                                    Playlist.id == source_info['playlist_id']))
                            playlist_info = query.scalar_one()
                            playlist_streams = fetch_playlist_streams(playlist_info.id)
                            playlist_stream = playlist_streams.get(source_info['stream_name'])
                            if playlist_info.use_hls_proxy:
                                if not playlist_info.use_custom_hls_proxy:
                                    app_url = settings['settings']['app_url']
                                    playlist_url = playlist_stream['url']
                                    extension = 'ts'
                                    if playlist_url.endswith('m3u8'):
                                        extension = 'm3u8'
                                    encoded_playlist_url = base64.b64encode(playlist_url.encode('utf-8')).decode(
                                        'utf-8')
                                    # noinspection HttpUrlsUsage
                                    playlist_stream[
                                        'url'] = f'{app_url}/tic-hls-proxy/{encoded_playlist_url}.{extension}'
                                else:
                                    hls_proxy_path = playlist_info.hls_proxy_path
                                    playlist_url = playlist_stream['url']
                                    encoded_playlist_url = base64.b64encode(playlist_url.encode('utf-8')).decode(
                                        'utf-8')
                                    hls_proxy_path = hls_proxy_path.replace("[URL]", playlist_url)
                                    hls_proxy_path = hls_proxy_path.replace("[B64_URL]", encoded_playlist_url)
                                    playlist_stream['url'] = hls_proxy_path
                            # Update playlist stream url
                            logger.info("    - Updating channel %s source from '%s' to '%s'", channel.name,
                                        channel_source.playlist_stream_url, playlist_stream['url'])
                            channel_source.playlist_stream_url = playlist_stream['url']
                            break
                # Update source priority (higher means higher priority)
                channel_source.priority = priority
                priority -= 1
                # Append to list of new sources
                new_sources.append(channel_source)
            # Remove all old entries in the channel_sources table
            query = await session.execute(select(ChannelSource).filter_by(channel_id=channel.id))
            current_sources = query.scalars().all()
            for source in current_sources:
                if source.id not in new_source_ids:
                    if source.tvh_uuid:
                        # Delete mux from TVH
                        await delete_channel_muxes(config, source.tvh_uuid)
                    await session.delete(source)
            if new_sources:
                channel.sources.clear()
                channel.sources = new_sources

            # Commit
            await session.commit()


async def add_bulk_channels(config, channels_list):
    # First, determine the starting channel number
    async with Session() as session:
        result = await session.execute(select(func.max(Channel.number)))
        max_channel_number = result.scalar()
        channel_number = 999 if max_channel_number is None else max_channel_number
    
    # Add each channel one by one
    channels_added = 0
    for channel_data in channels_list:
        try:
            playlist_id = channel_data.get('playlist_id')
            stream_id = channel_data.get('stream_id')
            
            # Fetch the stream info first
            async with Session() as session:
                async with session.begin():
                    # Use first() instead of one() to avoid multiple row errors
                    result = await session.execute(
                        select(PlaylistStreams)
                        .where(PlaylistStreams.id == stream_id)
                        .where(PlaylistStreams.playlist_id == playlist_id)
                    )
                    stream = result.scalar_one_or_none()
                    
                    if not stream:
                        logger.warning(f"Stream with ID {stream_id} not found")
                        continue
                    
                    # Check if the channel already exists with this name
                    # Use first() instead of one() to handle multiple results
                    existing_channel_result = await session.execute(
                        select(Channel)
                        .where(Channel.name == stream.name)
                        .limit(1)  # Limit to avoid multiple results
                    )
                    existing_channel = existing_channel_result.scalar_one_or_none()
                    
                    if existing_channel:
                        logger.info(f"Channel '{stream.name}' already exists (ID: {existing_channel.id}) - updating")
                        
                        # Update source only if it doesn't exist already
                        source_exists = False
                        for source in existing_channel.sources:
                            if source.playlist_id == playlist_id and source.playlist_stream_name == stream.name:
                                source_exists = True
                                break
                                
                        if not source_exists:
                            logger.info(f"Adding new source to existing channel '{stream.name}'")
                            source = ChannelSource(
                                channel_id=existing_channel.id,
                                playlist_id=playlist_id,
                                playlist_stream_name=stream.name,
                                playlist_stream_url=stream.url,
                                priority=1
                            )
                            session.add(source)
                            
                        # Add tags if provided and not already present
                        tag_names = channel_data.get('tags', [])
                        for tag_name in tag_names:
                            tag_exists = False
                            for tag in existing_channel.tags:
                                if tag.name == tag_name:
                                    tag_exists = True
                                    break
                                    
                            if not tag_exists:
                                # Find or create tag
                                tag_result = await session.execute(
                                    select(ChannelTag).where(ChannelTag.name == tag_name)
                                )
                                tag = tag_result.scalar_one_or_none()
                                if not tag:
                                    tag = ChannelTag(name=tag_name)
                                    session.add(tag)
                                    await session.flush()
                                
                                existing_channel.tags.append(tag)
                    else:
                        # Create a new channel
                        channel_number += 1
                        logger.info(f"Creating new channel '{stream.name}' with number {channel_number}")
                        
                        # Create the channel object
                        channel = Channel(
                            enabled=True,
                            name=stream.name,
                            logo_url=stream.tvg_logo,
                            number=channel_number,
                        )
                        
                        # Add source
                        source = ChannelSource(
                            playlist_id=playlist_id,
                            playlist_stream_name=stream.name,
                            playlist_stream_url=stream.url,
                            priority=1
                        )
                        
                        # Handle tags
                        tag_objects = []
                        tag_names = channel_data.get('tags', [])
                        for tag_name in tag_names:
                            logger.info(f"Adding tag '{tag_name}' to channel '{stream.name}'")
                            # Find or create tag
                            tag_result = await session.execute(
                                select(ChannelTag).where(ChannelTag.name == tag_name)
                            )
                            tag = tag_result.scalar_one_or_none()
                            if not tag:
                                tag = ChannelTag(name=tag_name)
                                session.add(tag)
                                await session.flush()
                            tag_objects.append(tag)
                            
                        # Set channel relationships
                        channel.tags = tag_objects
                        channel.sources = [source]
                        
                        # Add channel
                        session.add(channel)
                        channels_added += 1
                        
                    # Commit changes
                    await session.commit()
                    
        except Exception as e:
            logger.error(f"Error adding channel: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info(f"Added {channels_added} new channels")
    return channels_added


async def delete_channel(config, channel_id):
    async with Session() as session:
        async with session.begin():
            # Use select() instead of query()
            result = await session.execute(select(Channel).where(Channel.id == channel_id))
            channel = result.scalar_one()
            
            # Remove all source entries in the channel_sources table
            result = await session.execute(select(ChannelSource).filter_by(channel_id=channel.id))
            current_sources = result.scalars().all()
            
            for source in current_sources:
                if source.tvh_uuid:
                    # Delete mux from TVH
                    await delete_channel_muxes(config, source.tvh_uuid)
                await session.delete(source)
                
            # Clear out association table. This fixes an issue where if multiple similar entries ended up in that table,
            # no more updates could be made to the channel.
            #   > sqlalchemy.orm.exc.StaleDataError:
            #   > DELETE statement on table 'channels_tags_group' expected to delete 1 row(s); Only 2 were matched.
            stmt = channels_tags_association_table.delete().where(
                channels_tags_association_table.c.channel_id == channel_id
            )
            await session.execute(stmt)
            
            # Remove channel from DB
            await session.delete(channel)
            await session.commit()


async def build_m3u_lines_for_channel(tic_base_url, channel_uuid, channel):
    playlist = []
    line = f'#EXTINF:-1 tvg-name="{channel.name}" tvg-logo="{channel.logo_url}" tvg-id="{channel_uuid}" tvg-chno="{channel.number}"'
    if channel.tags:
        line += f' group-title="{channel.tags[0]}"'
    line += f',{channel.name}'
    playlist.append(line)
    playlist.append(f'{tic_base_url}/tic-tvh/stream/channel/{channel_uuid}?profile=pass')
    return playlist


async def publish_channel_to_tvh(tvh, channel):
    logger.info("Publishing channel to TVH - %s.", channel.name)
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


async def publish_bulk_channels_to_tvh_and_m3u(config):
    settings = config.read_settings()
    tic_base_url = settings['settings']['app_url']
    async with await get_tvh(config) as tvh:
        # Loop over configured channels
        managed_uuids = []
        results = db.session.query(Channel) \
            .options(joinedload(Channel.tags), joinedload(Channel.sources).subqueryload(ChannelSource.playlist)) \
            .order_by(Channel.id, Channel.number.asc()) \
            .all()
        # Fetch existing channels
        logger.info("Publishing all channels to TVH and M3U")
        playlist = [f'#EXTM3U url-tvg="{tic_base_url}/tic-web/epg.xml"']
        for result in results:
            channel_uuid = await publish_channel_to_tvh(tvh, result)
            playlist += await build_m3u_lines_for_channel(tic_base_url, channel_uuid, result)
            # Save network UUID against playlist in settings
            result.tvh_uuid = channel_uuid
            # Generate a local image cache
            result.logo_base64 = await parse_image_as_base64(result.logo_url)
            # Save channel details
            db.session.commit()
            # Append to list of current network UUIDs
            managed_uuids.append(channel_uuid)

        # Write playlist file
        custom_playlist_file = os.path.join(config.config_path, "playlist.m3u8")
        async with aiofiles.open(custom_playlist_file, 'w', encoding='utf-8') as f:
            for item in playlist:
                await f.write(f'{item}\n')

        #  Remove any channels that are not managed.
        logger.info("Running cleanup task on current TVH channels")
        for existing_channel in await tvh.list_all_channels():
            if existing_channel.get('uuid') not in managed_uuids:
                logger.info("    - Removing channel UUID - %s", existing_channel.get('uuid'))
                await tvh.delete_channel(existing_channel.get('uuid'))


async def publish_channel_muxes(config):
    async with await get_tvh(config) as tvh:
        # Loop over configured channels
        managed_uuids = []
        results = db.session.query(Channel) \
            .options(joinedload(Channel.tags), joinedload(Channel.sources).subqueryload(ChannelSource.playlist)) \
            .order_by(Channel.id, Channel.number.asc()) \
            .all()
        existing_muxes = await tvh.list_all_muxes()
        
        # Liste aller EPG-Quellen abrufen
        epg_channels = {}
        epgs = db.session.query(Epg).all()
        for epg in epgs:
            epg_channels_result = db.session.query(EpgChannels).filter(EpgChannels.epg_id == epg.id).all()
            for ch in epg_channels_result:
                epg_channels[ch.channel_id] = {
                    'epg_id': epg.id,
                    'name': ch.name
                }
        
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
                    
                    # Determine EPG ID to use
                    epg_id = None
                    if result.guide_channel_id:
                        epg_id = result.guide_channel_id
                        logger.info(f"    - Using configured EPG ID: {epg_id}")
                    else:
                        # Versuche EPG-ID aus Kanalname oder anderen Quellen zu finden
                        normalized_name = re.sub(r'[^a-zA-Z0-9]', '', result.name.lower())
                        for epg_ch_id, epg_data in epg_channels.items():
                            normalized_epg_name = re.sub(r'[^a-zA-Z0-9]', '', epg_data['name'].lower())
                            if normalized_name == normalized_epg_name or normalized_name in normalized_epg_name:
                                epg_id = epg_ch_id
                                # Aktualisiere auch den Kanal mit dieser EPG-ID
                                result.guide_channel_id = epg_id
                                result.guide_id = epg_data['epg_id']
                                result.guide_name = epg_data['name']
                                db.session.commit()
                                logger.info(f"    - Found matching EPG: {epg_id}")
                                break
                                
                    # Fallback channel_id wenn kein EPG gefunden wurde
                    channel_id = f"{result.number}_{re.sub(r'[^a-zA-Z0-9]', '', result.name)}"
                    if epg_id:
                        channel_id = epg_id
                    
                    # Update mux
                    service_name = f"{source.playlist.name} - {source.playlist_stream_name}"
                    iptv_url = generate_iptv_url(
                        config,
                        url=source.playlist_stream_url,
                        service_name=service_name,
                    )
                    
                    mux_conf = {
                        'enabled':        1,
                        'uuid':           mux_uuid,
                        'iptv_url':       iptv_url,
                        'iptv_icon':      result.logo_url,
                        'iptv_sname':     result.name,
                        'iptv_muxname':   service_name,
                        'channel_number': result.number,
                        'iptv_epgid':     channel_id,
                        "priority":       source.priority, 
                        "spriority":      source.priority,
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
    async with await get_tvh(config) as tvh:
        await tvh.delete_mux(mux_uuid)


async def map_all_services(config):
    """Map all services to channels in TVHeadend."""
    logger.info("Executing TVH Map all service")
    async with await get_tvh(config) as tvh:
        # First, ensure all muxes are properly scanned with longer timeout
        await ensure_muxes_scanned(tvh)
        
        # Then map all services to channels
        await tvh.map_all_services_to_channels()
        
        # Give a short pause for changes to take effect
        await asyncio.sleep(5)
        
        # Verify and fix any channels without services
        await verify_channel_service_mapping(tvh)
        
        # Nach dem Service-Mapping sollten wir auch das EPG-Mapping überprüfen
        # EPG-Mapping in TVHeadend aktivieren
        logger.info("Configuring EPG in TVHeadend")
        
        # Abrufen der TVHeadend-Kanäle und ihrer Konfiguration
        channels = await tvh.list_all_channels()
        
        # Für jeden Kanal EPG-Mapping prüfen und ggf. konfigurieren
        for channel in channels:
            try:
                ch_uuid = channel.get('uuid')
                ch_name = channel.get('name')
                
                # Überprüfe, ob dieser Kanal in unserer Datenbank existiert
                db_channel = db.session.query(Channel).filter(Channel.tvh_uuid == ch_uuid).first()
                
                if db_channel and db_channel.guide_channel_id:
                    logger.info(f"Setting EPG mapping for channel {ch_name} to {db_channel.guide_channel_id}")
                    
                    # EPG-Mapping in TVHeadend konfigurieren
                    channel_conf = {
                        'uuid': ch_uuid,
                        'epgauto': 0,  # EPG auto-mapping deaktivieren
                        'epgid': db_channel.guide_channel_id  # Explizite EPG-ID setzen
                    }
                    
                    # Konfiguration speichern
                    await tvh.idnode_save(channel_conf)
            except Exception as e:
                logger.error(f"Error configuring EPG for channel: {e}")
        
        # TVHeadend EPG-Grabber ausführen
        await tvh.epg_grab_now()
        
    return True


async def ensure_muxes_scanned(tvh):
    """Stelle sicher, dass alle Muxes ordnungsgemäß gescannt wurden."""
    logger.info("Checking mux scan status")
    muxes = await tvh.list_all_muxes()
    
    # Finde Muxes, die noch nicht gescannt wurden oder bei denen der Scan fehlgeschlagen ist
    scan_needed = []
    for mux in muxes:
        if mux.get('scan_result', 0) != 1:  # Nicht erfolgreich gescannt
            # Starte einen Scan, indem scan_state auf 1 gesetzt wird
            mux_conf = {
                'uuid': mux.get('uuid'),
                'scan_state': 1  # Erzwinge Scan
            }
            await tvh.idnode_save(mux_conf)
            scan_needed.append(mux.get('uuid'))
    
    if scan_needed:
        logger.info(f"Started scanning {len(scan_needed)} muxes that need attention")
        
        # Erhöhte Basis-Wartezeit und pro-Mux-Wartezeit
        wait_time = max(60, len(scan_needed) * 15)
        logger.info(f"Waiting {wait_time} seconds for mux scanning to complete")
        await asyncio.sleep(wait_time)
        
        # Nach dem Warten überprüfen, ob weitere Muxes gescannt werden müssen
        muxes = await tvh.list_all_muxes()
        services = await tvh.list_all_services()
        logger.info(f"Found {len(services)} services after scanning")


async def verify_channel_service_mapping(tvh):
    """Verify all channels have services mapped to them."""
    logger.info("Verifying channel-service mapping")
    
    # Get list of channels and services
    channels = await tvh.list_all_channels()
    services = await tvh.list_all_services()
    
    logger.info(f"Found {len(channels)} channels and {len(services)} services in TVHeadend")
    
    # Debug log all services
    for service in services:
        logger.info(f"Service available: {service.get('svcname')} - UUID: {service.get('uuid')}")
    
    # Check each channel for services
    channels_without_services = []
    for channel in channels:
        if not channel.get('services'):
            channels_without_services.append(channel)
            logger.info(f"Channel without service: {channel.get('name')} - UUID: {channel.get('uuid')}")
    
    if channels_without_services:
        logger.warning(f"Found {len(channels_without_services)} channels without services mapped")
        
        # ATTEMPT 1: Try direct service mapper first (TVHeadend's built-in mapping)
        logger.info("Attempting to map all services using TVHeadend's built-in mapper")
        await tvh.map_all_services_to_channels()
        
        # Wait for this to take effect
        await asyncio.sleep(5)
        
        # Check again after built-in mapping
        channels = await tvh.list_all_channels()
        channels_without_services = []
        for channel in channels:
            if not channel.get('services'):
                channels_without_services.append(channel)
        
        if channels_without_services:
            logger.warning(f"After built-in mapping, still found {len(channels_without_services)} channels without services")
            
            # ATTEMPT 2: Try manual mapping for remaining channels
            logger.info("Attempting manual service mapping for remaining channels")
            
            # Get fresh list of services
            services = await tvh.list_all_services()
            
            # Map services to channels based on exact name match first
            for channel in list(channels_without_services):
                channel_name = channel.get('name', '')
                channel_uuid = channel.get('uuid')
                
                # Try to find exact service match first
                exact_match = None
                for service in services:
                    service_name = service.get('svcname', '')
                    
                    # Normalize names for comparison (remove HD, spaces, etc.)
                    norm_channel = channel_name.lower().replace(' hd', '').replace('-', '').replace('_', '').strip()
                    norm_service = service_name.lower().replace(' hd', '').replace('-', '').replace('_', '').strip()
                    
                    if norm_channel == norm_service:
                        exact_match = service
                        break
                
                if exact_match:
                    logger.info(f"Mapping service '{exact_match.get('svcname')}' to channel '{channel_name}' (exact match)")
                    channel_conf = {
                        'uuid': channel_uuid,
                        'services': [exact_match.get('uuid')]
                    }
                    await tvh.idnode_save(channel_conf)
                    channels_without_services.remove(channel)
            
            # For remaining channels, try fuzzy matching
            if channels_without_services:
                for channel in list(channels_without_services):
                    channel_name = channel.get('name', '')
                    channel_uuid = channel.get('uuid')
                    
                    best_match = None
                    best_score = 0
                    
                    for service in services:
                        service_name = service.get('svcname', '')
                        
                        # Skip services already mapped
                        already_mapped = False
                        for c in channels:
                            if c.get('services') and service.get('uuid') in c.get('services'):
                                already_mapped = True
                                break
                        
                        if already_mapped:
                            continue
                        
                        # Calculate similarity score (simple implementation)
                        # Normalize names for comparison
                        norm_channel = channel_name.lower().replace(' hd', '').replace('-', '').replace('_', '').strip()
                        norm_service = service_name.lower().replace(' hd', '').replace('-', '').replace('_', '').strip()
                        
                        # Check for substring matches
                        if norm_channel in norm_service or norm_service in norm_channel:
                            # Calculate similarity score
                            score = len(set(norm_channel) & set(norm_service)) / max(len(norm_channel), len(norm_service))
                            if score > best_score:
                                best_score = score
                                best_match = service
                    
                    if best_match and best_score > 0.5:  # Only map if reasonable match
                        logger.info(f"Mapping service '{best_match.get('svcname')}' to channel '{channel_name}' (fuzzy match, score: {best_score:.2f})")
                        channel_conf = {
                            'uuid': channel_uuid,
                            'services': [best_match.get('uuid')]
                        }
                        await tvh.idnode_save(channel_conf)
    
    return True


async def cleanup_old_channels(config):
    logger.info("Cleaning up old TVH channels")
    async with await get_tvh(config) as tvh:
        for channel in await tvh.list_all_channels():
            if channel.get('name') == "{name-not-set}":
                logger.info("    - Removing channel UUID - %s", channel.get('uuid'))
                await tvh.delete_channel(channel.get('uuid'))


async def queue_background_channel_update_tasks(config):
    settings = config.read_settings()
    # Update TVH
    from backend.api.tasks import TaskQueueBroker
    task_broker = await TaskQueueBroker.get_instance()
    
    current_tasks = await task_broker.get_pending_tasks()
    task_names = []
    if current_tasks:
        if isinstance(current_tasks[0], dict):
            task_names = [task.get('name') for task in current_tasks]
        elif isinstance(current_tasks[0], str):
            task_names = current_tasks
    
    if 'Configuring TVH channels' not in task_names:
        await task_broker.add_task({
            'name':     'Configuring TVH channels',
            'function': publish_bulk_channels_to_tvh_and_m3u,
            'args':     [config],
        }, priority=11)
    
    if 'Configuring TVH muxes' not in task_names:
        await task_broker.add_task({
            'name':     'Configuring TVH muxes',
            'function': publish_channel_muxes,
            'args':     [config],
        }, priority=12)
    
    if 'Mapping all TVH services' not in task_names:
        await task_broker.add_task({
            'name':     'Mapping all TVH services',
            'function': map_all_services,
            'args':     [config],
        }, priority=13)
    
    if 'Cleanup old TVH channels' not in task_names:
        await task_broker.add_task({
            'name':     'Cleanup old TVH channels',
            'function': cleanup_old_channels,
            'args':     [config],
        }, priority=14)
    
    # Restliche Tasks mit derselben Überprüfungslogik
    epg_settings = settings['settings'].get('epgs', {})
    if (epg_settings.get('enable_tmdb_metadata') or epg_settings.get('enable_google_image_search_metadata')) and \
            'Update EPG Data with online metadata' not in task_names:
        from backend.epgs import update_channel_epg_with_online_data
        await task_broker.add_task({
            'name':     'Update EPG Data with online metadata',
            'function': update_channel_epg_with_online_data,
            'args':     [config],
        }, priority=21)
    
    if 'Recreating static XMLTV file' not in task_names:
        from backend.epgs import build_custom_epg
        await task_broker.add_task({
            'name':     'Recreating static XMLTV file',
            'function': build_custom_epg,
            'args':     [config],
        }, priority=23)
    
    if 'Triggering an update in TVH to fetch the latest XMLTV' not in task_names:
        from backend.epgs import run_tvh_epg_grabbers
        await task_broker.add_task({
            'name':     'Triggering an update in TVH to fetch the latest XMLTV',
            'function': run_tvh_epg_grabbers,
            'args':     [config],
        }, priority=31)


async def add_channels_from_groups(config, groups):
    """
    Add channels from specified groups to the channel list
    """
    added_channel_count = 0
    
    for group_info in groups:
        playlist_id = group_info.get('playlist_id')
        group_name = group_info.get('group_name')
        
        if not playlist_id or not group_name:
            continue
        
        # Get all streams from this group
        async with Session() as session:
            result = await session.execute(
                select(PlaylistStreams)
                .where(PlaylistStreams.playlist_id == playlist_id)
                .where(PlaylistStreams.group_title == group_name)
            )
            playlist_streams = result.scalars().all()
            
            logger.info(f"Found {len(playlist_streams)} streams in group '{group_name}' to add")
            
            for stream in playlist_streams:
                try:
                    channel_data = {
                        'playlist_id': playlist_id,
                        'playlist_name': group_info.get('playlist_name', ''),
                        'stream_id': stream.id,
                        'stream_name': stream.name,
                        'tags': [group_name]  # Add group name as tag
                    }
                    
                    # Process channel right away
                    await add_bulk_channels(config, [channel_data])
                    added_channel_count += 1
                except Exception as e:
                    logger.error(f"Error adding channel '{stream.name}' from group '{group_name}': {str(e)}")
    
    logger.info(f"Successfully added {added_channel_count} channels from groups")
    
    # Ensure a gets properly updated after adding channels
    await queue_background_channel_update_tasks(config)
    
    return added_channel_count
