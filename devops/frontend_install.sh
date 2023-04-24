#!/usr/bin/env bash
###
# File: frontend_install.sh
# Project: devops
# File Created: Tuesday, 11th April 2023 3:16:40 pm
# Author: Josh.5 (jsunnex@gmail.com)
# -----
# Last Modified: Monday, 24th April 2023 7:14:51 pm
# Modified By: Josh.5 (jsunnex@gmail.com)
###

script_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
project_root=$(readlink -e ${script_path}/..)


pushd "${project_root}/frontend" || exit 1


# Build frontend backage
npm ci
npm run build 


popd || exit 1
