#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import logging
from logging.config import dictConfig

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from backend.api import tasks

db = SQLAlchemy()
dictConfig({
    'version':    1,
    'formatters': {'default': {
        'format': '%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    }},
    'handlers':   {'wsgi': {
        'class':     'logging.StreamHandler',
        'stream':    'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root':       {
        'level':    'INFO',
        'handlers': ['wsgi']
    }
})


# Custom logging filter that ignores log messages for a specific endpoints
class IgnoreLoggingRoutesFilter(logging.Filter):
    def filter(self, record):
        if "/tic-api/get-background-tasks" in record.getMessage():
            return False
        return True


def register_extensions(app):
    db.init_app(app)


def register_blueprints(app):
    module = import_module('backend.api.routes')
    import_module('backend.api.routes_playlists')
    import_module('backend.api.routes_epgs')
    import_module('backend.api.routes_channels')
    import_module('backend.api.routes_tvh_proxy')
    app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def start_scheduler(app):
    tasks.scheduler.init_app(app)
    tasks.scheduler.start()


def create_app(config, debugging_enabled):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)

    register_blueprints(app)

    configure_database(app)

    start_scheduler(app)

    app.logger.setLevel(logging.INFO)
    if debugging_enabled:
        app.logger.setLevel(logging.DEBUG)

    app.logger.addFilter(IgnoreLoggingRoutesFilter())

    return app
