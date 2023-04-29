#  _____ ____   ___  _   _ _____ _____ _   _ ____    ____ _____  _    ____ _____ 
# |  ___|  _ \ / _ \| \ | |_   _| ____| \ | |  _ \  / ___|_   _|/ \  / ___| ____|
# | |_  | |_) | | | |  \| | | | |  _| |  \| | | | | \___ \ | | / _ \| |  _|  _|  
# |  _| |  _ <| |_| | |\  | | | | |___| |\  | |_| |  ___) || |/ ___ \ |_| | |___ 
# |_|   |_| \_\\___/|_| \_| |_| |_____|_| \_|____/  |____/ |_/_/   \_\____|_____|
#                                                                                
FROM node:16-bullseye as frontend_build_stage

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
FROM lscr.io/linuxserver/tvheadend:latest

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
            ffmpeg \
            ffmpeg4-libs \
            python3 \
            py3-pip \
    && \
    echo

# set environment variables
ENV PYTHONDONTWRITEBYTECODE="1"
ENV PYTHONUNBUFFERED="1"
ENV FLASK_APP="/app/run.py"
ENV FLASK_RUN_PORT="9985"
ENV FLASK_RUN_HOST="0.0.0.0"
ENV DEBUG="False"

# Install python dependencies
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Install project
COPY docker/overlay/ /
COPY --from=frontend_build_stage /build/dist/spa /app/frontend/dist/spa
COPY backend /app/backend
COPY migrations /app/migrations
COPY lib /app/lib
COPY run.py /app/run.py
