#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import re
import xml.etree.ElementTree as ET
from sqlalchemy.orm import joinedload
from backend import db
from backend.models import Epg, Channel, EpgChannels
from backend.tvheadend.tvh_requests import get_tvh
from lib.config import read_yaml
from lib.epg import parse_xmltv_for_programmes_for_channel


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


def store_epg_channels(epg_id, epg_data):
    items = []
    for data in epg_data.get('channels', []):
        items.append(
            EpgChannels(
                epg_id=epg_id,
                channel_id=data['channel_id'],
                name=data['display_name'],
                icon_url=data['icon'],
            )
        )
    # Delete all existing playlist channels
    stmt = EpgChannels.__table__.delete().where(EpgChannels.epg_id == epg_id)
    db.session.execute(stmt)
    # Save all new
    db.session.bulk_save_objects(items)
    db.session.commit()


def import_epg_data(config, epg_id):
    epg = read_config_one_epg(epg_id)
    # Download a new local copy of the EPG
    from lib.epg import download_xmltv_epg
    xmltv_file = os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.xml")
    download_xmltv_epg(epg['url'], xmltv_file)
    # Parse the XMLTV file for channels and cache them
    from lib.epg import parse_xmltv_for_channels
    epg_data = parse_xmltv_for_channels(config, epg_id)
    store_epg_channels(epg_id, epg_data)


def import_epg_data_for_all_epgs(config):
    for epg in db.session.query(Epg).all():
        import_epg_data(config, epg.id)


def read_channels_from_all_epgs(config):
    epgs_channels = {}
    for result in db.session.query(Epg).options(joinedload(Epg.epg_channels)).all():
        epgs_channels[result.id] = []
        for epg_channel in result.epg_channels:
            epgs_channels[result.id].append({
                "channel_id":   epg_channel.channel_id,
                "display_name": epg_channel.name,
                "icon":         epg_channel.icon_url,
            })
    return epgs_channels


# --- Cache ---
# TODO: Migrate this data into the database to speed up requests


def build_custom_epg(config):
    # Create the root <tv> element of the output XMLTV file
    output_root = ET.Element('tv')

    # Set the attributes for the output root element
    output_root.set('generator-info-name', 'TVH-IPTV-Config')
    output_root.set('source-info-name', 'TVH-IPTV-Config - v0.1')

    # Read programmes from cached source EPG
    configured_channels = []
    discovered_programmes = []
    # for key in settings.get('channels', {}):
    for result in db.session.query(Channel).all():
        if result.enabled:
            channel_id = f"{result.number}_{re.sub(r'[^a-zA-Z0-9]', '', result.name)}"
            # Populate a channels list
            configured_channels.append({
                'channel_id':   channel_id,
                'display_name': result.name,
                'logo_url':     result.logo_url,
            })
            discovered_programmes.append({
                'channel':    channel_id,
                'programmes': parse_xmltv_for_programmes_for_channel(config, result.guide_id, result.guide_channel_id)
            })

    # Loop over all configured channels
    for channel_info in configured_channels:
        # Create a <channel> element for a TV channel
        channel = ET.SubElement(output_root, 'channel')
        channel.set('id', str(channel_info['channel_id']))
        # Add a <display-name> element to the <channel> element
        display_name = ET.SubElement(channel, 'display-name')
        display_name.text = channel_info['display_name']
        # Add a <icon> element to the <channel> element
        icon = ET.SubElement(channel, 'icon')
        icon.set('src', channel_info['logo_url'])

    # Loop through all <programme> elements returned
    for channel_programme_info in discovered_programmes:
        for programme in channel_programme_info.get('programmes', []):
            # Create a <programme> element for the output file and copy the attributes from the input programme
            output_programme = ET.SubElement(output_root, 'programme')
            output_programme.attrib = programme.attrib
            # Set the channel number here
            output_programme.set('channel', str(channel_programme_info['channel']))
            # Loop through all child elements of the input programme and copy them to the output programme
            for child in programme:
                # Skip the <channel> element, which is already set by the output_programme.attrib line
                if child.tag == 'channel':
                    continue
                # Copy all other child elements to the output programme
                output_child = ET.SubElement(output_programme, child.tag)
                output_child.text = child.text

    # Create an XML file and write the output root element to it
    output_tree = ET.ElementTree(output_root)
    ET.indent(output_tree, space="\t", level=0)
    custom_epg_file = os.path.join(config.config_path, "epg.xml")
    output_tree.write(custom_epg_file, encoding='UTF-8', xml_declaration=True)


def run_tvh_epg_grabbers(config):
    # Trigger a re-grab of the EPG in TVH
    tvh = get_tvh(config)
    tvh.run_internal_epg_grabber()
