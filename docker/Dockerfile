#  _____ ____   ___  _   _ _____ _____ _   _ ____    ____ _____  _    ____ _____ 
# |  ___|  _ \ / _ \| \ | |_   _| ____| \ | |  _ \  / ___|_   _|/ \  / ___| ____|
# | |_  | |_) | | | |  \| | | | |  _| |  \| | | | | \___ \ | | / _ \| |  _|  _|  
# |  _| |  _ <| |_| | |\  | | | | |___| |\  | |_| |  ___) || |/ ___ \ |_| | |___ 
# |_|   |_| \_\\___/|_| \_| |_| |_____|_| \_|____/  |____/ |_/_/   \_\____|_____|
#                                                                                
FROM node:22-alpine as frontend_build_stage

COPY ./frontend/package.json /build/
COPY ./frontend/package-lock.json /build/

WORKDIR /build

RUN \
    echo "** Install node dependencies **" \
        && npm ci \
    && \
    echo

COPY ./frontend /build
RUN \
    echo "** Build frontend **" \
        && npm run build:publish \
    && \
    echo

#  __  __    _    ___ _   _ 
# |  \/  |  / \  |_ _| \ | |
# | |\/| | / _ \  | ||  \| |
# | |  | |/ ___ \ | || |\  |
# |_|  |_/_/   \_\___|_| \_|
#
FROM python:3.12-alpine

# set version label
ARG BUILD_DATE
ARG VERSION
LABEL build_version="Version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="Josh.5 <jsunnex@gmail.com>"

# environment settings
ENV HOME="/config"

RUN \
    echo "**** install runtime packages ****" \
        && apk add --no-cache \
            bash \
            ffmpeg \
            ffmpeg-libs \
    && \
    echo

# set environment variables
ENV PYTHONDONTWRITEBYTECODE="1"
ENV PYTHONUNBUFFERED="1"
ENV FLASK_APP="/app/run.py"
ENV FLASK_RUN_PORT="9985"
ENV FLASK_RUN_HOST="0.0.0.0"
ENV ENABLE_DEBUGGING="false"
ENV SKIP_MIGRATIONS="false"

# Install python dependencies
COPY requirements.txt /app/requirements.txt
RUN \
    echo "** Install python dependencies **" \
        && mkdir -p /app \
        && python3 -m venv --symlinks /var/venv-docker \
        && . /var/venv-docker/bin/activate \
        && python3 -m pip install --upgrade pip \
        && python3 -m pip install --no-cache-dir -r /app/requirements.txt \
    && \
    echo

# Install project
COPY --from=frontend_build_stage /build/dist/spa /app/frontend/dist/spa
COPY backend /app/backend
COPY migrations /app/migrations
COPY run.py /app/run.py
COPY proxy.py /app/proxy.py
COPY db-migrate.sh /app/db-migrate.sh

# Set working directory
WORKDIR /app/

# Expose ports
EXPOSE 9985/tcp

# Install entrypoint script
COPY ./docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
