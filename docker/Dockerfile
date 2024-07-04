ARG BASE_IMAGE
FROM ${BASE_IMAGE} AS base_image

#  _____ ____   ___  _   _ _____ _____ _   _ ____    ____ _____  _    ____ _____
# |  ___|  _ \ / _ \| \ | |_   _| ____| \ | |  _ \  / ___|_   _|/ \  / ___| ____|
# | |_  | |_) | | | |  \| | | | |  _| |  \| | | | | \___ \ | | / _ \| |  _|  _|
# |  _| |  _ <| |_| | |\  | | | | |___| |\  | |_| |  ___) || |/ ___ \ |_| | |___
# |_|   |_| \_\\___/|_| \_| |_| |_____|_| \_|____/  |____/ |_/_/   \_\____|_____|
#
FROM node:22-alpine AS frontend_build_stage

COPY ./frontend/package.json /build/
COPY ./frontend/package-lock.json /build/

WORKDIR /build

RUN \
    echo "** Install node build dependencies **" \
        && apk add --no-cache \
            build-base \
            libffi-dev \
            musl-dev \
            openssl-dev \
            py3-pip \
            py3-setuptools \
            py3-wheel \
            python3-dev \
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
        && apk add --no-cache \
            build-base \
            libffi-dev \
            musl-dev \
            openssl-dev \
            py3-pip \
            py3-setuptools \
            py3-wheel \
            python3-dev \
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
COPY --from=tianon/gosu:alpine /gosu /usr/local/bin/
RUN \
    echo "**** install container runtime packages ****" \
        && apk add --no-cache \
            bash \
            ca-certificates \
            curl \
            tini \
            tzdata \
    && \
    echo "**** install tic application runtime packages ****" \
        && apk add --no-cache \
            ffmpeg \
    && \
    if command -v tvheadend &> /dev/null; then \
        echo "**** install tvh application runtime packages ****" \
            && apk add --no-cache \
                bsd-compat-headers \
                ffmpeg \
                ffmpeg4-libavcodec \
                ffmpeg4-libavdevice \
                ffmpeg4-libavfilter \
                ffmpeg4-libavformat \
                ffmpeg4-libavutil \
                ffmpeg4-libpostproc \
                ffmpeg4-libswresample \
                ffmpeg4-libswscale \
                gnu-libiconv \
                libdvbcsa \
                libhdhomerun-libs \
                libva \
                libvpx \
                libxml2 \
                libxslt \
                linux-headers \
                mesa-va-gallium \
                opus \
                pcre2 \
                perl \
                perl-datetime-format-strptime \
                perl-json \
                perl-json-xs \
                py3-requests \
                python3 \
                uriparser \
                x264 \
                x265 \
                xmltv \
                zlib \
        && \
        echo "**** install nginx reverse proxy ****" \
            && apk add --no-cache \
                nginx \
        && \
        if [ "$(uname -m)" = 'x86_64' ]; then \
            echo "**** install intel media driver packages for x86_64 ****" \
                && apk add --no-cache \
                    intel-media-driver \
                    libva-intel-driver \
            && \
            echo \
        ; fi \
        && \
        echo \
    ; fi \
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
ENTRYPOINT [ "/sbin/tini", "--", "/entrypoint.sh" ]
