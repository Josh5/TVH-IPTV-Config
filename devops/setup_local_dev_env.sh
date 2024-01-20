#!/usr/bin/env bash
###
# File: setup_local_dev_env.sh
# Project: devops
# File Created: Tuesday, 11th April 2023 3:14:41 pm
# Author: Josh.5 (jsunnex@gmail.com)
# -----
# Last Modified: Saturday, 20th January 2024 4:23:22 pm
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

# Install all requirements
python3 -m pip install -r requirements.txt

# Install the project to the venv
./devops/frontend_install.sh


popd || exit 1
