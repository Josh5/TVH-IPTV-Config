#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from quart import Blueprint

blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix=''
)
