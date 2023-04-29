#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask_apscheduler import APScheduler

scheduler = APScheduler()


def configure_tvh_with_defaults(app):
    print("Configuring TVH")
    config = app.config['APP_CONFIG']
    from backend.tvheadend.tvh_requests import configure_tvh
    configure_tvh(config)


def update_playlists(app):
    print("Updating Playlists")
    config = app.config['APP_CONFIG']
    from backend.playlists import import_playlist_data_for_all_playlists
    import_playlist_data_for_all_playlists(config)


def update_epgs(app):
    print("Updating EPGs")
    config = app.config['APP_CONFIG']
    from backend.epgs import import_epg_data_for_all_epgs
    import_epg_data_for_all_epgs(config)


def rebuild_custom_epg(app):
    print("Rebuilding custom EPG")
    config = app.config['APP_CONFIG']
    from backend.epgs import build_custom_epg, run_tvh_epg_grabbers
    build_custom_epg(config)
    run_tvh_epg_grabbers(config)


def update_tvh_networks(app):
    print("Updating channels in TVH")
    config = app.config['APP_CONFIG']
    from backend.playlists import publish_playlist_networks
    publish_playlist_networks(config)


def update_tvh_channels(app):
    print("Updating channels in TVH")
    config = app.config['APP_CONFIG']
    from backend.channels import publish_bulk_channels_to_tvh
    publish_bulk_channels_to_tvh(config)


def update_tvh_muxes(app):
    print("Updating muxes in TVH")
    config = app.config['APP_CONFIG']
    from backend.channels import publish_channel_muxes
    publish_channel_muxes(config)


def map_new_tvh_services(app):
    print("Mapping new services in TVH")
    config = app.config['APP_CONFIG']
    # Map any new services
    from backend.channels import map_all_services, cleanup_old_channels
    map_all_services(config)
    # Clear out old channels
    cleanup_old_channels(config)
