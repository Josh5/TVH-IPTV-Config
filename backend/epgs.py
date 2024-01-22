#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import gzip
import json
import logging
import os
from mimetypes import guess_extension

import requests
import time
import xml.etree.ElementTree as ET
from types import NoneType

from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from backend import db
from backend.channels import read_base46_image_string
from backend.models import Epg, Channel, EpgChannels, EpgChannelProgrammes
from backend.tvheadend.tvh_requests import get_tvh

logger = logging.getLogger('werkzeug.epgs')


def generate_epg_channel_id(number, name):
    # return f"{number}_{re.sub(r'[^a-zA-Z0-9]', '', name)}"
    return str(number)


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


def download_xmltv_epg(url, output):
    logger.info("Downloading EPG from url - '%s'", url)
    if not os.path.exists(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))
    mozilla_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"}
    with requests.get(url, stream=True, allow_redirects=True, headers=mozilla_header) as r:
        r.raise_for_status()
        with open(output, 'wb') as f:
            for chunk in r.iter_content(chunk_size=128):
                f.write(chunk)
    try_unzip(output)


def try_unzip(output: str) -> None:
    try:
        with gzip.open(output, 'rb') as f:
            out = f.readlines()
        logger.info("Downloaded file iz gzipped. Unzipping")
        with open(output, 'wb') as f:
            f.writelines(out)
    except:
        pass


def store_epg_channels(config, epg_id):
    xmltv_file = os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.xml")
    if not os.path.exists(xmltv_file):
        # TODO: Add error logging here
        logger.info("No such file '%s'", xmltv_file)
        return False
    # Open file
    input_file = ET.parse(xmltv_file)
    # Delete all existing playlist channels
    logger.info("Clearing previous channels for EPG #%s", epg_id)
    stmt = EpgChannels.__table__.delete().where(EpgChannels.epg_id == epg_id)
    db.session.execute(stmt)
    # Add an updated list of channels from the XML file to the DB
    logger.info("Updating channels list for EPG #%s from path - '%s'", epg_id, xmltv_file)
    items = []
    channel_id_list = []
    for channel in input_file.iterfind('.//channel'):
        channel_id = channel.get('id')
        display_name = channel.find('display-name').text
        icon = ''
        icon_elem = channel.find('icon')
        if not isinstance(icon_elem, NoneType):
            icon = icon_elem.attrib.get('src', '')
        logger.debug("Channel ID: '%s', Display Name: '%s', Icon: %s", channel_id, display_name, icon)
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
    logger.info("Successfully imported %s channels from path - '%s'", len(channel_id_list), xmltv_file)
    # Return list of channels
    return channel_id_list


def store_epg_programmes(config, epg_id, channel_id_list):
    xmltv_file = os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.xml")
    if not os.path.exists(xmltv_file):
        # TODO: Add error logging here
        logger.info("No such file '%s'", xmltv_file)
        return False
    # Open file
    input_file = ET.parse(xmltv_file)
    # For each channel, create a list of programmes
    logger.info("Fetching list of channels from EPG #%s from database", epg_id)
    channel_ids = {}
    for channel_id in channel_id_list:
        epg_channel = db.session.query(EpgChannels) \
            .filter(and_(EpgChannels.channel_id == channel_id,
                         EpgChannels.epg_id == epg_id
                         )) \
            .first()
        channel_ids[channel_id] = epg_channel.id
    # Delete all existing playlist programmes
    logger.info("Clearing previous programmes for EPG #%s", epg_id)
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
    logger.info("Updating new programmes list for EPG #%s from path - '%s'", epg_id, xmltv_file)
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
            categories = []
            for category in programme.findall("category"):
                categories.append(category.text)
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
                    categories=json.dumps(categories)
                )
            )
    # Save all new
    db.session.bulk_save_objects(items)
    # Commit all updates to channel programmes
    db.session.commit()
    logger.info("Successfully imported %s programmes from path - '%s'", len(items), xmltv_file)


def import_epg_data(config, epg_id):
    epg = read_config_one_epg(epg_id)
    # Download a new local copy of the EPG
    logger.info("Downloading updated XMLTV file for EPG #%s from url - '%s'", epg_id, epg['url'])
    start_time = time.time()
    xmltv_file = os.path.join(config.config_path, 'cache', 'epgs', f"{epg_id}.xml")
    download_xmltv_epg(epg['url'], xmltv_file)
    execution_time = time.time() - start_time
    logger.info("Updated XMLTV file for EPG #%s was downloaded in '%s' seconds", epg_id, int(execution_time))
    # Read and save EPG data to DB
    logger.info("Importing updated data for EPG #%s", epg_id)
    start_time = time.time()
    channel_id_list = store_epg_channels(config, epg_id)
    store_epg_programmes(config, epg_id, channel_id_list)
    execution_time = time.time() - start_time
    logger.info("Updated data for EPG #%s was imported in '%s' seconds", epg_id, int(execution_time))


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
    settings = config.read_settings()
    logger.info("Generating custom EPG for TVH based on configured channels.")
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
    logger.info("   - Building a programme data for each channel.")
    for result in db.session.query(Channel).order_by(Channel.number.asc()).all():
        if result.enabled:
            channel_id = generate_epg_channel_id(result.number, result.name)
            # Read cached image
            image_data, mime_type = read_base46_image_string(result.logo_base64)
            cache_buster = time.time()
            ext = guess_extension(mime_type)
            logo_url = f"{settings['settings']['app_url']}/tic-api/channels/{channel_id}/logo/{cache_buster}.{ext}"
            # Populate a channels list
            configured_channels.append({
                'channel_id':   channel_id,
                'display_name': result.name,
                'logo_url':     logo_url,
            })
            db_programmes_query = db.session.query(EpgChannelProgrammes) \
                .options(joinedload(EpgChannelProgrammes.channel)) \
                .filter(and_(EpgChannelProgrammes.channel.has(epg_id=result.guide_id),
                             EpgChannelProgrammes.channel.has(channel_id=result.guide_channel_id)
                             )) \
                .order_by(EpgChannelProgrammes.channel_id.asc(), EpgChannelProgrammes.start.asc())
            logger.debug(db_programmes_query)
            db_programmes = db_programmes_query.all()
            programmes = []
            logger.info("       - Building programme list for %s - %s.", channel_id, result.name)
            for programme in db_programmes:
                programmes.append({
                    'start':           programme.start,
                    'stop':            programme.stop,
                    'start_timestamp': programme.start_timestamp,
                    'stop_timestamp':  programme.stop_timestamp,
                    'title':           programme.title,
                    'desc':            programme.desc,
                    'categories':      json.loads(programme.categories)
                })
            all_channel_programmes_data.append({
                'channel':    channel_id,
                'tags':       [tag.name for tag in result.tags],
                'programmes': programmes
            })
    # Loop over all configured channels
    logger.info("   - Generating XML channel info.")
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
    logger.info("   - Generating XML channel programme data.")
    for channel_programmes_data in all_channel_programmes_data:
        for epg_channel_programme in channel_programmes_data.get('programmes', []):
            # Create a <programme> element for the output file and copy the attributes from the input programme
            output_programme = ET.SubElement(output_root, 'programme')
            # Build programmes from DB data (manually create attributes etc.
            if epg_channel_programme['start']:
                output_programme.set('start', epg_channel_programme['start'])
            if epg_channel_programme['stop']:
                output_programme.set('stop', epg_channel_programme['stop'])
            if epg_channel_programme['start_timestamp']:
                output_programme.set('start_timestamp', epg_channel_programme['start_timestamp'])
            if epg_channel_programme['stop_timestamp']:
                output_programme.set('stop_timestamp', epg_channel_programme['stop_timestamp'])
            # Set the "channel" ident here
            output_programme.set('channel', str(channel_programmes_data.get('channel')))
            # Loop through all child elements of the input programme and copy them to the output programme
            for child in ['title', 'desc']:
                # Copy all other child elements to the output programme if they exist
                if child in epg_channel_programme:
                    output_child = ET.SubElement(output_programme, child)
                    output_child.text = epg_channel_programme[child]
            # Loop through all categories for this programme and add them as "category" child elements
            if epg_channel_programme['categories']:
                for category in epg_channel_programme['categories']:
                    output_child = ET.SubElement(output_programme, 'category')
                    output_child.text = category
            # Loop through all tags for this channel and add them as "category" child elements
            for tag in channel_programmes_data.get('tags', []):
                output_child = ET.SubElement(output_programme, 'category')
                output_child.text = tag
    # Create an XML file and write the output root element to it
    logger.info("   - Writing out XMLTV file.")
    output_tree = ET.ElementTree(output_root)
    ET.indent(output_tree, space="\t", level=0)
    custom_epg_file = os.path.join(config.config_path, "epg.xml")
    output_tree.write(custom_epg_file, encoding='UTF-8', xml_declaration=True)
    execution_time = time.time() - start_time
    logger.info("The custom XMLTV EPG file for TVH was generated in '%s' seconds", int(execution_time))


def run_tvh_epg_grabbers(config):
    # Trigger a re-grab of the EPG in TVH
    tvh = get_tvh(config)
    tvh.run_internal_epg_grabber()
