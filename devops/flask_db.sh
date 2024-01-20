#!/usr/bin/env bash
###
# File: run_local_dev_env.sh
# Project: devops
# File Created: Tuesday, 11th April 2023 3:31:39 pm
# Author: Josh.5 (jsunnex@gmail.com)
# -----
# Last Modified: Saturday, 20th January 2024 4:22:58 pm
# Modified By: Josh.5 (jsunnex@gmail.com)
###

script_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
project_root=$(readlink -e ${script_path}/..)

pushd "${project_root}" || exit 1

# Ensure we have created a venv
if [[ ! -e venv-local/bin/activate ]]; then
    python3 -m venv venv-local
fi
# Active the venv
source venv-local/bin/activate

# Configure env
export PYTHONUNBUFFERED=1;
export FLASK_APP=run.py;
export FLASK_DEBUG=true;
export HOME_DIR="${PWD}/dev_env/config/"

mkdir -p "${HOME_DIR}"

# Run flask DB command
flask db ${@}

popd || exit 1
