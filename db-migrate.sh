#!/bin/bash
set -e

__script_path=$(cd $(dirname ${BASH_SOURCE}) && pwd)

cd ${__script_path}/
./venv-docker/bin/flask db upgrade
echo "Successfully ran migrations"
