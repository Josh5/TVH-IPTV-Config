#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

logger = logging.getLogger('tic.tasks')

import itertools
from asyncio import Lock, PriorityQueue


class TaskQueueBroker:
    __instance = None
    __lock = Lock()
    __logger = None

    def __init__(self, **kwargs):
        if TaskQueueBroker.__instance is not None:
            raise Exception("Singleton instance already exists!")
        else:
            # Create the singleton instance
            TaskQueueBroker.__instance = self
            # Create the queue
            self.__running_task = None
            self.__status = "running"
            self.__task_queue = PriorityQueue()
            self.__task_names = set()
            self.__priority_counter = itertools.count()

    @staticmethod
    def initialize(app_logger):
        TaskQueueBroker.__logger = app_logger

    @staticmethod
    async def get_instance():
        # Ensure no other coroutines can access this method at the same time
        async with TaskQueueBroker.__lock:
            # If the singleton instance has not been created yet, create it
            if TaskQueueBroker.__instance is None:
                TaskQueueBroker()
        return TaskQueueBroker.__instance

    def set_logger(self, app_logger):
        self.__logger = app_logger

    async def get_status(self):
        return self.__status

    async def toggle_status(self):
        if self.__status == "paused":
            self.__status = "running"
        else:
            self.__status = "paused"
        return self.__status

    async def add_task(self, task, priority=100):
        if task['name'] in self.__task_names:
            self.__logger.debug("Task already queued. Ignoring.")
            return
        await self.__task_queue.put((priority, next(self.__priority_counter), task))
        self.__task_names.add(task['name'])

    async def get_next_task(self):
        # Get the next task from the queue
        if not self.__task_queue.empty():
            task = await self.__task_queue.get()
            self.__task_names.remove(task['name'])
            return task
        else:
            return None

    async def execute_tasks(self):
        if self.__running_task is not None:
            self.__logger.warning("Another process is already running scheduled tasks.")
        if self.__task_queue.empty():
            self.__logger.debug("No pending tasks found.")
            return
        if self.__status == "paused":
            self.__logger.debug("Pending tasks queue paused.")
            return
        while not self.__task_queue.empty():
            if self.__status == "paused":
                break
            priority, i, task = await self.__task_queue.get()
            self.__task_names.remove(task['name'])
            self.__running_task = task['name']
            # Execute task here
            try:
                self.__logger.info("Executing task - %s.", task['name'])
                await task['function'](*task['args'])
            except Exception as e:
                self.__logger.exception("Failed to run task %s - %s", task['name'], str(e))
        self.__running_task = None

    async def get_currently_running_task(self):
        return self.__running_task

    async def get_pending_tasks(self):
        results = []
        async with self.__lock:
            # Temporarily hold tasks to restore them later
            temp_tasks = []
            while not self.__task_queue.empty():
                task = await self.__task_queue.get()
                temp_tasks.append(task)
                priority, i, task_data = task
                results.append(task_data['name'])
            # Put tasks back into the queue
            for task in temp_tasks:
                await self.__task_queue.put(task)
        return results


async def configure_tvh_with_defaults(app):
    logger.info("Configuring TVH")
    config = app.config['APP_CONFIG']
    from backend.tvheadend.tvh_requests import configure_tvh
    await configure_tvh(config)


async def update_playlists(app):
    logger.info("Updating Playlists")
    config = app.config['APP_CONFIG']
    from backend.playlists import import_playlist_data_for_all_playlists
    await import_playlist_data_for_all_playlists(config)


async def update_epgs(app):
    logger.info("Updating EPGs")
    config = app.config['APP_CONFIG']
    from backend.epgs import import_epg_data_for_all_epgs
    await import_epg_data_for_all_epgs(config)


async def rebuild_custom_epg(app):
    logger.info("Rebuilding custom EPG")
    config = app.config['APP_CONFIG']
    from backend.epgs import update_channel_epg_with_online_data
    await update_channel_epg_with_online_data(config)
    from backend.epgs import build_custom_epg
    await build_custom_epg(config)


async def update_tvh_epg(app):
    logger.info("Triggering update of TVH EPG")
    config = app.config['APP_CONFIG']
    from backend.epgs import run_tvh_epg_grabbers
    await run_tvh_epg_grabbers(config)


async def update_tvh_networks(app):
    logger.info("Updating channels in TVH")
    config = app.config['APP_CONFIG']
    from backend.playlists import publish_playlist_networks
    await publish_playlist_networks(config)


async def update_tvh_channels(app):
    logger.info("Updating channels in TVH")
    config = app.config['APP_CONFIG']
    from backend.channels import publish_bulk_channels_to_tvh_and_m3u
    await publish_bulk_channels_to_tvh_and_m3u(config)


async def update_tvh_muxes(app):
    logger.info("Updating muxes in TVH")
    config = app.config['APP_CONFIG']
    from backend.channels import publish_channel_muxes
    await publish_channel_muxes(config)


async def map_new_tvh_services(app):
    logger.info("Mapping new services in TVH")
    config = app.config['APP_CONFIG']
    # Map any new services
    from backend.channels import map_all_services, cleanup_old_channels
    await map_all_services(config)
    # Clear out old channels
    await cleanup_old_channels(config)
