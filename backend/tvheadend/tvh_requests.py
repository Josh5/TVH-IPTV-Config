#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import logging
import os
import aiohttp
import asyncio

logger = logging.getLogger('werkzeug.tvh_requests')

# TVheadend API URLs:
api_config_save = "config/save"
api_imagecache_config_save = "imagecache/config/save"
api_accessentry_grid = "access/entry/grid"
api_accessentry_config_create = "access/entry/create"
api_password_grid = "passwd/entry/grid"
api_password_config_create = "passwd/entry/create"
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
api_list_all_channel_tags = "channeltag/grid"
api_create_channel_tag = "channeltag/create"
api_list_all_channels = "channel/grid"
api_create_channel = "channel/create"
api_services_mapper = "service/mapper/save"
api_services_list = "service/list"
api_int_epggrab_run = "epggrab/internal/rerun"
api_epggrab_list = "epggrab/module/list"

tvh_config = {
    "server_name":    "TVH-IPTV",
    "uilevel":        2,
    "digest":         2,
    "parser_backlog": True,  # See link above default_stream_profile_template config below
}
tvh_imagecache_config = {"enabled": True, "ignore_sslcert": True, "expire": 7, "ok_period": 168, "fail_period": 24}
tvh_client_access_entry_comment = "TVH IPTV Config client access entry"
tvh_client_password_comment = "TVH IPTV Config client password entry"
tvh_client_access_entry = {
    "comment":             "COMMENT",
    "enabled":             True,
    "username":            "user",
    "change":              [
        "change_profiles",
        "change_uilevel",
        "change_xmltv_output",
        "change_htsp_output"
    ],
    "webui":               True,
    "admin":               False,
    "streaming":           ["basic", "htsp"],
    "dvr":                 ["basic", "htsp", "all", "all_rw", "failed"],
    "prefix":              "0.0.0.0/0,::/0",
    "lang":                "", "themeui": "",
    "langui":              "",
    "profile":             "",
    "dvr_config":          "",
    "channel_min":         "0",
    "channel_max":         "0",
    "channel_tag_exclude": False,
    "channel_tag":         "",
    "xmltv_output_format": 0,
    "htsp_output_format":  0,
    "uilevel":             0,
    "uilevel_nochange":    0,
    "conn_limit_type":     0,
    "conn_limit":          0,
    "htsp_anonymize":      False
}
tvh_client_password = {
    "comment":  "COMMENT",
    "username": "USERNAME",
    "password": "PASSWORD",
    "enabled":  True,
    "auth":     ["enable"],
}
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
    "max_timeout":  10,
    "skipinitscan": True,
    "bouquet":      False, "max_bandwidth": 0, "nid": 0, "ignore_chnum": True, "satip_source": 0,
    "charset":      "", "use_libav": False, "scan_create": False, "spriority": 1, "icon_url": "",
    "idlescan":     False, "sid_chnum": False, "localtime": 0, "service_sid": 0, "remove_scrambled": True
}
channel_tag_comment = "TVH IPTV Config channel tag"
channel_tag_template = {
    "enabled":     True,
    "name":        "TAG_NAME",
    "comment":     "TAG_COMMENT",
    "index":       0,
    "internal":    False,
    "icon":        "",
    "private":     False,
    "titled_icon": False
}
channel_template = {
    "enabled":      True,
    "name":         "CHANNEL_NAME",
    "number":       "CHANNEL_NUMBER",
    "tags":         "CHANNEL_TAGS",
    "icon":         "CHANNEL_ICON",
    "services":     "", "autoname": False, "epgauto": True, "epglimit": 0, "epggrab": "", "dvr_pre_time": 0,
    "dvr_pst_time": 0, "remote_timeshift": False, "epg_running": 0, "epg_parent": ""
}
mux_template = {
    "iptv_url":          "IPTV_URL",
    "iptv_icon":         "ICON",
    "iptv_sname":        "SERVICE_NAME",
    "iptv_muxname":      "NETWORK - SERVICE_NAME",
    "channel_number":    "0",
    "iptv_epgid":        "0",
    "iptv_tags":         "",
    "enabled":           0,
    "epg":               1, "epg_module_id": "", "use_libav": 0, "iptv_atsc": False, "scan_state": 0, "charset": "",
    "priority":          0, "spriority": 0, "iptv_send_reports": False, "iptv_ret_url": "", "iptv_substitute": False,
    "iptv_interface":    "", "iptv_satip_dvbt_freq": 0, "iptv_satip_dvbc_freq": 0, "iptv_satip_dvbs_freq": 0,
    "iptv_buffer_limit": 0, "tsid_zero": False, "pmt_06_ac3": 0, "eit_tsid_nocheck": False, "sid_filter": 0,
    "iptv_respawn":      False, "iptv_kill": 0, "iptv_kill_timeout": 5, "iptv_env": "", "iptv_hdr": ""
}
# REF: https://tvheadend.org/d/5282-iptv-buffering-stalls-general-drop-outs-settings-that-resolved-things-for-me/41
default_stream_profile_template = {
    "enabled":     True,
    "default":     True,
    "comment":     "MPEG-TS Pass-thru",
    "timeout":     0,
    "priority":    3,
    "fpriority":   0,
    "restart":     True,
    "contaccess":  True,
    "catimeout":   2000,
    "swservice":   True,
    "svfilter":    0,
    "sid":         0,
    "rewrite_pmt": False,
    "rewrite_pat": False,
    "rewrite_sdt": False,
    "rewrite_nit": False,
    "rewrite_eit": False,
}
htsp_stream_profile_template = {
    "enabled":    True,
    "default":    False,
    "comment":    "HTSP Default Stream Settings",
    "timeout":    0,
    "priority":   3,
    "fpriority":  0,
    "restart":    True,
    "contaccess": True,
    "catimeout":  2000,
    "swservice":  True,
    "svfilter":   0,
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


class Tvheadend:

    def __init__(self, host, port, admin_username, admin_password):
        self.api_url = f"http://{host}:{port}/api"
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.timeout = 5
        self.session = aiohttp.ClientSession(auth=aiohttp.BasicAuth(admin_username,
                                                                    admin_password)) if admin_username and admin_password else aiohttp.ClientSession()
        self.default_headers = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def __get(self, url, payload=None, rformat='content'):
        headers = self.default_headers
        async with self.session.get(url, headers=headers, params=payload, allow_redirects=False,
                                    timeout=self.timeout) as r:
            if r.status == 200:
                if rformat == 'json':
                    return await r.json()
                return await r.text()
            raise Exception(f"GET Failed to TVH API - CODE:{r.status} - CONTENT:{await r.text()} - PAYLOAD:{payload}")

    async def __post(self, url, payload=None, rformat='content'):
        headers = self.default_headers
        async with self.session.post(url, headers=headers, data=payload, allow_redirects=False,
                                     timeout=self.timeout) as r:
            if r.status == 200:
                if rformat == 'json':
                    return await r.json()
                return await r.text()
            raise Exception(f"POST Failed to TVH API - CODE:{r.status} - CONTENT:{await r.text()} - PAYLOAD:{payload}")

    async def __json(self, url, payload=None):
        headers = self.default_headers
        headers['Content-Type'] = 'application/json'
        async with self.session.post(url, headers=headers, json=payload, allow_redirects=False,
                                     timeout=self.timeout) as r:
            if r.status == 200:
                return await r.json()
            raise Exception(f"JSON Failed to TVH API - CODE:{r.status} - CONTENT:{await r.text()}")

    async def idnode_load(self, data):
        url = f"{self.api_url}/{api_idnode_load}"
        response = await self.__post(url, payload=data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list

    async def idnode_save(self, node):
        url = f"{self.api_url}/{api_idnode_save}"
        await self.__post(url, payload={"node": json.dumps(node)})

    async def idnode_delete(self, node_uuid):
        url = f"{self.api_url}/{api_idnode_delete}"
        await self.__post(url, payload={"uuid": node_uuid})

    async def save_tvh_config(self, node):
        url = f"{self.api_url}/{api_config_save}"
        await self.__post(url, payload={"node": json.dumps(node)})

    async def save_imagecache_config(self, node):
        url = f"{self.api_url}/{api_imagecache_config_save}"
        await self.__post(url, payload={"node": json.dumps(node)})

    async def create_accessentry_config(self, node):
        url = f"{self.api_url}/{api_imagecache_config_save}"
        await self.__post(url, payload={"node": json.dumps(node)})

    async def save_epggrab_config(self, node):
        url = f"{self.api_url}/{api_epggrab_config_save}"
        await self.__post(url, payload={"node": json.dumps(node)})

    async def disable_all_epg_grabbers(self):
        url = f"{self.api_url}/{api_epggrab_list}"
        response = await self.__get(url, payload={}, rformat='json')
        for grabber in response.get('entries', []):
            await self.idnode_save({"enabled": False, "uuid": grabber['uuid']})

    async def create_and_configure_client_user(self, username, password):
        # Read current access entries
        url = f"{self.api_url}/{api_accessentry_grid}"
        response = await self.__post(url, payload={'groupBy': 'false', 'groupDir': 'ASC'})
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        # Create template for access entry
        node = tvh_client_access_entry.copy()
        node['comment'] = tvh_client_access_entry_comment
        for entry in json_list.get('entries', []):
            if entry.get('comment') == tvh_client_access_entry_comment:
                node['uuid'] = entry['uuid']
        # Create the access control if it does not yet exist
        if not node.get('uuid'):
            # Create access control
            post_data = {"conf": json.dumps(node)}
            # Send request to server
            url = f"{self.api_url}/{api_accessentry_config_create}"
            response = await self.__post(url, payload=post_data)
            try:
                json_list = json.loads(response)
            except json.JSONDecodeError:
                json_list = {}
            node['uuid'] = json_list.get('uuid')
        # Save and update the client user access control
        node['username'] = username
        node['comment'] = tvh_client_access_entry_comment
        await self.idnode_save(node)
        # Read current password entries
        url = f"{self.api_url}/{api_password_grid}"
        response = await self.__post(url, payload={'groupBy': 'false', 'groupDir': 'ASC'})
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        # Create template for password
        node = tvh_client_password.copy()
        node['comment'] = tvh_client_password_comment
        for entry in json_list.get('entries', []):
            if entry.get('comment') == tvh_client_password_comment:
                node['uuid'] = entry['uuid']
        # Create the password if it does not yet exist
        if not node.get('uuid'):
            # Create access control
            post_data = {"conf": json.dumps(node)}
            # Send request to server
            url = f"{self.api_url}/{api_password_config_create}"
            response = await self.__post(url, payload=post_data)
            try:
                json_list = json.loads(response)
            except json.JSONDecodeError:
                json_list = {}
            node['uuid'] = json_list.get('uuid')
        # Save and update the client user access control
        node['username'] = username
        node['password'] = password
        node['comment'] = tvh_client_password_comment
        await self.idnode_save(node)

    async def remove_client_user(self):
        # Read current access entries
        url = f"{self.api_url}/{api_accessentry_grid}"
        response = await self.__post(url, payload={'groupBy': 'false', 'groupDir': 'ASC'})
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        # Look for the client user access entry managed by TIC
        access_entry_uuid = None
        for entry in json_list.get('entries', []):
            if entry.get('comment') == tvh_client_access_entry_comment:
                access_entry_uuid = entry['uuid']
        # Read current password entries
        url = f"{self.api_url}/{api_password_grid}"
        response = await self.__post(url, payload={'groupBy': 'false', 'groupDir': 'ASC'})
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        # Look for the client password managed by TIC
        password_uuid = None
        for entry in json_list.get('entries', []):
            if entry.get('comment') == tvh_client_password_comment:
                password_uuid = entry['uuid']
        # Delete idnodes
        if access_entry_uuid:
            await self.idnode_delete(access_entry_uuid)
        if password_uuid:
            await self.idnode_delete(password_uuid)

    async def enable_xmltv_url_epg_grabber(self):
        url = f"{self.api_url}/{api_epggrab_list}"
        response = await self.__get(url, payload={}, rformat='json')
        for grabber in response.get('entries', []):
            if grabber['title'] == "Internal: XMLTV: XMLTV URL grabber":
                tic_web_host = os.environ.get("APP_HOST_IP", "127.0.0.1")
                tic_web_port = os.environ.get("APP_PORT", "9985")
                node = {
                    "enabled": True, "priority": 1, "dn_chnum": 1, "uuid": grabber['uuid'],
                    "args":    f"http://{tic_web_host}:{tic_web_port}/tic-web/epg.xml"
                }
                await self.idnode_save(node)

    async def configure_default_stream_profile(self):
        response = await self.idnode_load({'enum': 1, 'class': 'profile'})
        for profile in response.get('entries', []):
            if profile['val'] == "pass":
                node = default_stream_profile_template.copy()
                node['uuid'] = profile['key']
                await self.idnode_save(node)

    async def configure_htsp_stream_profile(self):
        response = await self.idnode_load({'enum': 1, 'class': 'profile'})
        for profile in response.get('entries', []):
            if profile['val'] == "htsp":
                node = htsp_stream_profile_template.copy()
                node['uuid'] = profile['key']
                await self.idnode_save(node)

    async def configure_default_recorder_profile(self):
        response = await self.idnode_load({'enum': 1, 'class': 'dvrconfig'})
        for profile in response.get('entries', []):
            if profile['val'] == "(Default profile)":
                node = default_recorder_profile_template.copy()
                node['uuid'] = profile['key']
                await self.idnode_save(node)

    async def list_premade_scanfiles(self, adapter_type):
        url = f"{self.api_url}/{api_list_scanfile}"
        post_data = {"type": adapter_type}
        response = await self.__post(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    async def list_all_network_builders(self):
        url = f"{self.api_url}/{api_view_network_builders}"
        response = await self.__get(url, payload={})
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    async def list_cur_networks(self):
        url = f"{self.api_url}/{api_view_networks}"
        post_data = {
            "start":    "0", "limit": "999999999", "sort": "networkname", "dir": "ASC", "groupBy": "false",
            "groupDir": "ASC"
        }
        response = await self.__post(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    async def create_network(self, name, network_name, max_streams, priority):
        url = f"{self.api_url}/{api_create_network}"
        net_conf = network_template.copy()
        net_conf['networkname'] = name
        net_conf['pnetworkname'] = network_name
        net_conf['max_streams'] = max_streams
        net_conf['priority'] = priority
        post_data = {"class": "iptv_network", "conf": json.dumps(net_conf)}
        # Send request to server
        response = await self.__get(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {}
        return json_list.get('uuid')

    async def delete_network(self, net_uuid):
        await self.idnode_delete(net_uuid)

    async def list_all_muxes(self):
        url = f"{self.api_url}/{api_view_muxes}"
        post_data = {"start": "0", "limit": "999999999", "sort": "name", "dir": "ASC"}
        response = await self.__post(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except:
            json_list = {"entries": []}
        return json_list["entries"]

    async def network_mux_create(self, net_uuid):
        url = f"{self.api_url}/{api_create_mux}"
        mux_conf = mux_template.copy()
        data = {"uuid": net_uuid, "conf": json.dumps(mux_conf)}
        response = await self.__post(url, payload=data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {}
        return json_list.get('uuid')

    async def delete_mux(self, mux_uuid):
        url = f"{self.api_url}/{api_idnode_delete}"
        await self.__post(url, payload={"uuid": mux_uuid})

    async def list_all_services(self):
        url = f"{self.api_url}/{api_list_all_services}"
        post_data = {
            "start":    "0", "limit": "999999999", "sort": "svcname", "dir": "ASC", "groupBy": "false",
            "groupDir": "ASC"
        }
        response = await self.__post(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    async def map_all_services_to_channels(self):
        url = f"{self.api_url}/{api_services_mapper}"
        srv_info = await self.list_all_services()
        services = []
        for service in srv_info:
            services.append(service["uuid"])
        data = {"node": json.dumps({"services": services, "encrypted": False, "merge_same_name": True})}
        response = await self.__post(url, payload=data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {}
        return json_list

    async def run_internal_epg_grabber(self):
        url = f"{self.api_url}/{api_int_epggrab_run}"
        await self.__post(url, payload={'rerun': 1})

    async def list_all_managed_channel_tags(self):
        url = f"{self.api_url}/{api_list_all_channel_tags}"
        post_data = {"limit": "999999999", "sort": "name", "dir": "ASC", "all": 1}
        response = await self.__post(url, payload=post_data)
        return_list = []
        try:
            json_list = json.loads(response)
            for tvh_channel_tag in json_list["entries"]:
                if tvh_channel_tag.get('comment') == channel_tag_comment:
                    return_list.append(tvh_channel_tag)
        except json.JSONDecodeError:
            return_list = []
        return return_list

    async def create_channel_tag(self, tag_name):
        url = f"{self.api_url}/{api_create_channel_tag}"
        channel_conf = channel_tag_template.copy()
        channel_conf["name"] = tag_name
        channel_conf["comment"] = channel_tag_comment
        # Send request to server
        post_data = {"conf": json.dumps(channel_conf)}
        response = await self.__get(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {}
        return json_list.get('uuid')

    async def list_all_channels(self):
        url = f"{self.api_url}/{api_list_all_channels}"
        post_data = {"start": "0", "limit": "999999999", "sort": "services", "dir": "ASC", "all": 1}
        response = await self.__post(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {"entries": []}
        return json_list["entries"]

    async def create_channel(self, channel_name, channel_number, logo_url):
        url = f"{self.api_url}/{api_create_channel}"
        channel_conf = channel_template.copy()
        channel_conf["name"] = channel_name
        channel_conf["number"] = channel_number
        channel_conf["icon"] = logo_url
        # Send request to server
        post_data = {"conf": json.dumps(channel_conf)}
        response = await self.__get(url, payload=post_data)
        try:
            json_list = json.loads(response)
        except json.JSONDecodeError:
            json_list = {}
        return json_list.get('uuid')

    async def delete_channel(self, chan_uuid):
        url = f"{self.api_url}/{api_idnode_delete}"
        await self.__post(url, payload={"uuid": chan_uuid})

    async def manage_client_user_access(self, enabled, username, password):
        if enabled:
            await self.create_and_configure_client_user(username, password)
        else:
            await self.remove_client_user()


async def get_tvh(config):
    settings = config.read_settings()
    tvh_host = settings['settings']['tvheadend']['host']
    tvh_port = settings['settings']['tvheadend']['port']
    tvh_username = settings['settings']['tvheadend']['username']
    tvh_password = settings['settings']['tvheadend']['password']
    return Tvheadend(tvh_host, tvh_port, tvh_username, tvh_password)


async def configure_tvh(config):
    settings = config.read_settings()
    async with await get_tvh(config) as tvh:
        # Update Base Config
        await tvh.save_tvh_config(tvh_config)
        # Update Image Cache Config
        await tvh.save_imagecache_config(tvh_imagecache_config)
        # Create a client user
        enable_client_user = settings.get('settings', {}).get('create_client_user', False)
        username = settings.get('settings', {}).get('client_username', '')
        password = settings.get('settings', {}).get('client_password', '')
        await tvh.manage_client_user_access(enable_client_user, username, password)
        # Configure EPG Grab Config
        await tvh.save_epggrab_config(epggrab_config)
        # Disable all EPG grabbers
        await tvh.disable_all_epg_grabbers()
        # Enable XMLTV URL grabber
        await tvh.enable_xmltv_url_epg_grabber()
        # Configure the default stream profile
        await tvh.configure_default_stream_profile()
        # Configure the htsp stream profile
        await tvh.configure_htsp_stream_profile()
        # Configure the default recorder profile
        await tvh.configure_default_recorder_profile()
