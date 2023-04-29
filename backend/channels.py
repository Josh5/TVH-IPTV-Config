#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import re

from sqlalchemy.orm import joinedload
from sqlalchemy import and_, func
from backend import db
from backend.models import Channel, ChannelTag, Epg, ChannelSource, Playlist, EpgChannels, PlaylistStreams, \
    channels_tags_association_table
from backend.playlists import fetch_playlist_streams
from backend.tvheadend.tvh_requests import get_tvh
from lib.playlist import generate_iptv_url


def read_config_all_channels():
    return_list = []
    for result in db.session.query(Channel) \
            .options(joinedload(Channel.tags), joinedload(Channel.sources).subqueryload(ChannelSource.playlist)) \
            .all():
        tags = []
        for tag in result.tags:
            tags.append(tag.name)
        sources = []
        for source in result.sources:
            sources.append({
                'playlist_id':   source.playlist_id,
                'playlist_name': source.playlist.name,
                'priority':      1,
                'stream_name':   source.playlist_stream_name,
            })
        return_list.append({
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
        })
    return return_list


def read_config_one_channel(channel_id):
    return_item = {}
    result = db.session.query(Channel) \
        .options(joinedload(Channel.tags), joinedload(Channel.sources).subqueryload(ChannelSource.playlist)) \
        .filter(Channel.id == channel_id) \
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
                'priority':      1,
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


def add_new_channel(config, data, commit=True):
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

    # Publish changes to TVH
    channel_uuid = publish_channel_to_tvh(config, channel)
    # Save network UUID against playlist in settings
    channel.tvh_uuid = channel_uuid

    # Add new row and commit
    db.session.add(channel)
    if commit:
        db.session.commit()


def update_channel(config, channel_id, data):
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
    for source_info in data.get('sources', []):
        channel_source = db.session.query(ChannelSource) \
            .filter(and_(ChannelSource.channel_id == channel.id,
                         ChannelSource.playlist_id == source_info['playlist_id'],
                         ChannelSource.playlist_stream_name == source_info['stream_name']
                         )) \
            .one_or_none()
        if channel_source:
            new_source_ids.append(channel_source.id)
        if not channel_source:
            playlist_info = db.session.query(Playlist).filter(Playlist.id == source_info['playlist_id']).one()
            playlist_streams = fetch_playlist_streams(playlist_info.id)
            playlist_stream = playlist_streams.get(source_info['stream_name'])
            channel_source = ChannelSource(
                playlist_id=playlist_info.id,
                playlist_stream_name=source_info['stream_name'],
                playlist_stream_url=playlist_stream['url'],
            )
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

    # Publish changes to TVH
    channel_uuid = publish_channel_to_tvh(config, channel)
    # Save network UUID against playlist in settings
    channel.tvh_uuid = channel_uuid

    # Commit
    db.session.commit()


def add_bulk_channels(config, data):
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
        add_new_channel(config, new_channel_data, commit=False)
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
    # db.session.delete(channel)
    db.session.commit()


def publish_channel_to_tvh(config, channel):
    print(f"Publishing channel to TVH - {channel.name}")
    tvh = get_tvh(config)
    # Check if channel exists with a matching UUID and create it if not
    channel_uuid = channel.tvh_uuid
    existing_channels = tvh.list_all_channels()
    if channel_uuid:
        found = False
        for tvh_channel in existing_channels:
            if tvh_channel.get('uuid') == channel_uuid:
                found = True
        if not found:
            channel_uuid = None
    if not channel_uuid:
        # No channel exists, create one
        channel_uuid = tvh.create_channel(channel.name, channel.number, channel.logo_url)
    channel_conf = {
        'enabled': True,
        'uuid':    channel_uuid,
        "name":    channel.name,
        "number":  channel.number,
        "icon":    channel.logo_url
    }
    # TODO: Add channel tags
    # channel_conf["tags"] = result.name
    tvh.idnode_save(channel_conf)
    return channel_uuid


def publish_bulk_channels_to_tvh(config):
    tvh = get_tvh(config)
    # Loop over configured channels
    managed_uuids = []
    results = db.session.query(Channel) \
        .options(joinedload(Channel.tags), joinedload(Channel.sources).subqueryload(ChannelSource.playlist)) \
        .order_by(Channel.number.asc()) \
        .all()
    # Fetch existing channels
    print("Publishing all channels to TVH")
    for result in results:
        channel_uuid = publish_channel_to_tvh(config, result)
        # Save network UUID against playlist in settings
        result.tvh_uuid = channel_uuid
        db.session.commit()
        # Append to list of current network UUIDs
        managed_uuids.append(channel_uuid)

    #  Remove any channels that are not managed.
    print("Running cleanup task on current TVH channels")
    for existing_channel in tvh.list_all_channels():
        if existing_channel.get('uuid') not in managed_uuids:
            print(f"    - Removing channel UUID - {existing_channel.get('uuid')}")
            tvh.delete_channel(existing_channel.get('uuid'))


def publish_channel_muxes(config):
    tvh = get_tvh(config)
    # TODO: Add support for settings priority
    # Loop over configured channels
    managed_uuids = []
    results = db.session.query(Channel) \
        .options(joinedload(Channel.tags), joinedload(Channel.sources).subqueryload(ChannelSource.playlist)) \
        .order_by(Channel.number.asc()) \
        .all()
    existing_muxes = tvh.list_all_muxes()
    for result in results:
        if result.enabled:
            print(f"Configuring MUX for channel '{result.name}'")
            # Create/update a network in TVH for each enabled playlist line
            for source in result.sources:
                # Write playlist to TVH Network
                net_uuid = source.playlist.tvh_uuid
                if not net_uuid:
                    # Show error
                    print("Playlist is not configured on TVH")
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
                    print(f"    - Creating new MUX for channel '{result.name}'")
                    # No mux exists, create one
                    mux_uuid = tvh.network_mux_create(net_uuid)
                    print(mux_uuid)
                    run_mux_scan = True
                else:
                    print(f"    - Updating existing MUX for channel '{result.name}' - {mux_uuid}")
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
                    'iptv_epgid':     channel_id
                }
                if run_mux_scan:
                    mux_conf['scan_state'] = 1
                tvh.idnode_save(mux_conf)
                # Save network UUID against playlist in settings
                source.tvh_uuid = mux_uuid
                db.session.commit()
                # Append to list of current network UUIDs
                managed_uuids.append(mux_uuid)

    #  Remove any muxes that are not managed.
    print("Running cleanup task on current TVH muxes")
    for existing_mux in tvh.list_all_muxes():
        if existing_mux.get('uuid') not in managed_uuids:
            print(f"    - Removing mux UUID - {existing_mux.get('uuid')}")
            tvh.delete_mux(existing_mux.get('uuid'))


def delete_channel_muxes(config, mux_uuid):
    tvh = get_tvh(config)
    tvh.delete_mux(mux_uuid)


def map_all_services(config):
    print("Executing TVH Map all service")
    tvh = get_tvh(config)
    tvh.map_all_services_to_channels()


def cleanup_old_channels(config):
    print("Cleaning up old TVH channels")
    tvh = get_tvh(config)
    for channel in tvh.list_all_channels():
        if channel.get('name') == "{name-not-set}":
            print(f"    - Removing channel UUID - {channel.get('uuid')}")
            tvh.delete_channel(channel.get('uuid'))
