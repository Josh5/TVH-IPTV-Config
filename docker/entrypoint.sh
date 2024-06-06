#!/usr/bin/env bash
###
# File: entrypoint.sh
# Project: docker
# File Created: Monday, 13th May 2024 4:20:35 pm
# Author: Josh.5 (jsunnex@gmail.com)
# -----
# Last Modified: Monday, 13th May 2024 4:24:23 pm
# Modified By: Josh.5 (jsunnex@gmail.com)
###

set -e -x

# All printed log lines from this script should be formatted with this function
print_log() {
  local timestamp="$(date +'%Y-%m-%d %H:%M:%S %z')"
  local pid="$$"
  local level="$1"
  local message="${@:2}"
  echo "[${timestamp}] [${pid}] [${level^^}] ${message}"
}

# Ensure the customer is set
print_log info "APP_HOST_IP: ${APP_HOST_IP:-APP_HOST_IP variable has not been set}"
print_log info "APP_PORT: ${APP_PORT:-APP_PORT variable has not been set}"
print_log info "ENABLE_DEBUGGING: ${ENABLE_DEBUGGING:-ENABLE_DEBUGGING variable has not been set}"

# Configure required directories
mkdir -p \
    /config/.tvh_iptv_config

# Exec provided command
if [ "X$@" != "X" ]; then
    print_log info "Running command '${@}'"
    exec "$@"
else
    # Install packages (if requested)
    if [ "${RUN_PIP_INSTALL}" = "true" ]; then
        python3 -m venv --symlinks --clear /app/venv-docker
        source /app/venv-docker/bin/activate
        python3 -m pip install --no-cache-dir -r /app/requirements.txt
    else
        source /app/venv-docker/bin/activate
    fi

    # Execute migrations
    if [ "${SKIP_MIGRATIONS}" != "true" ]; then
        print_log info "Running TVH-IPTV-Config DB migrations"
        flask db upgrade
    fi

    # Run Flask server
    flask run
fi
