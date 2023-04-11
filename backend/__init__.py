#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from flask import Flask
from importlib import import_module


def register_blueprints(app):
    module = import_module('backend.api.routes')
    import_module('backend.api.routes_playlists')
    import_module('backend.api.routes_epgs')
    app.register_blueprint(module.blueprint)

# def register_blueprints(app):
#     for module_name in ['routes', 'routes_playlists']:
#         module = import_module('api.{}'.format(module_name))
#         app.register_blueprint(module.blueprint)

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    register_blueprints(app)
    return app
