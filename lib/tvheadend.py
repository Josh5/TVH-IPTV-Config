#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import time

import requests
import json

from lib.playlist import read_data_from_playlist_cache, generate_iptv_url

# TVheadend API URLs:
api_list_scanfile = "dvb/scanfile/list"
api_create_network = "mpegts/network/create"
api_view_networks = "mpegts/network/grid"
api_view_network_builders = "mpegts/network/builders"
api_network_mux_class = "mpegts/network/mux_class"
api_create_mux = "mpegts/network/mux_create"
api_input_networks = "mpegts/input/network_list"
api_view_muxes = "mpegts/mux/grid"
api_list_all_services = "mpegts/service/grid"
api_idnode_load = "idnode/load"
api_idnode_save = "idnode/save"
api_hardware_tree = "hardware/tree"
api_list_all_channels = "channel/grid"
api_services_mapper = "service/mapper/save"
api_services_list = "service/list"

network_template = {
    "enabled":      True,
    "networkname":  'NETWORK_NAME',
    "pnetworkname": 'PROVIDER_NETWORK_NAME',
    "max_streams":  1,
    "priority":     1,
    "max_timeout":  30,
    "skipinitscan": True,
    "bouquet":      False, "max_bandwidth": 0, "nid": 0, "ignore_chnum": False, "satip_source": 0,
    "charset":      "", "use_libav": False, "scan_create": False, "spriority": 1, "icon_url": "",
    "idlescan":     False, "sid_chnum": False, "localtime": 0, "service_sid": 0, "remove_scrambled": True
}
mux_template = {
    "uuid":              "MUX_UUID",
    "iptv_url":          "IPTV_URL",
    "iptv_icon":         "ICON",
    "iptv_sname":        "SERVICE_NAME",
    "iptv_muxname":      "NETWORK - SERVICE_NAME",
    "channel_number":    "CHANNEL_NUMBER",
    "iptv_epgid":        "CHANNEL_NUMBER",
    "iptv_tags":         "",
    "enabled":           0,
    "epg":               1, "epg_module_id": "", "use_libav": 0, "iptv_atsc": False, "scan_state": 0, "charset": "",
    "priority":          0, "spriority": 0, "iptv_send_reports": False, "iptv_ret_url": "", "iptv_substitute": False,
    "iptv_interface":    "", "iptv_satip_dvbt_freq": 0, "iptv_satip_dvbc_freq": 0, "iptv_satip_dvbs_freq": 0,
    "iptv_buffer_limit": 0, "tsid_zero": False, "pmt_06_ac3": 0, "eit_tsid_nocheck": False, "sid_filter": 0,
    "iptv_respawn":      False, "iptv_kill": 0, "iptv_kill_timeout": 5, "iptv_env": "", "iptv_hdr": ""
}


class TVHeadend:

    def __init__(self, host, port, admin_username, admin_password):
        self.api_url = f"http://{host}:{port}/api"
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.timeout = 5
        self.session = requests.Session()
        self.session.auth = (admin_username, admin_password)
        self.default_headers = {}

    def __get(self, url, payload=None):
        headers = self.default_headers
        r = self.session.get(url, headers=headers, params=payload, allow_redirects=False, timeout=self.timeout)
        if r.status_code == 200:
            return r.content
        return {}

    def __post(self, url, payload=None):
        headers = self.default_headers
        r = self.session.post(url, headers=headers, data=payload, allow_redirects=False, timeout=self.timeout)
        if r.status_code == 200:
            return r.content
        return {}

    def __json(self, url, payload=None):
        headers = self.default_headers
        headers['Content-Type'] = 'application/json'
        r = self.session.post(url, headers=headers, json=payload, allow_redirects=False, timeout=self.timeout)
        if r.status_code == 200:
            return r.json()
        return {}

    def idnode_load(self, data):
        url = f"{self.api_url}/{api_idnode_load}"
        response = self.__post(url, payload=data)
        try:
            json_list = json.loads(response)["entries"]
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list

    def idnode_save(self, node):
        url = f"{self.api_url}/{api_idnode_save}"
        self.__post(url, payload={"node": json.dumps(node)})

    def list_premade_scanfiles(self, adapter_type):
        url = f"{self.api_url}/{api_list_scanfile}"
        post_data = {}
        post_data["type"] = adapter_type
        response = self.__post(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    def list_all_network_builders(self):
        url = f"{self.api_url}/{api_view_network_builders}"
        response = self.__get(url, payload={})
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    def list_cur_networks(self):
        url = f"{self.api_url}/{api_view_networks}"
        post_data = {}
        post_data["sort"] = "networkname"
        post_data["dir"] = "ASC"
        response = self.__post(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    def create_network(self, name, network_name, max_streams, priority):
        url = f"{self.api_url}/{api_create_network}"
        net_conf = network_template.copy()
        net_conf['networkname'] = name
        net_conf['pnetworkname'] = network_name
        net_conf['max_streams'] = max_streams
        net_conf['priority'] = priority
        post_data = {"class": "iptv_network", "conf": json.dumps(net_conf)}
        ### # Get current list
        ### dnode_data = {"class": "mpegts_network", "enum": "1"}
        ### past_networks = self.idnode_load(dnode_data)
        # Send request to server
        response = self.__get(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {}
        return json_list.get('uuid')
        ## current_networks = idnode_load(dnode_data)
        ## for net in current_networks:
        ##     if not any(d['key'] == net["key"] for d in past_networks):
        ##         # print "NOT FOUND - "+net["val"]+" "+net["key"]
        ##         return net
        ## return af9c2d74817cc22f95d1a3d4a3b85f65

    def list_all_muxes(self, sort="name"):
        url = f"{self.api_url}/{api_view_muxes}"
        post_data = {}
        post_data["sort"] = sort
        post_data["dir"] = "ASC"
        response = self.__post(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except:
            json_list = {"entries": []}
        return json_list["entries"]

    def network_mux_create(self, net_uuid):
        url = f"{self.api_url}/{api_create_mux}"
        mux_conf = mux_template.copy()
        data = {"uuid": net_uuid, "conf": json.dumps(mux_conf)}
        response = self.__post(url, payload=data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {}
        return json_list.get('uuid')

    def list_all_services(self):
        url = f"{self.api_url}/{api_list_all_services}"
        data = {"sort": "svcname", "dir": "ASC"}
        response = self.__post(url, payload=data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    def map_all_services(self):
        url = f"{self.api_url}/{api_services_mapper}"
        srv_info = self.list_all_services()
        services = []
        for service in srv_info:
            services.append(service["uuid"])
        data = {"node": json.dumps({"services": services, "encrypted": False, "merge_same_name": True})}
        response = self.__post(url, payload=data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {}
        return json_list


def get_tvh(config):
    settings = config.read_settings()
    tvh_host = settings['settings']['tvheadend']['host']
    tvh_port = settings['settings']['tvheadend']['port']
    tvh_username = settings['settings']['tvheadend']['username']
    tvh_password = settings['settings']['tvheadend']['password']
    return TVHeadend(tvh_host, tvh_port, tvh_username, tvh_password)


def configure_playlist_networks(config):
    settings = config.read_settings()
    tvh = get_tvh(config)

    # Loop over configured playlists
    existing_uuids = []
    net_priority = 0
    for key in settings['playlists']:
        print(key)
        net_priority += 1
        playlist_info = settings['playlists'][key]
        net_uuid = playlist_info.get('tvh_uuid')
        playlist_name = playlist_info['name']
        max_streams = playlist_info['connections']
        if net_uuid:
            found = False
            for net in tvh.list_cur_networks():
                if net.get('uuid') == net_uuid:
                    found = True
            if not found:
                net_uuid = None
        if not net_uuid:
            # No network exists, create one
            # Check if network exists with this playlist name
            net_uuid = tvh.create_network(playlist_name, key, max_streams, net_priority)
        # Update network
        net_conf = network_template.copy()
        net_conf['uuid'] = net_uuid
        net_conf['enabled'] = playlist_info['enabled']
        net_conf['networkname'] = playlist_name
        net_conf['pnetworkname'] = key
        net_conf['max_streams'] = max_streams
        net_conf['priority'] = net_priority
        tvh.idnode_save(net_conf)
        # Save network UUID against playlist in settings
        settings['playlists'][key]['tvh_uuid'] = net_uuid
        config.save_settings()
        # Append to list of current network UUIDs
        existing_uuids.append(net_uuid)

    #  TODO: Remove any networks that are not managed. DONT DO THIS UNTIL THINGS ARE ALL WORKING!


def configure_channel_muxes(config):
    settings = config.read_settings()
    tvh = get_tvh(config)
    # TODO: Add support for settings priority
    # Loop over configured channels
    existing_uuids = []
    for key in settings['channels']:
        channel_info = settings['channels'][key]
        if channel_info['enabled']:
            print(f"Configuring MUX for channel '{channel_info['name']}'")
            # Create/update a network in TVH for each enabled playlist line
            for source_id in channel_info.get('sources', {}):
                source = channel_info['sources'][source_id]
                playlist_entries = read_data_from_playlist_cache(config, source.get('playlist_id', ''))
                if not playlist_entries:
                    print("No playlist is configured")
                    continue
                playlist_info = settings['playlists'][source['playlist_id']]
                net_uuid = playlist_info['tvh_uuid']
                # Check if MUX exists with a matching UUID and create it if not
                mux_uuid = source.get('tvh_uuid')
                if mux_uuid:
                    found = False
                    for mux in tvh.list_all_muxes():
                        if mux.get('uuid') == mux_uuid:
                            found = True
                    if not found:
                        mux_uuid = None
                if not mux_uuid:
                    # No mux exists, create one
                    mux_uuid = tvh.network_mux_create(playlist_info['tvh_uuid'])
                # Update mux
                iptv_url = generate_iptv_url(
                    config,
                    url=playlist_entries[source['stream_name']]['url'],
                    service_name=f"{playlist_info['name']} {source['stream_name']}"
                )
                mux_conf = {
                    'enabled':        1,
                    'scan_state':     1,
                    'uuid':           mux_uuid,
                    'iptv_url':       iptv_url,
                    'iptv_icon':      playlist_entries[source['stream_name']]['attributes'].get('tvg-logo', ''),
                    'iptv_sname':     source['stream_name'],
                    'iptv_muxname':   f"{playlist_info['name']} - {source['stream_name']}",
                    'channel_number': key,
                    'iptv_epgid':     key
                }
                tvh.idnode_save(mux_conf)
                # Save network UUID against playlist in settings
                source['tvh_uuid'] = mux_uuid
                config.save_settings()
                # Append to list of current network UUIDs
                existing_uuids.append(net_uuid)

    #  TODO: Remove any muxes that are not managed. DONT DO THIS UNTIL THINGS ARE ALL WORKING!


def map_all_services(config):
    settings = config.read_settings()
    tvh = get_tvh(config)
    tvh.map_all_services()


def read_tvh_config(config):
    settings = config.read_settings()
    return settings['settings']['tvheadend']


def rm__configure_tvh(config):
    settings = config.read_settings()
    tvh_host = settings['settings']['tvheadend'].get('host')
    tvh_port = settings['settings']['tvheadend'].get('port')
    tvh_username = settings['settings']['tvheadend'].get('username')
    tvh_password = settings['settings']['tvheadend'].get('password')
    tvh = TVHeadend(tvh_host, tvh_port, tvh_username, tvh_password)
    # TODO: Configure a debug log array.
    # TODO: Configure a singleton to post update notifications.
    # Loop over configured channels
    for key in settings.get('channels', {}):
        if settings.get('channels', {}).get(key).get('enabled'):
            channel_settings = settings.get('channels', {}).get(key)
            # Create/update a network in TVH for each enabled playlist line
            net_priority = 0
            for source in channel_settings.get('sources', []):
                net_priority += 1
                playlist_name = settings.get('playlists', {}).get(source['playlist'], {})['name']
                max_streams = settings.get('playlists', {}).get(source['playlist'], {})['connections']
                # Check if network exists with this playlist name
                net_uuid = tvh.create_network(playlist_name, source['playlist'], max_streams, net_priority)
                print(net_priority)

    services = []
    failed_muxes = []
    # TODO: Loop over channels and create a list of channel 'Sources'.
    #   - # TODO: For each Source in the list, create/update a TVH mux (PEND only if new). Record mux ID.
    #   - # TODO: Wait for mux to become IDLE and OK. If it does not become OK, then mark in failed_muxes.
    ###   - # TODO: For each Source in the list, trigger a map service.
    #   - # TODO: Find the EPG UUID matching (api/channel/list) this service name. Wait up to a min for this to appear.
    #   - # TODO: Find the newly created service from the mux ID, then update that service with the matching EPG UUID.

    ####for key in settings.get('epg', {}):
    ####    if settings.get('epg', {}).get(key).get('enabled'):
    ####        xmltv_file = os.path.join(config.config_path, 'cache', 'epgs', f"{key}.xml")
    ####        download_xmltv_epg(settings.get('epg', {}).get(key).get('url', ''), xmltv_file)


def test():
    from pprint import pprint
    import sys
    import os

    param = sys.argv[1]
    tvh_host = os.environ.get('tvh_host')
    tvh_port = os.environ.get('tvh_port')
    tvh_admin_username = os.environ.get('tvh_admin_username')
    tvh_admin_password = os.environ.get('tvh_admin_password')

    tvh = TVHeadend(tvh_host, tvh_port, tvh_admin_username, tvh_admin_password)

    if param == "list_scanfiles":
        res = tvh.list_premade_scanfiles("dvbt")
        if not res:
            print(res)
            return
        for x in res:
            print("KEY:   " + x["key"])
            print("VALUE: " + x["val"])
            print()
    # elif param == "add_dvbt_network":
    #     net_class = "dvb_network_dvbt"
    #     networkname = "DVB-TESTER6"
    #     scanfile = "dvbt/nz/dvb-t_nz-WellingtonNgarara"
    #     res = create_network_w_premade_scanfile(net_class, networkname, scanfile)
    #     print(res)
    # elif param == "poll":
    #     url = "http://192.168.1.5:9981/comet/poll"
    #     post_data = {}
    #     post_data["boxid"] = "5b8fac3970d9c302fc2dc1ba20bdb274694651ad"
    #     post_data["immediate"] = "0"
    #     response = post(url, post_data)
    #     print(response)
    # elif param == "list_hardware_tree":
    #     res = list_hardware_tree()
    #     for x in res:
    #         pprint(list_hardware_tree(uuid=x["uuid"]))
    # elif param == "toggle_tuner_setting":
    #     settings = {"enabled": False}
    #     a_uuid = "9d84dad05c885fe8d8a91db0bf0c47ce"
    #     t_uuid = "00d82a25a33337b569edf20c762b1682"
    #     toggle_tuner_setting(a_uuid, t_uuid, settings)
    elif param == "list_cur_networks":
        net_list = tvh.list_cur_networks()
        if not net_list:
            print(net_list)
            return
        for net in net_list:
            print()
            print(net["uuid"])
            print(net["networkname"])
    elif param == "list_all_networks":
        net_list = tvh.list_all_networks()
        if not net_list:
            print(net_list)
            return
        for net in net_list:
            print()
            print()
            print(net["caption"])
            print()
            pprint(net)
    elif param == "list_all_muxes":
        muxes = tvh.list_all_muxes()
        pprint(muxes)
    elif param == "list_mux_class":
        data = {}
        data["class"] = "mpegts_network"
        data["enum"] = "1"
        response = idnode_load(data)
        if response:
            print()
            print()
            pprint(response)
            print()
            for x in response:
                data = {}
                data["uuid"] = x["key"]
                data["grid"] = "1"
                response = idnode_load(data)
                print()
                print("idnode_load " + data["uuid"])
                pprint(response)
                print()
                response = network_mux_class(data["uuid"])
                print()
                print("network_mux_class")
                pprint(response)
                print()
                print()
                print()
                print()
    elif param == "network_mux_create":
        uuid = "ef91d687477a48e6933fc553dc71d15c"
        mux_conf = {u'fec_hi':    'AUTO', u'transmission_mode': 'AUTO', u'delsys': 'DVBT', u'guard_interval': 'AUTO',
                    u'hierarchy': 'AUTO',
                    u'enabled':   '-1', u'plp_id': '-1', u'fec_lo': 'AUTO', u'bandwidth': 'AUTO', u'frequency': '999',
                    u'epg':       '1', u'constellation': 'AUTO'}
        print(network_mux_create(uuid, mux_conf))
    elif param == "list_all_channels":
        pprint(list_all_channels(sort="number"))
    elif param == "toggle_mux_setting":
        uuid = "3b8ac78aad26a92b27206a889403aaad"
        settings = {"scan_state": "1"}
        toggle_mux_setting(uuid, settings=settings)
    else:
        pprint(map_all_services())


if __name__ == '__main__':
    test()
