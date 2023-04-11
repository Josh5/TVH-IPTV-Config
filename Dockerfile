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
        && npm run build \
        && \
    echo

#  __  __    _    ___ _   _ 
# |  \/  |  / \  |_ _| \ | |
# | |\/| | / _ \  | ||  \| |
# | |  | |/ ___ \ | || |\  |
# |_|  |_/_/   \_\___|_| \_|
#
FROM python:3.9

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP run.py
ENV DEBUG True

# Create a runtime user
RUN \
    echo "*** create app user and make our folders ***" && \
    groupmod -g 1000 users && \
    useradd -u 1000 -U -d /home/app -s /bin/false app && \
    usermod -G users app && \
    mkdir -p \
    /home/app \
    /app \
    && chown -Rv app:app \
    /home/app \
    /app \
    && \
    echo

# Install python dependencies
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt


# Set working directory to the /app path and switch to the 'app' user
WORKDIR /app
USER app

# Install project
COPY --from=frontend_build_stage --chown=app:app /build/dist/spa /app/frontend/dist/spa
COPY backend /app/backend
COPY lib /app/lib
COPY run.py /app/run.py
COPY gunicorn-cfg.py /app/gunicorn-cfg.py


# TODO: Re-add db scripts when/if migrated to sqlite
## RUN flask db init
## RUN flask db migrate
## RUN flask db upgrade

# Execute gunicorn for main process
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]
