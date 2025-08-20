# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-docstring
import signal
from argparse import Namespace
from contextlib import suppress
from pathlib import Path
from threading import Event
from time import sleep
from unittest.mock import MagicMock, patch

import pytest
from watchdog.events import FileModifiedEvent
from watchdog.observers.api import EventQueue

from memeid_extractor.validator import ValidatorArgs
from memeid_extractor.watch import EventHandler, _setup_signal_handler, _update_csv, _watch_notebooks

pytestmark = pytest.mark.timeout(10)


def test_event_handler_on_any_event():
    que = EventQueue()
    handler = EventHandler(que, "*.ipynb")

    event = FileModifiedEvent("/test/file.ipynb")
    handler.on_any_event(event)

    assert not que.empty()
    assert que.get() == "run"


def test_event_handler_ignores_non_matching_events():
    que = EventQueue()
    handler = EventHandler(que, "*.ipynb")

    # Create a custom event type that's not in the handled list
    class CustomEvent:
        event_type = "custom_event"

    handler.on_any_event(CustomEvent())  # type: ignore

    # Queue should still be empty after a short wait
    sleep(0.1)
    assert que.empty()


@patch("memeid_extractor.watch.process_notebooks_once")
@patch("memeid_extractor.watch.sleep")
def test_update_csv_processes_events(mock_sleep, mock_process, sample_extractor_args) -> None:
    que = EventQueue()

    def side_effect_gen():
        que.put("run")
        yield
        yield
        msg = "Stop iteration"
        raise RuntimeError(msg)

    gen = side_effect_gen()
    mock_sleep.side_effect = lambda x: next(gen)  # noqa: ARG005

    validator_args = ValidatorArgs(csv_file=sample_extractor_args["csv_file"], enabled=True, strict_mode=False)
    with suppress(RuntimeError):
        _update_csv(que, sample_extractor_args, delay=10, validator_args=validator_args)

    mock_process.assert_called_with(sample_extractor_args, validator_args)


@patch("memeid_extractor.watch.process_notebooks_once")
@patch("memeid_extractor.watch.sleep")
def test_update_csv_handles_exception(mock_sleep, mock_process, sample_extractor_args, caplog) -> None:
    que = EventQueue()
    que.put("run")

    def side_effect_gen():
        yield
        msg = "Stop iteration"
        raise RuntimeError(msg)

    gen = side_effect_gen()
    mock_sleep.side_effect = lambda x: next(gen)  # noqa: ARG005
    mock_process.side_effect = Exception("Test error")
    caplog.set_level("ERROR")

    validator_args = ValidatorArgs(csv_file=sample_extractor_args["csv_file"], enabled=True, strict_mode=False)
    with suppress(RuntimeError):
        _update_csv(que, sample_extractor_args, delay=10, validator_args=validator_args)

    assert "Error updating CSV" in caplog.text


@patch("memeid_extractor.watch.signal")
def test_setup_signal_handler(mock_signal):
    que = EventQueue()
    ev = Event()

    _setup_signal_handler(que, ev)

    # Verify that signal handlers were set up
    assert mock_signal.call_count == 3

    # Test the signal handlers
    calls = mock_signal.call_args_list

    # Find the SIGUSR1 handler call
    sigusr1_handler = None
    sigint_handler = None
    for call in calls:
        match call[0][0]:
            case signal.SIGUSR1:
                sigusr1_handler = call[0][1]
            case signal.SIGINT:
                sigint_handler = call[0][1]

    assert sigusr1_handler is not None
    assert sigint_handler is not None

    # Test SIGUSR1 handler (force update)
    sigusr1_handler(signal.SIGUSR1, None)
    assert not que.empty()
    assert que.get() == "run"

    # Test SIGINT and SIGTERM handlers (stop loop)
    sigint_handler(signal.SIGINT, None)
    assert ev.is_set()


@patch("memeid_extractor.watch.Observer")
@patch("memeid_extractor.watch.Thread")
@patch("memeid_extractor.watch._setup_signal_handler")
def test__watch_notebooks(mock_setup, mock_thread, mock_observer_class, sample_watch_args, sample_extractor_args):
    mock_observer = MagicMock()
    mock_observer.is_alive.side_effect = [True, False]  # Simulate observer running once
    mock_observer_class.return_value = mock_observer

    validator_args = ValidatorArgs(csv_file=sample_extractor_args["csv_file"], enabled=True, strict_mode=False)
    _watch_notebooks(sample_watch_args, sample_extractor_args, validator_args)

    mock_setup.assert_called_once()

    # Verify observer was set up correctly
    mock_observer.schedule.assert_called_once()
    mock_observer.start.assert_called_once()
    mock_observer.stop.assert_called_once()
    mock_observer.join.assert_called_once()

    # Verify thread was started
    mock_thread.assert_called_once()
    thread_args = mock_thread.call_args[1]
    assert thread_args["daemon"] is True


@patch("memeid_extractor.watch.Observer")
@patch("memeid_extractor.watch.Thread")
@patch("memeid_extractor.watch._setup_signal_handler")
def test__watch_notebooks_handles_exception(
    mock_setup, mock_thread, mock_observer_class, sample_watch_args, sample_extractor_args, caplog
):
    mock_observer = MagicMock()
    mock_observer.is_alive.side_effect = Exception("Test error")
    mock_observer_class.return_value = mock_observer

    caplog.set_level("ERROR")

    validator_args = ValidatorArgs(csv_file=sample_extractor_args["csv_file"], enabled=True, strict_mode=False)
    _watch_notebooks(sample_watch_args, sample_extractor_args, validator_args)

    mock_setup.assert_called_once()
    mock_thread.assert_called_once()

    assert "Error while watching directory" in caplog.text
    mock_observer.stop.assert_called_once()
    mock_observer.join.assert_called_once()


def test_event_handler_with_recursive_pattern():
    que = EventQueue()

    # Test with recursive pattern
    args_recursive = Namespace(include="**/*.ipynb", notebook_path="/test")

    handler = EventHandler(que, Path(args_recursive.include).name)

    # The pattern should be just the filename part
    assert handler.patterns == ["*.ipynb"]
