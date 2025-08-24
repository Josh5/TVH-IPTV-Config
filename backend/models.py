#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Table, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

from backend import config

metadata = MetaData()
Base = declarative_base(metadata=metadata)

engine = create_async_engine(config.sqlalchemy_database_async_uri, echo=config.enable_sqlalchemy_debugging)
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

    # Extended XMLTV fields
    # Alle folgenden Felder sind optional (nullable=True explizit gesetzt zur Klarheit)
    summary = Column(String(500), nullable=True, index=False, unique=False)           # <summary>
    keywords = Column(String(500), nullable=True, index=False, unique=False)          # multiple <keyword> (Delimiter)
    actors = Column(String(500), nullable=True, index=False, unique=False)            # multiple <actor>
    directors = Column(String(500), nullable=True, index=False, unique=False)         # multiple <director>
    guests = Column(String(500), nullable=True, index=False, unique=False)            # multiple <guest>
    presenters = Column(String(500), nullable=True, index=False, unique=False)        # multiple <presenter>
    writers = Column(String(500), nullable=True, index=False, unique=False)           # multiple <writer>
    video_colour = Column(String(32), nullable=True, index=False, unique=False)       # <video><colour>
    video_aspect = Column(String(32), nullable=True, index=False, unique=False)       # <video><aspect>
    video_quality = Column(String(16), nullable=True, index=False, unique=False)      # <video><quality>
    subtitles_type = Column(String(32), nullable=True, index=False, unique=False)     # <subtitles type="">
    audio_described = Column(Boolean, nullable=True, unique=False)                    # <audio-described />
    previously_shown = Column(String(32), nullable=True, index=False, unique=False)   # <previously-shown start="">
    premiere = Column(Boolean, nullable=True, unique=False)                           # <premiere />
    is_new = Column(Boolean, nullable=True, unique=False)                             # <new />
    episode_num_onscreen = Column(String(128), nullable=True, index=False, unique=False)   # episode-num onscreen
    episode_num_xmltv_ns = Column(String(128), nullable=True, index=False, unique=False)   # episode-num xmltv_ns
    episode_num_dd_progid = Column(String(128), nullable=True, index=False, unique=False)  # episode-num dd_progid
    star_rating = Column(String(32), nullable=True, index=False, unique=False)        # <star-rating><value>
    date = Column(String(8), nullable=True, index=False, unique=False)                # <date>YYYY
    rating_system = Column(String(64), nullable=True, index=False, unique=False)      # <rating system="Name">
    rating_value = Column(String(64), nullable=True, index=False, unique=False)       # <rating><value>

    # Link with an epg channel
    epg_channel_id = Column(Integer, ForeignKey('epg_channels.id'), nullable=False)

    def __repr__(self):
        return '<EpgChannelProgrammes {}>'.format(self.id)

    # -------- Helper für Listenfelder --------
    _DELIM = '\u001f'  # Unit Separator als Delimiter, geringes Kollisionsrisiko

    def _split(self, value):
        return [] if not value else value.split(self._DELIM)

    def _join(self, items):
        if not items:
            return None
        return self._DELIM.join([i for i in items if i])

    # Keywords
    @property
    def keyword_list(self):
        return self._split(self.keywords)

    @keyword_list.setter
    def keyword_list(self, items):
        self.keywords = self._join(items)

    # Actors
    @property
    def actor_list(self):
        return self._split(self.actors)

    @actor_list.setter
    def actor_list(self, items):
        self.actors = self._join(items)

    # Directors
    @property
    def director_list(self):
        return self._split(self.directors)

    @director_list.setter
    def director_list(self, items):
        self.directors = self._join(items)

    # Guests
    @property
    def guest_list(self):
        return self._split(self.guests)

    @guest_list.setter
    def guest_list(self, items):
        self.guests = self._join(items)

    # Presenters
    @property
    def presenter_list(self):
        return self._split(self.presenters)

    @presenter_list.setter
    def presenter_list(self, items):
        self.presenters = self._join(items)

    # Writers
    @property
    def writer_list(self):
        return self._split(self.writers)

    @writer_list.setter
    def writer_list(self, items):
        self.writers = self._join(items)

    def as_xmltv_dict(self):
        """Gibt nur gesetzte (nicht-leere) Felder zurück -> erleichtert XML-Export."""
        fields = {}
        simple_map = {
            'summary': self.summary,
            'desc': self.desc,
            'sub_title': self.sub_title,
            'series_desc': self.series_desc,
            'country': self.country,
            'video_colour': self.video_colour,
            'video_aspect': self.video_aspect,
            'video_quality': self.video_quality,
            'subtitles_type': self.subtitles_type,
            'previously_shown': self.previously_shown,
            'star_rating': self.star_rating,
            'date': self.date,
            'rating_system': self.rating_system,
            'rating_value': self.rating_value,
            'episode_num_onscreen': self.episode_num_onscreen,
            'episode_num_xmltv_ns': self.episode_num_xmltv_ns,
            'episode_num_dd_progid': self.episode_num_dd_progid,
        }
        for k, v in simple_map.items():
            if v not in (None, '', []):
                fields[k] = v
        # Boolean Flags
        if self.audio_described:
            fields['audio_described'] = True
        if self.premiere:
            fields['premiere'] = True
        if self.is_new:
            fields['is_new'] = True
        # Listen
        if self.keyword_list:
            fields['keywords'] = self.keyword_list
        if self.actor_list:
            fields['actors'] = self.actor_list
        if self.director_list:
            fields['directors'] = self.director_list
        if self.guest_list:
            fields['guests'] = self.guest_list
        if self.presenter_list:
            fields['presenters'] = self.presenter_list
        if self.writer_list:
            fields['writers'] = self.writer_list
        return fields


class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True)

    enabled = Column(Boolean, nullable=False, unique=False)
    connections = Column(Integer, nullable=False, unique=False)
    name = Column(String(500), index=True, unique=False)
    tvh_uuid = Column(String(64), index=True, unique=True)
    url = Column(String(500), index=True, unique=False)
    use_hls_proxy = Column(Boolean, nullable=False, unique=False)
    use_custom_hls_proxy = Column(Boolean, nullable=False, unique=False)
    hls_proxy_path = Column(String(256), unique=False)

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
