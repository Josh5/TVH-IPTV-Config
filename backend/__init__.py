#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from importlib import import_module

db = SQLAlchemy()


def register_extensions(app):
    db.init_app(app)


def register_blueprints(app):
    module = import_module('backend.api.routes')
    import_module('backend.api.routes_playlists')
    import_module('backend.api.routes_epgs')
    import_module('backend.api.routes_channels')
    app.register_blueprint(module.blueprint)


# def register_blueprints(app):
#     for module_name in ['routes', 'routes_playlists']:
#         module = import_module('api.{}'.format(module_name))
#         app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)

    register_blueprints(app)

    configure_database(app)

    return app
