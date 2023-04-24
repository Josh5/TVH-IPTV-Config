Tvheadend IPTV Config
===========================

![Tvheadend IPTV Config](https://github.com/Josh5/TVH-IPTV-Config/raw/master/logo.png)

<a href='https://ko-fi.com/I2I21F8E1' target='_blank'><img height='26' style='border:0px;height:26px;' src='https://cdn.ko-fi.com/cdn/kofi1.png?v=2' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/Josh5/TVH-IPTV-Config?color=009dc7&label=latest%20release&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/Josh5/TVH-IPTV-Config/releases)
[![GitHub issues](https://img.shields.io/github/issues-raw/Josh5/TVH-IPTV-Config?color=009dc7&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/Josh5/TVH-IPTV-Config/issues?q=is%3Aopen+is%3Aissue)
[![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/Josh5/TVH-IPTV-Config?color=009dc7&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/Josh5/TVH-IPTV-Config/issues?q=is%3Aissue+is%3Aclosed)
[![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/Josh5/TVH-IPTV-Config?color=009dc7&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/Josh5/TVH-IPTV-Config/pulls?q=is%3Aopen+is%3Apr)
[![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed-raw/Josh5/TVH-IPTV-Config?color=009dc7&logo=github&logoColor=%23403d3d&style=flat-square)](https://github.com/Josh5/TVH-IPTV-Config/pulls?q=is%3Apr+is%3Aclosed)

[![Docker Stars](https://img.shields.io/docker/stars/josh5/tvh-iptv-config?color=009dc7&logo=docker&logoColor=%23403d3d&style=for-the-badge)](https://hub.docker.com/r/josh5/tvh-iptv-config)
[![Docker Pulls](https://img.shields.io/docker/pulls/josh5/tvh-iptv-config?color=009dc7&logo=docker&logoColor=%23403d3d&style=for-the-badge)](https://hub.docker.com/r/josh5/tvh-iptv-config)
[![Docker Image Size (tag)](https://img.shields.io/docker/image-size/josh5/tvh-iptv-config/latest?color=009dc7&label=docker%20image%20size&logo=docker&logoColor=%23403d3d&style=for-the-badge)](https://hub.docker.com/r/josh5/tvh-iptv-config)



![GitHub Workflow Status (with branch)](https://img.shields.io/github/actions/workflow/status/Josh5/TVH-IPTV-Config/build_docker_ci.yml?branch=master&logo=github&logoColor=403d3d&style=flat-square)

[![GitHub license](https://img.shields.io/github/license/Josh5/TVH-IPTV-Config?color=009dc7&style=flat-square)]()
---

Tvheadend IPTV Config is a simple wrapper around Tvheadned with the singular goal of making it simple to configure Tvheadend for IPTV playlist.

Tvheadend is an extremely powerful TV streaming server and recorder with excellent support for IPTV sources. However, for most people, setting this up can be difficult and time-consuming.
The goal of this project is to wrap around Tvheadend and, using its API, configure most of the server for you.

### Project Status

This project is currently in beta. I am publishing builds, but the application is very new and could be full of bugs, inefficent processes, or visual blemishes. That being said, if you would like to contribute to this project, feel free to provide a PR.

I will probably not be acknowledging any issue reports or testing. But feel free to also reach out on [Discord](https://unmanic.app/discord) if you would like to contribute any suggestions there.

### Table Of Contents

[Dependencies](#dependencies)

[Install and Run](#install-and-run)

[License](#license)


## Dependencies

 - NodeJS ([Install](https://nodejs.org/en/download)).
 - Python 3.x ([Install](https://www.python.org/downloads/)).
 - Various Python requirements listed in 'requirements.txt' in the project root.


## Install and Run

To run from source:

1) Run the setup script. This will create a local environment, installing a Python virtual environment and all dependencies listed in the requirements.txt file, along with the building the frontend. You should re-run this script whenever you pull updates from GitHub.
    ```
    ./devops/setup_local_dev_env.sh
    ```
2) Run the project.
    ```
    ./devops/run_local_dev_env.sh
    ```

This will create a directory within this project rooth called `./config` which contains all configuration and cache data.


## License

This projected is licensed under the [Apache 2.0 Licence](./LICENSE). 

Copyright (C) Josh Sunnex - All Rights Reserved.

