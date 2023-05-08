#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from flask_migrate import Migrate
from flask_minify import Minify
from sys import exit

from backend.api.tasks import scheduler, update_playlists, map_new_tvh_services, update_epgs, rebuild_custom_epg, \
    update_tvh_muxes, configure_tvh_with_defaults, update_tvh_channels, update_tvh_networks, update_tvh_epg, \
    TaskQueueBroker
from lib.config import config_dict
from backend import create_app, db

# WARNING: Don't run with debug turned on in production!
DEBUG = (os.getenv('FLASK_DEBUG', 'False').capitalize() == 'True')

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]
except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config, DEBUG)
Migrate(app, db)

if not DEBUG:
    Minify(app=app, html=True, js=False, cssless=False)

if DEBUG:
    app.logger.info('DEBUG       = ' + str(DEBUG))
    app.logger.info('DBMS        = ' + app_config.SQLALCHEMY_DATABASE_URI)
    app.logger.info('ASSETS_ROOT = ' + app_config.ASSETS_ROOT)


@scheduler.task('interval', id='background_tasks', seconds=60)
def background_tasks():
    with app.app_context():
        task_broker = TaskQueueBroker.get_instance()
        task_broker.execute_tasks()


@scheduler.task('interval', id='do_5_mins', minutes=5, misfire_grace_time=60)
def every_5_mins():
    with app.app_context():
        task_broker = TaskQueueBroker.get_instance()
        task_broker.add_task({
            'name':     'Mapping all TVH services',
            'function': map_new_tvh_services,
            'args':     [app],
        })


@scheduler.task('interval', id='do_60_mins', minutes=60, misfire_grace_time=300)
def every_60_mins():
    with app.app_context():
        task_broker = TaskQueueBroker.get_instance()
        task_broker.add_task({
            'name':     'Configuring TVH with global default',
            'function': configure_tvh_with_defaults,
            'args':     [app],
        })
        task_broker.add_task({
            'name':     'Configuring TVH networks',
            'function': update_tvh_networks,
            'args':     [app],
        })
        task_broker.add_task({
            'name':     'Configuring TVH channels',
            'function': update_tvh_channels,
            'args':     [app],
        })
        task_broker.add_task({
            'name':     'Configuring TVH muxes',
            'function': update_tvh_muxes,
            'args':     [app],
        })
        task_broker.add_task({
            'name':     'Triggering an update in TVH to fetch the latest XMLTV',
            'function': update_tvh_epg,
            'args':     [app],
        })


@scheduler.task('cron', id='do_job_twice_a_day', hour='0/12', minute=1, misfire_grace_time=900)
def every_12_hours():
    with app.app_context():
        task_broker = TaskQueueBroker.get_instance()
        task_broker.add_task({
            'name':     f'Updating all playlists',
            'function': update_playlists,
            'args':     [app],
        })
        task_broker.add_task({
            'name':     f'Updating all EPGs',
            'function': update_epgs,
            'args':     [app],
        })


@scheduler.task('cron', id='do_job_once_a_day', hour=0, minute=10, misfire_grace_time=900)
def every_24_hours():
    with app.app_context():
        task_broker = TaskQueueBroker.get_instance()
        task_broker.add_task({
            'name':     'Recreating static XMLTV file',
            'function': rebuild_custom_epg,
            'args':     [app],
        })


if __name__ == "__main__":
    app.run()
