#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import logging
import threading
from queue import Queue
from flask_apscheduler import APScheduler

scheduler = APScheduler()

logger = logging.getLogger('werkzeug.tasks')


class TaskQueueBroker:
    __instance = None
    __lock = threading.Lock()

    def __init__(self):
        if TaskQueueBroker.__instance is not None:
            raise Exception("Singleton instance already exists!")
        else:
            # Create the singleton instance
            TaskQueueBroker.__instance = self
            # Create the queue
            self.__running_task = None
            self.__task_queue = Queue()
            self.__task_names = set()

    @staticmethod
    def get_instance():
        # Ensure no other threads can access this method at the same time
        with TaskQueueBroker.__lock:
            # If the singleton instance has not been created yet, create it
            if TaskQueueBroker.__instance is None:
                TaskQueueBroker()
        return TaskQueueBroker.__instance

    def add_task(self, task):
        if task['name'] in self.__task_names:
            logger.debug("Task already queued. Ignoring.")
            return
        self.__task_queue.put(task)
        self.__task_names.add(task['name'])

    def get_next_task(self):
        # Get the next task from the queue
        if not self.__task_queue.empty():
            task = self.__task_queue.get()
            self.__task_names.remove(task['name'])
        else:
            return None

    def execute_tasks(self):
        if self.__running_task is not None:
            logger.warning("Another process is already running scheduled tasks.")
        if self.__task_queue.empty():
            logger.debug("No pending tasks found.")
            return
        while not self.__task_queue.empty():
            task = self.__task_queue.get()
            self.__task_names.remove(task['name'])
            self.__running_task = task['name']
            # Execute task here
            try:
                logger.info("Executing task - %s.", task['name'])
                task['function'](*task['args'])
            except Exception as e:
                logger.error("Failed to run task %s - %s", task['name'], str(e))
        self.__running_task = None

    def get_currently_running_task(self):
        return self.__running_task

    def get_pending_tasks(self):
        results = []
        for task_name in self.__task_names:
            results.append(task_name)
        return results


def configure_tvh_with_defaults(app):
    logger.info("Configuring TVH")
    config = app.config['APP_CONFIG']
    from backend.tvheadend.tvh_requests import configure_tvh
    configure_tvh(config)


def update_playlists(app):
    logger.info("Updating Playlists")
    config = app.config['APP_CONFIG']
    from backend.playlists import import_playlist_data_for_all_playlists
    import_playlist_data_for_all_playlists(config)


def update_epgs(app):
    logger.info("Updating EPGs")
    config = app.config['APP_CONFIG']
    from backend.epgs import import_epg_data_for_all_epgs
    import_epg_data_for_all_epgs(config)


def rebuild_custom_epg(app):
    logger.info("Rebuilding custom EPG")
    config = app.config['APP_CONFIG']
    from backend.epgs import build_custom_epg
    build_custom_epg(config)


def update_tvh_epg(app):
    logger.info("Triggering update of TVH EPG")
    config = app.config['APP_CONFIG']
    from backend.epgs import run_tvh_epg_grabbers
    run_tvh_epg_grabbers(config)


def update_tvh_networks(app):
    logger.info("Updating channels in TVH")
    config = app.config['APP_CONFIG']
    from backend.playlists import publish_playlist_networks
    publish_playlist_networks(config)


def update_tvh_channels(app):
    logger.info("Updating channels in TVH")
    config = app.config['APP_CONFIG']
    from backend.channels import publish_bulk_channels_to_tvh
    publish_bulk_channels_to_tvh(config)


def update_tvh_muxes(app):
    logger.info("Updating muxes in TVH")
    config = app.config['APP_CONFIG']
    from backend.channels import publish_channel_muxes
    publish_channel_muxes(config)


def map_new_tvh_services(app):
    logger.info("Mapping new services in TVH")
    config = app.config['APP_CONFIG']
    # Map any new services
    from backend.channels import map_all_services, cleanup_old_channels
    map_all_services(config)
    # Clear out old channels
    cleanup_old_channels(config)
