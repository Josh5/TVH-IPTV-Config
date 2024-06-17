ARG BASE_IMAGE
FROM ${BASE_IMAGE} as base_image

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
FROM base_image

# set version label
ARG VERSION
ARG BUILD_DATE
ARG BASE_IMAGE
LABEL maintainer="Josh.5 <jsunnex@gmail.com>"
LABEL build="Version:- ${VERSION} Build-date:- ${BUILD_DATE} Base:- ${BASE_IMAGE}"

USER root

# environment settings
ENV HOME="/config"

# Runtime packages
RUN \
    echo "**** install container runtime packages ****" \
        && apk add --no-cache \
            bash \
            ca-certificates \
            curl \
            tzdata \
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
                intel-media-driver \
                libdvbcsa \
                libhdhomerun-libs \
                libva \
                libva-intel-driver \
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
        if [ "$(uname -m)" = 'x86_64' ]; then \
            echo "**** install intel media driver packages for x86_64 ****" \
                && apk add --no-cache \
                    intel-media-driver \
            && \
            echo \
        ; fi \
        && \
        echo \
    ; fi \
    && \
    echo

# Install python dependencies
ARG PYTHONDONTWRITEBYTECODE="1"
ARG PYTHONUNBUFFERED="1"
COPY requirements.txt /app/requirements.txt
RUN \
    echo "**** Install python dependencies ****" \
        && mkdir -p /app \
        && python3 -m venv --symlinks /var/venv-docker \
        && . /var/venv-docker/bin/activate \
        && python3 -m pip install --no-cache-dir --upgrade pip \
        && python3 -m pip install --no-cache-dir -r /app/requirements.txt \
    && \
    echo

# Install project
COPY docker/overlay /
COPY --from=frontend_build_stage /build/dist/spa /app/frontend/dist/spa
COPY backend /app/backend
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini
COPY run.py /app/run.py
COPY db-migrate.sh /app/db-migrate.sh

# Set environment variables
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
ENTRYPOINT [ "/entrypoint.sh" ]
