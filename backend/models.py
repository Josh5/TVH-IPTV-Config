#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from backend import db


class Epg(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    enabled = db.Column(db.Boolean, nullable=False, unique=False)
    name = db.Column(db.String(500), index=True, unique=False)
    url = db.Column(db.String(500), index=True, unique=False)

    # Backref to all associated linked channels
    channels = db.relationship('Channel', backref='guide', lazy=True)


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    enabled = db.Column(db.Boolean, nullable=False, unique=False)
    connections = db.Column(db.Integer, nullable=False, unique=False)
    name = db.Column(db.String(500), index=True, unique=False)
    tvh_uuid = db.Column(db.String(64), index=True, unique=True)
    url = db.Column(db.String(500), index=True, unique=False)

    # Backref to all associated linked streams
    channel_streams = db.relationship('ChannelStream', backref='playlist', lazy=True)

    def __repr__(self):
        return '<Playlist {}>'.format(self.id)


class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    enabled = db.Column(db.Boolean, nullable=False, unique=False)
    name = db.Column(db.String(500), index=True, unique=False)
    logo_url = db.Column(db.String(500), index=True, unique=False)
    number = db.Column(db.Integer, index=True, unique=True)

    # Link with a guide
    guide_id = db.Column(db.Integer, db.ForeignKey('epg.id'), nullable=True)
    guide_channel_id = db.Column(db.String(64), index=False, unique=True)

    # Backref to all associated linked streams
    streams = db.relationship('ChannelStream', backref='channel', lazy=True)

    def __repr__(self):
        return '<Channel {}>'.format(self.id)


class ChannelStream(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Link with channel
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)

    # Link with a playlist
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    playlist_stream_name = db.Column(db.String(500), index=True, unique=False)
    playlist_stream_url = db.Column(db.String(500), index=True, unique=False)
    priority = db.Column(db.String(500), index=True, unique=False)
    tvh_uuid = db.Column(db.String(500), index=True, unique=False)

    def __repr__(self):
        return '<ChannelStream {}>'.format(self.id)
