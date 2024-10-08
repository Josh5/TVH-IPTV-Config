#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import hashlib
import base64
import time
from functools import wraps

from quart import Response, request, current_app

digest_auth_realm = "tvheadend"


def unauthorized_response(auth_type="Basic"):
    if auth_type == "Basic":
        auth_header = 'Basic realm="{}"'.format(digest_auth_realm)
    else:
        nonce = hashlib.md5(str(time.time()).encode()).hexdigest()
        auth_header = (
            f'Digest realm="{digest_auth_realm}", '
            f'qop="auth", nonce="{nonce}", opaque="abcdef"'
        )

    response = Response(status=401)
    response.headers["WWW-Authenticate"] = auth_header
    return response


def validate_digest_auth(auth_info, admin_user):
    username = auth_info.get("username")
    if username != admin_user.get('username'):
        return False

    ha1 = hashlib.md5(f"{username}:{digest_auth_realm}:{admin_user.get('password')}".encode()).hexdigest()
    ha2 = hashlib.md5(f'{request.method}:{auth_info["uri"]}'.encode()).hexdigest()
    response = hashlib.md5(
        f'{ha1}:{auth_info["nonce"]}:{auth_info["nc"]}:'
        f'{auth_info["cnonce"]}:{auth_info["qop"]}:{ha2}'.encode()
    ).hexdigest()

    return response == auth_info.get("response")


def validate_basic_auth(auth_info, admin_user):
    username, password = base64.b64decode(auth_info).decode().split(':')
    return username == admin_user['username'] and password == admin_user['password']


async def check_auth():
    config = current_app.config['APP_CONFIG']
    settings = config.read_settings()
    if not settings.get('settings', {}).get('enable_admin_user', True):
        return True

    # Check if Authorization header is present
    auth = request.headers.get("Authorization")
    if not auth:
        return False

    # Check if auth is "Digest" type
    if auth.startswith("Digest "):
        # Validate provided auth
        auth_type = "Digest"
        auth_info = {}
        for item in auth[len("Digest "):].split(","):
            key, value = item.split("=", 1)
            auth_info[key.strip()] = value.strip().replace('"', '')
    # If not "Digest" auth, then it must be Basic auth
    elif auth.startswith("Basic "):
        auth_type = "Basic"
        auth_info = auth[len("Basic "):].strip()
    else:
        return False

    admin_user = {
        'username': 'admin',
        'password': settings['settings'].get('admin_password', 'admin'),
    }

    if auth_type == "Digest" and not validate_digest_auth(auth_info, admin_user):
        return False
    elif auth_type == "Basic" and not validate_basic_auth(auth_info, admin_user):
        return False

    return True


def admin_auth_required(func):
    @wraps(func)
    async def decorated_function(*args, **kwargs):
        if await check_auth():
            return await func(*args, **kwargs)
        return unauthorized_response()

    return decorated_function
