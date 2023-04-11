#!/usr/bin/env bash
###
# File: run_local_dev_env.sh
# Project: devops
# File Created: Tuesday, 11th April 2023 3:31:39 pm
# Author: Josh.5 (jsunnex@gmail.com)
# -----
# Last Modified: Tuesday, 11th April 2023 11:40:19 pm
# Modified By: Josh.5 (jsunnex@gmail.com)
###

script_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
project_root=$(readlink -e ${script_path}/..)


pushd "${project_root}" || exit 1


# Ensure we have created a venv
if [[ ! -e venv/bin/activate ]]; then
    python3 -m venv venv
fi

# Active the venv
source venv/bin/activate

# Run
export PYTHONUNBUFFERED=1;
export FLASK_APP=run.py;
export FLASK_DEBUG=true;
export HOME_DIR="${PWD}/config/"

mkdir -p "${HOME_DIR}"

# Setup database
flask db init
flask db migrate
flask db upgrade

# Run main process
python3 ./run.py


popd || exit 1
