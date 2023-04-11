#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from backend import db
from backend.models import Epg


def read_config_all_epgs():
    return_list = []
    for result in db.session.query(Epg).all():
        return_list.append({
            'id':      result.id,
            'enabled': result.enabled,
            'name':    result.name,
            'url':     result.url,
        })
    return return_list


def read_config_one_epg(epg_id):
    return_item = {}
    result = db.session.query(Epg).filter(Epg.id == epg_id).one()
    if result:
        return_item = {
            'id':      result.id,
            'enabled': result.enabled,
            'name':    result.name,
            'url':     result.url,
        }
    return return_item


def add_new_epg(data):
    epg = Epg(
        enabled=data.get('enabled'),
        name=data.get('name'),
        url=data.get('url'),
    )
    # This is a new entry. Add it to the session before commit
    db.session.add(epg)
    db.session.commit()


def update_epg(epg_id, data):
    epg = db.session.query(Epg).where(Epg.id == epg_id).one()
    epg.enabled = data.get('enabled')
    epg.name = data.get('name')
    epg.url = data.get('url')
    db.session.commit()


def delete_epg(config, epg_id):
    epg = db.session.query(Epg).where(Epg.id == epg_id).one()
    db.session.delete(epg)
    db.session.commit()
    # Remove cached copy of epg
    cache_files = [
        os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.xml"),
        os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.yml"),
    ]
    for f in cache_files:
        if os.path.isfile(f):
            os.remove(f)


def import_epg_data(config, epg_id):
    epg = read_config_one_epg(epg_id)
    # Download a new local copy of the EPG
    from lib.epg import download_xmltv_epg
    xmltv_file = os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.xml")
    download_xmltv_epg(epg['url'], xmltv_file)
    # Parse the XMLTV file for channels and cache them
    from lib.epg import parse_xmltv_for_channels
    parse_xmltv_for_channels(config, epg_id)
