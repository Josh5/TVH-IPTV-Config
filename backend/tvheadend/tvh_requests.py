#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import requests
import json

# TVheadend API URLs:
api_config_save = "config/save"
api_imagecache_config_save = "imagecache/config/save"
api_epggrab_config_save = "epggrab/config/save"
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
api_idnode_delete = "idnode/delete"
api_hardware_tree = "hardware/tree"
api_list_all_channels = "channel/grid"
api_services_mapper = "service/mapper/save"
api_services_list = "service/list"
api_int_epggrab_run = "epggrab/internal/rerun"
api_epggrab_list = "epggrab/module/list"

tvh_config = {
    "server_name": "TVH-IPTV",
    "uilevel":     0
}
tvh_imagecache_config = {"enabled": True, "ignore_sslcert": True, "expire": 7, "ok_period": 168, "fail_period": 24}
epggrab_config = {
    "channel_rename":     False, "channel_renumber": False, "channel_reicon": False,
    "epgdb_periodicsave": 0, "epgdb_saveafterimport": True,
    "int_initial":        True, "cron": "25 */12 * * *",
    "ota_initial":        False, "ota_cron": ""
}
network_template = {
    "enabled":      True,
    "networkname":  'NETWORK_NAME',
    "pnetworkname": 'PROVIDER_NETWORK_NAME',
    "max_streams":  1,
    "priority":     1,
    "max_timeout":  30,
    "skipinitscan": True,
    "bouquet":      False, "max_bandwidth": 0, "nid": 0, "ignore_chnum": True, "satip_source": 0,
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
default_recorder_profile_template = {
    "pre-extra-time":               1,
    "post-extra-time":              5,
    "pathname":                     "$t/$t-$c-%F_%R$n.$x",
    "clean-title":                  True,
    "whitespace-in-title":          True,
    "windows-compatible-filenames": False,
    "skip-commercials":             False
}


class TVHeadend:

    def __init__(self, host, port, admin_username, admin_password):
        self.api_url = f"http://{host}:{port}/api"
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.timeout = 5
        self.session = requests.Session()
        if self.admin_username and self.admin_password:
            self.session.auth = (admin_username, admin_password)
        self.default_headers = {}

    def __get(self, url, payload=None, rformat='content'):
        headers = self.default_headers
        r = self.session.get(url, headers=headers, params=payload, allow_redirects=False, timeout=self.timeout)
        if r.status_code == 200:
            if rformat == 'json':
                return r.json()
            return r.content
        raise Exception(f"GET Failed to TVH API - CODE:{r.status_code} - CONTENT:{r.content}")

    def __post(self, url, payload=None, rformat='content'):
        headers = self.default_headers
        r = self.session.post(url, headers=headers, data=payload, allow_redirects=False, timeout=self.timeout)
        if r.status_code == 200:
            if rformat == 'json':
                return r.json()
            return r.content
        raise Exception(f"POST Failed to TVH API - CODE:{r.status_code} - CONTENT:{r.content}")

    def __json(self, url, payload=None):
        headers = self.default_headers
        headers['Content-Type'] = 'application/json'
        r = self.session.post(url, headers=headers, json=payload, allow_redirects=False, timeout=self.timeout)
        if r.status_code == 200:
            return r.json()
        raise Exception(f"JSON Failed to TVH API - CODE:{r.status_code} - CONTENT:{r.content}")

    def idnode_load(self, data):
        url = f"{self.api_url}/{api_idnode_load}"
        response = self.__post(url, payload=data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list

    def idnode_save(self, node):
        url = f"{self.api_url}/{api_idnode_save}"
        self.__post(url, payload={"node": json.dumps(node)})

    def idnode_delete(self, node_uuid):
        url = f"{self.api_url}/{api_idnode_delete}"
        self.__post(url, payload={"uuid": node_uuid})

    def save_tvh_config(self, node):
        url = f"{self.api_url}/{api_config_save}"
        self.__post(url, payload={"node": json.dumps(node)})

    def save_imagecache_config(self, node):
        url = f"{self.api_url}/{api_imagecache_config_save}"
        self.__post(url, payload={"node": json.dumps(node)})

    def save_epggrab_config(self, node):
        url = f"{self.api_url}/{api_epggrab_config_save}"
        self.__post(url, payload={"node": json.dumps(node)})

    def disable_all_epg_grabbers(self):
        url = f"{self.api_url}/{api_epggrab_list}"
        response = self.__get(url, payload={}, rformat='json')
        for grabber in response.get('entries', []):
            self.idnode_save({"enabled": False, "uuid": grabber['uuid']})

    def enable_xmltv_url_epg_grabber(self):
        url = f"{self.api_url}/{api_epggrab_list}"
        response = self.__get(url, payload={}, rformat='json')
        for grabber in response.get('entries', []):
            if grabber['title'] == "Internal: XMLTV: XMLTV URL grabber":
                node = {"enabled": True, "priority": 1, "dn_chnum": 1, "uuid": grabber['uuid'],
                        "args":    "http://127.0.0.1:9985/tic-web/epg.xml"}
                self.idnode_save(node)

    def configure_default_recorder_profile(self):
        response = self.idnode_load({'enum': 1, 'class': 'dvrconfig'})
        for profile in response.get('entries', []):
            if profile['val'] == "(Default profile)":
                node = default_recorder_profile_template.copy()
                node['uuid'] = profile['key']
                self.idnode_save(node)

    def list_premade_scanfiles(self, adapter_type):
        url = f"{self.api_url}/{api_list_scanfile}"
        post_data = {"type": adapter_type}
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
        # Send request to server
        response = self.__get(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {}
        return json_list.get('uuid')

    def delete_network(self, net_uuid):
        self.idnode_delete(net_uuid)

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

    def delete_mux(self, mux_uuid):
        self.idnode_delete(mux_uuid)

    def list_all_services(self):
        url = f"{self.api_url}/{api_list_all_services}"
        data = {"sort": "svcname", "dir": "ASC"}
        response = self.__post(url, payload=data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    def map_all_services_to_channels(self):
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

    def run_internal_epg_grabber(self):
        url = f"{self.api_url}/{api_int_epggrab_run}"
        self.__post(url, payload={'rerun': 1})

    def list_all_channels(self):
        url = f"{self.api_url}/{api_list_all_channels}"
        data = {"sort": "services", "dir": "ASC", "all": 1}
        response = self.__post(url, payload=data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    def delete_channels(self, chan_uuid):
        self.idnode_delete(chan_uuid)


def get_tvh(config):
    settings = config.read_settings()
    tvh_host = settings['settings']['tvheadend']['host']
    tvh_port = settings['settings']['tvheadend']['port']
    tvh_username = settings['settings']['tvheadend']['username']
    tvh_password = settings['settings']['tvheadend']['password']
    return TVHeadend(tvh_host, tvh_port, tvh_username, tvh_password)


def configure_tvh(config):
    tvh = get_tvh(config)
    # Update Base Config
    tvh.save_tvh_config(tvh_config)
    # Update Image Cache Config
    tvh.save_imagecache_config(tvh_imagecache_config)
    # Configure EPG Grab Config
    tvh.save_epggrab_config(epggrab_config)
    # Disable all EPG grabbers
    tvh.disable_all_epg_grabbers()
    # Enable XMLTV URL grabber
    tvh.enable_xmltv_url_epg_grabber()
    # Configure the default recorder profile
    tvh.configure_default_recorder_profile()
