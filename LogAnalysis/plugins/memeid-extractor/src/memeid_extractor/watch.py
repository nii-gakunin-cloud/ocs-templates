# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0
"""
File system watcher and CSV update utilities for memeid_extractor.

This module provides utilities for monitoring a directory of Jupyter notebooks and automatically
updating a meme ID CSV file in response to file system events or signals. The main public function
is watch_notebooks, which sets up file watching and triggers CSV updates. Internal helpers handle
signal registration, event processing, and CSV writing.
"""

from logging import getLogger
from pathlib import Path
from signal import SIGINT, SIGTERM, SIGUSR1, signal
from threading import Event, Thread
from time import sleep
from typing import NoReturn, TypedDict

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    PatternMatchingEventHandler,
)
from watchdog.observers import Observer
from watchdog.observers.api import EventQueue

from memeid_extractor.extractor import ExtractorArgs, process_notebooks_once
from memeid_extractor.validator import ValidatorArgs

logger = getLogger(__name__)


class WatchArgs(TypedDict):
    """
    Typed dictionary for arguments required by watch functions.

    Attributes:
        notebook_path (Path): Path to the directory containing notebooks to watch.
        include (str): Glob pattern for files to include.
        delay (int): Delay in seconds between CSV updates after an event.
    """

    notebook_path: Path
    include: str
    delay: int


class EventHandler(PatternMatchingEventHandler):
    """
    Event handler for monitoring file system changes and triggering CSV updates.
    """

    def __init__(self, que: EventQueue, pattern: str):
        """
        Initialize the event handler with a queue and file pattern.

        Args:
            que (EventQueue): Queue to put events into.
            pattern (str): Pattern to match files for monitoring.
        """
        super().__init__(patterns=[pattern], ignore_directories=True)
        self._que = que

    def on_any_event(self, event: FileSystemEvent) -> None:
        """
        Handle any file system event and enqueue a CSV update if relevant.

        Args:
            event (FileSystemEvent): The file system event.
        """
        logger.debug("Event: %s", event)
        if event.event_type in [
            FileCreatedEvent.event_type,
            FileDeletedEvent.event_type,
            FileModifiedEvent.event_type,
            FileMovedEvent.event_type,
        ]:
            self._que.put("run")


def _setup_signal_handler(que: EventQueue, ev: Event) -> None:
    """
    Set up signal handlers for the event queue and shutdown event.

    Registers handlers for SIGINT, SIGTERM (to stop the watcher), and SIGUSR1 (to force CSV update).

    Args:
        que (EventQueue): Queue to put events into.
        ev (Event): Event to set when a signal is received.
    """

    def stop_loop(sig, _frame):
        logger.debug("Received signal %s", sig)
        ev.set()

    def force_update_handler(_sig, _frame):
        logger.debug("Forcing CSV update")
        que.put("run")

    signal(SIGINT, stop_loop)
    signal(SIGTERM, stop_loop)
    signal(SIGUSR1, force_update_handler)


def _update_csv(
    que: EventQueue,
    extractor_args: ExtractorArgs,
    delay: int,
    validator_args: ValidatorArgs,
) -> NoReturn:
    """
    Continuously update the CSV file based on events in the queue.

    Waits for events in the queue, then triggers CSV writing after a delay using the new
    validation-integrated architecture. Handles errors and logs exceptions. Runs indefinitely until interrupted.

    Args:
        que (EventQueue): Queue containing events that trigger CSV updates.
        extractor_args (ExtractorArgs): Extractor arguments for CSV generation.
        delay (int): Delay in seconds between updates.
        validator_args (ValidatorArgs): Validation arguments including enabled flag and strict mode.
    """
    while True:
        if que.empty():
            sleep(1)
            continue
        sleep(delay)
        que.get()
        try:
            logger.info("Updating CSV: %s", extractor_args["csv_file"])
            exit_code = process_notebooks_once(extractor_args, validator_args)
            if exit_code == 0:
                logger.debug("CSV update completed successfully")
            else:
                logger.warning("CSV update completed with validation warnings")
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error updating CSV")
        que.task_done()


def _watch_notebooks(
    watch_args: WatchArgs,
    extractor_args: ExtractorArgs,
    validator_args: ValidatorArgs,
) -> None:
    """
    Watch a directory for changes and update the CSV file accordingly.

    Sets up file system monitoring for the specified directory and pattern. On relevant file events
    or signals, triggers CSV updates using the provided extractor arguments with validation integration.

    Args:
        watch_args (WatchArgs): Watch-specific arguments (directory, pattern, delay).
        extractor_args (ExtractorArgs): Extractor arguments for CSV generation.
        validator_args (ValidatorArgs): Validation arguments including enabled flag and strict mode.
    """
    que = EventQueue()
    ev = Event()
    _setup_signal_handler(que, ev)

    Thread(target=_update_csv, args=(que, extractor_args, watch_args["delay"], validator_args), daemon=True).start()
    handler = EventHandler(que, Path(watch_args["include"]).name)
    observer = Observer()
    observer.schedule(handler, str(watch_args["notebook_path"]), recursive="**" in watch_args["include"])
    observer.start()
    logger.info("Started watching directory: %s", watch_args["notebook_path"])
    try:
        while observer.is_alive() and not ev.is_set():
            ev.wait(1)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Error while watching directory")
    finally:
        observer.stop()
        observer.join()
        que.join()
        logger.info("Stopped watching directory: %s", watch_args["notebook_path"])


def watch_with_full_validation(
    watch_args: WatchArgs, extractor_args: ExtractorArgs, validator_args: ValidatorArgs
) -> None:
    """
    Watch notebooks with full validation support.

    This function integrates the new validation architecture with watch mode.
    Both initial generation and file change events use the same validation workflow.

    Args:
        watch_args (WatchArgs): Watch arguments.
        extractor_args (ExtractorArgs): Extractor arguments.
        validator_args (ValidatorArgs): Validation arguments including enabled flag and strict mode.
    """
    logger.info("Starting watch mode with validation integration")

    # Perform initial CSV generation with validation
    logger.info("Performing initial CSV generation...")
    exit_code = process_notebooks_once(extractor_args, validator_args)

    if exit_code == 0:
        logger.info("Initial CSV generation completed successfully")
    else:
        logger.warning("Initial CSV generation completed with validation warnings")
        if validator_args["strict_mode"]:
            logger.info("Continuing watch mode despite strict validation failure")

    # Start file system watching with validation integration
    logger.info("Starting file system watching with validation support")
    _watch_notebooks(watch_args, extractor_args, validator_args)
