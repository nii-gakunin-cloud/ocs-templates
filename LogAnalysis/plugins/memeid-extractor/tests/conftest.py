# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-docstring
import json
from pathlib import Path

import nbformat
import pytest

from memeid_extractor.extractor import ExtractorArgs
from memeid_extractor.watch import WatchArgs


@pytest.fixture
def sample_notebook() -> nbformat.NotebookNode:
    nb_data = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Question 1\n", "This is a test question."],
                "metadata": {},
            },
            {
                "cell_type": "code",
                "source": ["print('hello world')\n", "x = 1 + 1"],
                "metadata": {"lc_cell_meme": {"current": "test-cell-meme-id-123-456"}},
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "source": [],
                "metadata": {},
                "execution_count": None,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "source": ["y = 2 * 3"],
                "metadata": {"lc_cell_meme": {"current": "test-cell-meme-id-789-012"}},
                "execution_count": None,
                "outputs": [],
            },
        ],
        "metadata": {"lc_notebook_meme": {"current": "notebook-meme-id-abc-def"}},
    }
    return nbformat.reads(json.dumps(nb_data), as_version=nbformat.NO_CONVERT)


@pytest.fixture
def sample_extractor_args() -> ExtractorArgs:
    return ExtractorArgs(
        notebook_path=Path("/test/notebooks"),
        csv_file=Path("test.csv"),
        include="*.ipynb",
        format="{:02}-{:03}",
        hold_branch_number=False,
        absolute_path=False,
        course_server=False,
    )


@pytest.fixture
def sample_watch_args() -> WatchArgs:
    return WatchArgs(
        notebook_path=Path("/test/notebooks"),
        include="*.ipynb",
        delay=1,
    )
