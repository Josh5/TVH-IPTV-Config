#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import logging
import time
from importlib import import_module

import quart_flask_patch
from quart import Quart

from backend import config
from backend.api import tasks


# Custom logging filter that ignores log messages for a specific endpoints
class IgnoreLoggingRoutesFilter(logging.Filter):
    def filter(self, record):
        if "/tic-api/get-background-tasks" in record.getMessage():
            return False
        return True


def init_db(app):
    from backend.models import db
    app.config["SQLALCHEMY_DATABASE_URI"] = config.sqlalchemy_database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.sqlalchemy_track_modifications
    db.init_app(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return db


def register_blueprints(app):
    module = import_module('backend.api.routes')
    import_module('backend.api.routes_playlists')
    import_module('backend.api.routes_epgs')
    import_module('backend.api.routes_channels')
    import_module('backend.api.routes_playlist_proxy')
    import_module('backend.api.routes_hls_proxy')
    app.register_blueprint(module.blueprint)


def create_app():
    # Fetch app config
    app_config = config.Config()
    app_config.runtime_key = int(time.time())
    # Create app
    app = Quart(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = config.secret_key
    app.config["SCHEDULER_API_ENABLED"] = config.scheduler_api_enabled
    app.config["APP_CONFIG"] = app_config
    app.config["ASSETS_ROOT"] = config.assets_root

    # Init the DB connection
    db = init_db(app)

    # Register the route blueprints
    register_blueprints(app)

    log = logging.getLogger('hypercorn.access')
    app.logger.setLevel(logging.INFO)
    log.setLevel(logging.INFO)
    if config.enable_debugging:
        app.logger.setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)
    log.addFilter(IgnoreLoggingRoutesFilter())

    return app
