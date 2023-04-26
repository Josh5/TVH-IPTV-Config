#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os
import re
import time
import xml.etree.ElementTree as ET
from types import NoneType

from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from backend import db
from backend.models import Epg, Channel, EpgChannels, EpgChannelProgrammes
from backend.tvheadend.tvh_requests import get_tvh


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


def store_epg_channels(config, epg_id):
    xmltv_file = os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.xml")
    if not os.path.exists(xmltv_file):
        # TODO: Add error logging here
        print(f"No such file '{xmltv_file}'")
        return False
    # Open file
    input_file = ET.parse(xmltv_file)
    # Delete all existing playlist channels
    print(f"Clearing previous channels for EPG #{epg_id}")
    stmt = EpgChannels.__table__.delete().where(EpgChannels.epg_id == epg_id)
    db.session.execute(stmt)
    # Add an updated list of channels from the XML file to the DB
    print(f"Updating channels list for EPG #{epg_id} from path - '{xmltv_file}'")
    items = []
    channel_id_list = []
    for channel in input_file.iterfind('.//channel'):
        channel_id = channel.get('id')
        display_name = channel.find('display-name').text
        icon = ''
        icon_elem = channel.find('icon')
        if not isinstance(icon_elem, NoneType):
            icon = icon_elem.attrib.get('src', '')
        # print(f"Channel ID: '{channel_id}', Display Name: '{display_name}', Icon: {icon}")
        items.append(
            EpgChannels(
                epg_id=epg_id,
                channel_id=channel_id,
                name=display_name,
                icon_url=icon,
            )
        )
        channel_id_list.append(channel_id)
    # Save all new
    db.session.bulk_save_objects(items)
    # Commit all updates to channels
    db.session.commit()
    print(f"Successfully imported {len(channel_id_list)} channels from path - '{xmltv_file}'")
    # Return list of channels
    return channel_id_list


def store_epg_programmes(config, epg_id, channel_id_list):
    xmltv_file = os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.xml")
    if not os.path.exists(xmltv_file):
        # TODO: Add error logging here
        print(f"No such file '{xmltv_file}'")
        return False
    # Open file
    input_file = ET.parse(xmltv_file)
    # For each channel, create a list of programmes
    print(f"Fetching list of channels from EPG #{epg_id} from database")
    channel_ids = {}
    for channel_id in channel_id_list:
        epg_channel = db.session.query(EpgChannels) \
            .filter(and_(EpgChannels.channel_id == channel_id,
                         EpgChannels.epg_id == epg_id
                         )) \
            .first()
        channel_ids[channel_id] = epg_channel.id
    # Delete all existing playlist programmes
    print(f"Clearing previous programmes for EPG #{epg_id}")
    epg_channel_rows = (
        db.session.query(EpgChannels)
        .options(joinedload(EpgChannels.guide))
        .filter(EpgChannels.epg_id == epg_id)
        .all()
    )
    stmt = EpgChannelProgrammes.__table__.delete().where(
        EpgChannelProgrammes.epg_channel_id.in_([epg_channel.id for epg_channel in epg_channel_rows])
    )
    db.session.execute(stmt)
    # Add an updated list of programmes from the XML file to the DB
    print(f"Updating new programmes list for EPG #{epg_id} from path - '{xmltv_file}'")
    items = []
    for programme in input_file.iterfind(".//programme"):
        channel_id = programme.attrib.get('channel', None)
        if channel_id in channel_ids:
            epg_channel_id = channel_ids.get(channel_id)
            # Parse attributes first
            start = programme.attrib.get('start', None)
            stop = programme.attrib.get('stop', None)
            start_timestamp = programme.attrib.get('start_timestamp', None)
            stop_timestamp = programme.attrib.get('stop_timestamp', None)
            # Parse sub-elements
            title = programme.findtext("title", default=None)
            desc = programme.findtext("desc", default=None)
            # Create new line entry for the programmes table
            items.append(
                EpgChannelProgrammes(
                    epg_channel_id=epg_channel_id,
                    channel_id=channel_id,
                    title=title,
                    desc=desc,
                    start=start,
                    stop=stop,
                    start_timestamp=start_timestamp,
                    stop_timestamp=stop_timestamp,
                )
            )
    # Save all new
    db.session.bulk_save_objects(items)
    # Commit all updates to channel programmes
    db.session.commit()
    print(f"Successfully imported {len(items)} programmes from path - '{xmltv_file}'")


def import_epg_data(config, epg_id):
    epg = read_config_one_epg(epg_id)
    # Download a new local copy of the EPG
    print(f"Downloading updated XMLTV file for EPG #{epg_id} from url - '{epg['url']}'")
    start_time = time.time()
    from lib.epg import download_xmltv_epg
    xmltv_file = os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.xml")
    download_xmltv_epg(epg['url'], xmltv_file)
    execution_time = time.time() - start_time
    print(f"Updated XMLTV file for EPG #{epg_id} was downloaded in '{int(execution_time)}' seconds")
    # Read and save EPG data to DB
    print(f"Importing updated data for EPG #{epg_id}")
    start_time = time.time()
    channel_id_list = store_epg_channels(config, epg_id)
    store_epg_programmes(config, epg_id, channel_id_list)
    execution_time = time.time() - start_time
    print(f"Updated data for EPG #{epg_id} was imported in '{int(execution_time)}' seconds")


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
    print(f"Generating custom EPG for TVH based on configured channels.")
    start_time = time.time()
    # Create the root <tv> element of the output XMLTV file
    output_root = ET.Element('tv')
    # Set the attributes for the output root element
    output_root.set('generator-info-name', 'TVH-IPTV-Config')
    output_root.set('source-info-name', 'TVH-IPTV-Config - v0.1')
    # Read programmes from cached source EPG
    configured_channels = []
    all_channel_programmes_data = []
    # for key in settings.get('channels', {}):
    for result in db.session.query(Channel).order_by(Channel.number.asc()).all():
        if result.enabled:
            channel_id = f"{result.number}_{re.sub(r'[^a-zA-Z0-9]', '', result.name)}"
            # Populate a channels list
            configured_channels.append({
                'channel_id':   channel_id,
                'display_name': result.name,
                'logo_url':     result.logo_url,
            })
            programmes = db.session.query(EpgChannelProgrammes) \
                .options(joinedload(EpgChannelProgrammes.channel)) \
                .filter(and_(EpgChannelProgrammes.channel.has(epg_id=result.guide_id),
                             EpgChannelProgrammes.channel.has(channel_id=result.guide_channel_id)
                             )) \
                .order_by(EpgChannelProgrammes.channel_id.asc(), EpgChannelProgrammes.start.asc()) \
                .all()
            all_channel_programmes_data.append({
                'channel':    channel_id,
                'programmes': programmes
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
    for channel_programmes_data in all_channel_programmes_data:
        for epg_channel_programme in channel_programmes_data.get('programmes', []):
            # Create a <programme> element for the output file and copy the attributes from the input programme
            output_programme = ET.SubElement(output_root, 'programme')
            # Build programmes from DB data (manually create attributes etc.
            if epg_channel_programme.start:
                output_programme.set('start', epg_channel_programme.start)
            if epg_channel_programme.stop:
                output_programme.set('stop', epg_channel_programme.stop)
            if epg_channel_programme.start_timestamp:
                output_programme.set('start_timestamp', epg_channel_programme.start_timestamp)
            if epg_channel_programme.stop_timestamp:
                output_programme.set('stop_timestamp', epg_channel_programme.stop_timestamp)
            # Set the "channel" ident here
            output_programme.set('channel', str(channel_programmes_data.get('channel')))
            # Loop through all child elements of the input programme and copy them to the output programme
            for child in ['title', 'desc']:
                # Copy all other child elements to the output programme if they exist
                if getattr(epg_channel_programme, child):
                    output_child = ET.SubElement(output_programme, child)
                    output_child.text = getattr(epg_channel_programme, child)
    # Create an XML file and write the output root element to it
    output_tree = ET.ElementTree(output_root)
    ET.indent(output_tree, space="\t", level=0)
    custom_epg_file = os.path.join(config.config_path, "epg.xml")
    output_tree.write(custom_epg_file, encoding='UTF-8', xml_declaration=True)
    execution_time = time.time() - start_time
    print(f"The custom XMLTV EPG file for TVH was generated in '{int(execution_time)}' seconds")


def run_tvh_epg_grabbers(config):
    # Trigger a re-grab of the EPG in TVH
    tvh = get_tvh(config)
    tvh.run_internal_epg_grabber()
