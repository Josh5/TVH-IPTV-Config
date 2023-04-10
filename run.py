#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
from flask_minify import Minify
from sys import exit

from lib.config import config_dict
from tvh_iptv_config import create_app

# WARNING: Don't run with debug turned on in production!
DEBUG = (os.getenv('FLASK_DEBUG', 'False').capitalize() == 'True')

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)

if not DEBUG:
    Minify(app=app, html=True, js=False, cssless=False)

if DEBUG:
    app.logger.info('DEBUG       = ' + str(DEBUG))
    app.logger.info('ASSETS_ROOT = ' + app_config.ASSETS_ROOT)

if __name__ == "__main__":
    app.run()
