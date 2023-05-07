#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from backend import db
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Epg(db.Model):
    __tablename__ = "epgs"
    id = db.Column(db.Integer, primary_key=True)

    enabled = db.Column(db.Boolean, nullable=False, unique=False)
    name = db.Column(db.String(500), index=True, unique=False)
    url = db.Column(db.String(500), index=True, unique=False)

    # Backref to all associated linked channels
    epg_channels = db.relationship('EpgChannels', backref='guide', lazy=True, cascade="all, delete-orphan")
    channels = db.relationship('Channel', backref='guide', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return '<Epg {}>'.format(self.id)


class EpgChannels(db.Model):
    __tablename__ = "epg_channels"
    id = db.Column(db.Integer, primary_key=True)

    channel_id = db.Column(db.String(256), index=True, unique=False)
    name = db.Column(db.String(500), index=True, unique=False)
    icon_url = db.Column(db.String(500), index=False, unique=False)

    # Link with an epg
    epg_id = db.Column(db.Integer, db.ForeignKey('epgs.id'), nullable=False)

    # Backref to all associated linked channels
    epg_channel_programmes = db.relationship('EpgChannelProgrammes', backref='channel', lazy=True,
                                             cascade="all, delete-orphan")

    def __repr__(self):
        return '<EpgChannels {}>'.format(self.id)


class EpgChannelProgrammes(db.Model):
    """
        <programme start="20230423183001 +0100"0 stop="20230423190001 +100" start_timestamp="1682271001" stop_timestamp="1682272801" channel="some_channel_id" >
            <title>Programme Title</title>
            <desc>Programme description.</desc>
        </programme>
    """
    __tablename__ = "epg_channel_programmes"
    id = db.Column(db.Integer, primary_key=True)

    channel_id = db.Column(db.String(256), index=True, unique=False)
    title = db.Column(db.String(500), index=True, unique=False)
    desc = db.Column(db.String(500), index=False, unique=False)
    start = db.Column(db.String(256), index=False, unique=False)
    stop = db.Column(db.String(256), index=False, unique=False)
    start_timestamp = db.Column(db.String(256), index=False, unique=False)
    stop_timestamp = db.Column(db.String(256), index=False, unique=False)
    categories = db.Column(db.String(256), index=True, unique=False)

    # Link with an epg channel
    epg_channel_id = db.Column(db.Integer, db.ForeignKey('epg_channels.id'), nullable=False)

    def __repr__(self):
        return '<EpgChannelProgrammes {}>'.format(self.id)


class Playlist(db.Model):
    __tablename__ = "playlists"
    id = db.Column(db.Integer, primary_key=True)

    enabled = db.Column(db.Boolean, nullable=False, unique=False)
    connections = db.Column(db.Integer, nullable=False, unique=False)
    name = db.Column(db.String(500), index=True, unique=False)
    tvh_uuid = db.Column(db.String(64), index=True, unique=True)
    url = db.Column(db.String(500), index=True, unique=False)

    # Backref to all associated linked sources
    channel_sources = db.relationship('ChannelSource', backref='playlist', lazy=True, cascade="all, delete-orphan")
    playlist_streams = db.relationship('PlaylistStreams', backref='playlist', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return '<Playlist {}>'.format(self.id)


class PlaylistStreams(db.Model):
    __tablename__ = "playlist_streams"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(500), index=True, unique=False)
    url = db.Column(db.String(500), index=True, unique=False)
    channel_id = db.Column(db.String(500), index=True, unique=False)
    group_title = db.Column(db.String(500), index=True, unique=False)
    tvg_chno = db.Column(db.Integer, index=False, unique=False)
    tvg_id = db.Column(db.String(500), index=True, unique=False)
    tvg_logo = db.Column(db.String(500), index=False, unique=False)

    # Link with a playlist
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False)

    def __repr__(self):
        return '<PlaylistStreams {}>'.format(self.id)


channels_tags_association_table = db.Table(
    'channels_tags_group',
    db.Column('channel_id', db.Integer, db.ForeignKey('channels.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('channel_tags.id'))
)


class Channel(db.Model):
    __tablename__ = "channels"
    id = db.Column(db.Integer, primary_key=True)

    enabled = db.Column(db.Boolean, nullable=False, unique=False)
    name = db.Column(db.String(500), index=True, unique=False)
    logo_url = db.Column(db.String(500), index=True, unique=False)
    number = db.Column(db.Integer, index=True, unique=False)
    tvh_uuid = db.Column(db.String(500), index=True, unique=False)

    # Link with a guide
    guide_id = db.Column(db.Integer, db.ForeignKey('epgs.id'))
    guide_name = db.Column(db.String(256), index=False, unique=False)
    guide_channel_id = db.Column(db.String(64), index=False, unique=False)

    # Backref to all associated linked sources
    sources = db.relationship('ChannelSource', backref='channel', lazy=True, cascade="all, delete-orphan")

    # Specify many-to-many relationships
    tags = relationship("ChannelTag", secondary=channels_tags_association_table)

    def __repr__(self):
        return '<Channel {}>'.format(self.id)


class ChannelTag(db.Model):
    __tablename__ = "channel_tags"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(64), index=False, unique=True)

    def __repr__(self):
        return '<ChannelTag {}>'.format(self.id)


class ChannelSource(db.Model):
    __tablename__ = "channel_sources"
    id = db.Column(db.Integer, primary_key=True)

    # Link with channel
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id'), nullable=False)

    # Link with a playlist
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False)
    playlist_stream_name = db.Column(db.String(500), index=True, unique=False)
    playlist_stream_url = db.Column(db.String(500), index=True, unique=False)
    priority = db.Column(db.String(500), index=True, unique=False)
    tvh_uuid = db.Column(db.String(500), index=True, unique=False)

    def __repr__(self):
        return '<ChannelSource {}>'.format(self.id)
