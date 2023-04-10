#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from flask import Blueprint, current_app

blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix=''
)
