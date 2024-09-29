ARG BASE_IMAGE
FROM ${BASE_IMAGE} AS base_image

#  _____ ____   ___  _   _ _____ _____ _   _ ____    ____ _____  _    ____ _____
# |  ___|  _ \ / _ \| \ | |_   _| ____| \ | |  _ \  / ___|_   _|/ \  / ___| ____|
# | |_  | |_) | | | |  \| | | | |  _| |  \| | | | | \___ \ | | / _ \| |  _|  _|
# |  _| |  _ <| |_| | |\  | | | | |___| |\  | |_| |  ___) || |/ ___ \ |_| | |___
# |_|   |_| \_\\___/|_| \_| |_| |_____|_| \_|____/  |____/ |_/_/   \_\____|_____|
#
FROM node:22-bookworm AS frontend_build_stage

COPY ./frontend/package.json /build/
COPY ./frontend/package-lock.json /build/

WORKDIR /build

RUN \
    echo "** Install node build dependencies **" \
        && apt-get update \
        && apt-get install -y --no-install-recommends \
            build-essential \
            libffi-dev \
            libssl-dev \
            python3-dev \
            python3-pip \
            python3-setuptools \
            python3-venv \
            python3-wheel \
    && \
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


#  ____    _    ____ _  _______ _   _ ____    ____ _____  _    ____ _____ 
# | __ )  / \  / ___| |/ / ____| \ | |  _ \  / ___|_   _|/ \  / ___| ____|
# |  _ \ / _ \| |   | ' /|  _| |  \| | | | | \___ \ | | / _ \| |  _|  _|  
# | |_) / ___ \ |___| . \| |___| |\  | |_| |  ___) || |/ ___ \ |_| | |___ 
# |____/_/   \_\____|_|\_\_____|_| \_|____/  |____/ |_/_/   \_\____|_____|
#                                                                         
FROM base_image AS backend_build_stage

USER root
WORKDIR /var

RUN \
    echo "** Install python build dependencies **" \
        && apt-get update \
        && apt-get install -y --no-install-recommends \
            build-essential \
            libffi-dev \
            libssl-dev \
            python3-dev \
            python3-pip \
            python3-setuptools \
            python3-venv \
            python3-wheel \
    && \
    echo

# Install python dependencies
ARG PYTHONDONTWRITEBYTECODE="1"
ARG PYTHONUNBUFFERED="1"
COPY requirements.txt /requirements.txt
RUN \
    echo "**** Install python dependencies ****" \
        && python3 -m venv --symlinks /var/venv-docker \
        && . /var/venv-docker/bin/activate \
        && python3 -m pip install --no-cache-dir --upgrade pip \
        && python3 -m pip install --no-cache-dir -r /requirements.txt \
    && \
    echo


#  __  __    _    ___ _   _
# |  \/  |  / \  |_ _| \ | |
# | |\/| | / _ \  | ||  \| |
# | |  | |/ ___ \ | || |\  |
# |_|  |_/_/   \_\___|_| \_|
#
FROM base_image

# set version label
ARG VERSION
ARG BUILD_DATE
ARG BASE_IMAGE
LABEL maintainer="Josh.5 <jsunnex@gmail.com>"
LABEL build="Version:- ${VERSION} Build-date:- ${BUILD_DATE} Base:- ${BASE_IMAGE}"

USER root

# Runtime packages
COPY --from=tianon/gosu:bookworm /gosu /usr/local/bin/
RUN \
    echo "**** update apt repositories ****" \
        && apt-get update \
    && \
    echo "**** install container runtime packages ****" \
        && apt-get install -y --no-install-recommends \
            bash \
            ca-certificates \
            curl \
            tini \
            tzdata \
    && \
    echo "**** install tic application runtime packages ****" \
        && apt-get install -y --no-install-recommends \
            ffmpeg \
    && \
    if command -v tvheadend &> /dev/null; then \
        echo "**** install tvh application runtime packages ****" \
            && apt-get install -y --no-install-recommends \
                libavahi-client3 \
                libavcodec59 \
                libavdevice59 \
                libavfilter8 \
                libavfilter8 \
                libavutil57 \
                libdbus-1-3 \
                libdvbcsa1 \
                libhdhomerun4 \
                libopus0 \
                libpcre2-8-0 \
                libpostproc56 \
                libssl3 \
                libswscale6 \
                liburiparser1 \
                libva2 \
                libvpx7 \
                libx264-164 \
                libx265-199 \
                mesa-va-drivers \
                mesa-vdpau-drivers \
                pngquant \
                python3 \
                x264 \
                x265 \
                xmltv \
                zlib1g \
                zlib1g-dev \
        && \
        echo "**** install nginx reverse proxy ****" \
            && apt-get install -y --no-install-recommends \
                nginx \
        && \
        if [ "$(uname -m)" = 'x86_64' ]; then \
            echo "**** install intel media driver packages for x86_64 ****" \
                && apt-get install -y --no-install-recommends \
                    intel-media-va-driver \
                    i965-va-driver \
            && \
            echo \
        ; fi \
        && \
        echo \
    ; fi \
    && \
    echo "**** cleanup apt cache ****" \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/* \
    && \
    echo

# Install project
COPY --from=backend_build_stage /var/venv-docker /var/venv-docker
COPY --from=frontend_build_stage /build/dist/spa /app/frontend/dist/spa
COPY docker/overlay /
COPY backend /app/backend
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini
COPY run.py /app/run.py
COPY db-migrate.sh /app/db-migrate.sh

# Set environment variables
ENV HOME="/config"
ENV FLASK_APP="/app/run.py"
ENV FLASK_RUN_PORT="9985"
ENV FLASK_RUN_HOST="0.0.0.0"
ENV ENABLE_DEBUGGING="false"
ENV SKIP_MIGRATIONS="false"

# Set working directory
WORKDIR /app/

# Expose ports
EXPOSE 9985/tcp

# Install entrypoint script
COPY ./docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "/usr/bin/tini", "--", "/entrypoint.sh" ]
