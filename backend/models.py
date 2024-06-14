#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Table, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

from backend import config

metadata = MetaData()
Base = declarative_base(metadata=metadata)

engine = create_async_engine(config.sqlalchemy_database_async_uri, echo=True)
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Use of 'db' in this project is now deprecated and will be removed in a future release. Use Session instead.
db = SQLAlchemy()


class Epg(Base):
    __tablename__ = "epgs"
    id = Column(Integer, primary_key=True)

    enabled = Column(Boolean, nullable=False, unique=False)
    name = Column(String(500), index=True, unique=False)
    url = Column(String(500), index=True, unique=False)

    # Backref to all associated linked channels
    epg_channels = relationship('EpgChannels', backref='guide', lazy=True, cascade="all, delete-orphan")
    channels = relationship('Channel', backref='guide', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return '<Epg {}>'.format(self.id)


class EpgChannels(Base):
    __tablename__ = "epg_channels"
    id = Column(Integer, primary_key=True)

    channel_id = Column(String(256), index=True, unique=False)
    name = Column(String(500), index=True, unique=False)
    icon_url = Column(String(500), index=False, unique=False)

    # Link with an epg
    epg_id = Column(Integer, ForeignKey('epgs.id'), nullable=False)

    # Backref to all associated linked channels
    epg_channel_programmes = relationship('EpgChannelProgrammes', backref='channel', lazy=True,
                                          cascade="all, delete-orphan")

    def __repr__(self):
        return '<EpgChannels {}>'.format(self.id)


class EpgChannelProgrammes(Base):
    """
        <programme start="20230423183001 +0100"0 stop="20230423190001 +100" start_timestamp="1682271001" stop_timestamp="1682272801" channel="some_channel_id" >
            <title>Programme Title</title>
            <desc>Programme description.</desc>
        </programme>
    """
    __tablename__ = "epg_channel_programmes"
    id = Column(Integer, primary_key=True)

    channel_id = Column(String(256), index=True, unique=False)
    title = Column(String(500), index=True, unique=False)
    sub_title = Column(String(500), index=False, unique=False)
    desc = Column(String(500), index=False, unique=False)
    series_desc = Column(String(500), index=False, unique=False)
    country = Column(String(500), index=False, unique=False)
    icon_url = Column(String(500), index=False, unique=False)
    start = Column(String(256), index=False, unique=False)
    stop = Column(String(256), index=False, unique=False)
    start_timestamp = Column(String(256), index=False, unique=False)
    stop_timestamp = Column(String(256), index=False, unique=False)
    categories = Column(String(256), index=True, unique=False)

    # Link with an epg channel
    epg_channel_id = Column(Integer, ForeignKey('epg_channels.id'), nullable=False)

    def __repr__(self):
        return '<EpgChannelProgrammes {}>'.format(self.id)


class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True)

    enabled = Column(Boolean, nullable=False, unique=False)
    connections = Column(Integer, nullable=False, unique=False)
    name = Column(String(500), index=True, unique=False)
    tvh_uuid = Column(String(64), index=True, unique=True)
    url = Column(String(500), index=True, unique=False)
    use_hls_proxy = Column(Boolean, nullable=False, unique=False)

    # Backref to all associated linked sources
    channel_sources = relationship('ChannelSource', backref='playlist', lazy=True, cascade="all, delete-orphan")
    playlist_streams = relationship('PlaylistStreams', backref='playlist', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return '<Playlist {}>'.format(self.id)


class PlaylistStreams(Base):
    __tablename__ = "playlist_streams"
    id = Column(Integer, primary_key=True)

    name = Column(String(500), index=True, unique=False)
    url = Column(String(500), index=True, unique=False)
    channel_id = Column(String(500), index=True, unique=False)
    group_title = Column(String(500), index=True, unique=False)
    tvg_chno = Column(Integer, index=False, unique=False)
    tvg_id = Column(String(500), index=True, unique=False)
    tvg_logo = Column(String(500), index=False, unique=False)

    # Link with a playlist
    playlist_id = Column(Integer, ForeignKey('playlists.id'), nullable=False)

    def __repr__(self):
        return '<PlaylistStreams {}>'.format(self.id)


channels_tags_association_table = Table(
    'channels_tags_group',
    Base.metadata,
    Column('channel_id', Integer, ForeignKey('channels.id')),
    Column('tag_id', Integer, ForeignKey('channel_tags.id'))
)


class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)

    enabled = Column(Boolean, nullable=False, unique=False)
    name = Column(String(500), index=True, unique=False)
    logo_url = Column(String(500), index=False, unique=False)
    logo_base64 = Column(String(500), index=False, unique=False)
    number = Column(Integer, index=True, unique=False)
    tvh_uuid = Column(String(500), index=True, unique=False)

    # Link with a guide
    guide_id = Column(Integer, ForeignKey('epgs.id'))
    guide_name = Column(String(256), index=False, unique=False)
    guide_channel_id = Column(String(64), index=False, unique=False)

    # Backref to all associated linked sources
    sources = relationship('ChannelSource', backref='channel', lazy=True, cascade="all, delete-orphan")

    # Specify many-to-many relationships
    tags = relationship("ChannelTag", secondary=channels_tags_association_table)

    def __repr__(self):
        return '<Channel {}>'.format(self.id)


class ChannelTag(Base):
    __tablename__ = "channel_tags"
    id = Column(Integer, primary_key=True)

    name = Column(String(64), index=False, unique=True)

    def __repr__(self):
        return '<ChannelTag {}>'.format(self.id)


class ChannelSource(Base):
    __tablename__ = "channel_sources"
    id = Column(Integer, primary_key=True)

    # Link with channel
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)

    # Link with a playlist
    playlist_id = Column(Integer, ForeignKey('playlists.id'), nullable=False)
    playlist_stream_name = Column(String(500), index=True, unique=False)
    playlist_stream_url = Column(String(500), index=True, unique=False)
    priority = Column(String(500), index=True, unique=False)
    tvh_uuid = Column(String(500), index=True, unique=False)

    def __repr__(self):
        return '<ChannelSource {}>'.format(self.id)
