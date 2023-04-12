#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from backend import db
from backend.models import Channel, ChannelTag, Epg, ChannelSource, Playlist
from backend.playlists import read_stream_data_from_playlist


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


def add_new_channel(config, data):
    channel = Channel(
        enabled=data.get('enabled'),
        name=data.get('name'),
        logo_url=data.get('logo_url'),
        number=data.get('number'),
    )
    # Add tags
    for tag_name in data.get('tags', []):
        channel_tag = db.session.query(ChannelTag).filter(ChannelTag.name == tag_name).one_or_none()
        if not channel_tag:
            channel_tag = ChannelTag(name=tag_name)
            db.session.add(channel_tag)
        channel.tags.append(channel_tag)

    # Programme Guide
    guide_info = data.get('guide', {})
    if guide_info:
        channel_guide_source = db.session.query(Epg).filter(Epg.id == guide_info['epg_id']).one()
        channel.guide_id = channel_guide_source.id
        channel.guide_name = guide_info['epg_name']
        channel.guide_channel_id = guide_info['channel_id']

    # Sources
    new_sources = []
    for source_info in data.get('sources', []):
        playlist_info = db.session.query(Playlist).filter(Playlist.id == source_info['playlist_id']).one()
        streams = read_stream_data_from_playlist(config, playlist_info.id)
        stream_data = streams.get(source_info['stream_name'])
        channel_source = ChannelSource(
            playlist_id=playlist_info.id,
            playlist_stream_name=source_info['stream_name'],
            playlist_stream_url=stream_data['url'],
        )
        new_sources.append(channel_source)
    channel.sources.clear()
    channel.sources = new_sources

    # Add new row and commit
    db.session.add(channel)
    db.session.commit()


def update_channel(config, channel_id, data, commit=True):
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
    channel.tags.clear()
    channel.tags = new_tags

    # Programme Guide
    guide_info = data.get('guide', {})
    if guide_info:
        channel_guide_source = db.session.query(Epg).filter(Epg.id == guide_info['epg_id']).one()
        channel.guide_id = channel_guide_source.id
        channel.guide_name = guide_info['epg_name']
        channel.guide_channel_id = guide_info['channel_id']

    # Sources
    new_sources = []
    for source_info in data.get('sources', []):
        channel_source = db.session.query(ChannelSource) \
            .filter(and_(ChannelSource.channel_id == channel.id,
                         ChannelSource.playlist_id == source_info['playlist_id'],
                         ChannelSource.playlist_stream_name == source_info['stream_name']
                         )) \
            .one_or_none()
        if not channel_source:
            playlist_info = db.session.query(Playlist).filter(Playlist.id == source_info['playlist_id']).one()
            streams = read_stream_data_from_playlist(config, playlist_info.id)
            stream_data = streams.get(source_info['stream_name'])
            channel_source = ChannelSource(
                channel_id=channel.id,
                playlist_id=playlist_info.id,
                playlist_stream_name=source_info['stream_name'],
                playlist_stream_url=stream_data['url'],
            )
            db.session.add(channel_source)
        new_sources.append(channel_source)
    channel.sources.clear()
    channel.sources = new_sources

    # Commit
    if commit:
        db.session.commit()
