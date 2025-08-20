# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-docstring
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from memeid_extractor.cli import memeid_extractor
from memeid_extractor.cli.parser import parse_args
from memeid_extractor.extractor import ExtractorArgs
from memeid_extractor.validator import ValidatorArgs
from memeid_extractor.watch import WatchArgs


def test_parse_args_defaults():
    with patch("sys.argv", ["memeid-extractor"]):
        args = parse_args()

        assert args.notebook_path == "/jupyter/admin/textbook"
        assert args.csv_file == "meme.csv"
        assert args.include == "**/*.ipynb"
        assert args.exclude is None
        assert args.pattern is None
        assert args.format == "{:02}-{:03}"
        assert args.hold_branch_number is False
        assert args.absolute_path is False
        assert args.course_server is False
        assert args.delay == 10
        assert args.watch is False


def test_parse_args_custom_values():
    test_args = [
        "memeid-extractor",
        "--notebook-path",
        "/custom/path",
        "--csv-file",
        "custom.csv",
        "--include",
        "*.ipynb",
        "--exclude",
        "exclude_*.ipynb",
        "--pattern",
        r"Question \d+",
        "--format",
        "{:03}-{:04}",
        "--hold-branch-number",
        "--absolute-path",
        "--course-server",
        "--delay",
        "5",
        "--watch",
    ]

    with patch("sys.argv", test_args):
        args = parse_args()

        assert args.notebook_path == "/custom/path"
        assert args.csv_file == "custom.csv"
        assert args.include == "*.ipynb"
        assert args.exclude == "exclude_*.ipynb"
        assert isinstance(args.pattern, re.Pattern)
        assert args.format == "{:03}-{:04}"
        assert args.hold_branch_number is True
        assert args.absolute_path is True
        assert args.course_server is True
        assert args.delay == 5
        assert args.watch is True


def test_parse_args_short_options():
    test_args = [
        "memeid-extractor",
        "-n",
        "/short/path",
        "-o",
        "short.csv",
        "-I",
        "short*.ipynb",
        "-X",
        "exclude*.ipynb",
        "-p",
        r"Q\d+",
        "-F",
        "{:01}-{:02}",
        "-B",
        "-A",
        "-C",
        "-d",
        "3",
        "-W",
    ]

    with patch("sys.argv", test_args):
        args = parse_args()

        assert args.notebook_path == "/short/path"
        assert args.csv_file == "short.csv"
        assert args.include == "short*.ipynb"
        assert args.exclude == "exclude*.ipynb"
        assert isinstance(args.pattern, re.Pattern)
        assert args.format == "{:01}-{:02}"
        assert args.hold_branch_number is True
        assert args.absolute_path is True
        assert args.course_server is True
        assert args.delay == 3
        assert args.watch is True


def test_parse_args_environment_variables():
    env_vars = {
        "NB_PATH": "/env/notebook/path",
        "MEME_CSV_FILE": "env.csv",
        "QLABEL_PATTERN": r"Exercise \d+",
        "QNO_FORMAT": "{:04}-{:05}",
        "COURSE_SERVER": "true",
    }

    with patch("sys.argv", ["memeid-extractor"]), patch.dict("os.environ", env_vars):
        args = parse_args()

        assert args.notebook_path == "/env/notebook/path"
        assert args.csv_file == "env.csv"
        assert isinstance(args.pattern, re.Pattern)
        assert args.format == "{:04}-{:05}"
        assert args.course_server is True


def test_parse_args_invalid_regex():
    test_args = ["memeid-extractor", "--pattern", "[invalid regex"]

    with patch("sys.argv", test_args), pytest.raises(re.error):
        parse_args()


@patch("memeid_extractor.cli.process_notebooks_once")
def test_memeid_extractor_no_watch(mock_process):
    mock_process.return_value = 0

    with patch("sys.argv", ["memeid-extractor"]):
        result = memeid_extractor()
        assert result == 0

        expected_args = ExtractorArgs(
            notebook_path=Path("/jupyter/admin/textbook"),
            csv_file=Path("meme.csv"),
            include="**/*.ipynb",
            format="{:02}-{:03}",
            hold_branch_number=False,
            absolute_path=False,
            course_server=False,
            sort_order="ctime",
        )

        expected_validator_args = ValidatorArgs(
            csv_file=Path("meme.csv"),
            enabled=True,
            strict_mode=False,
            display_mode="normal",
        )
        mock_process.assert_called_once_with(expected_args, expected_validator_args)


@patch("memeid_extractor.cli.watch_with_full_validation")
def test_memeid_extractor_with_watch(mock_watch):
    with patch("sys.argv", ["memeid-extractor", "--watch"]):
        result = memeid_extractor()
        assert result == 0

        expected_extractor_args = ExtractorArgs(
            notebook_path=Path("/jupyter/admin/textbook"),
            csv_file=Path("meme.csv"),
            include="**/*.ipynb",
            format="{:02}-{:03}",
            hold_branch_number=False,
            absolute_path=False,
            course_server=False,
            sort_order="ctime",
        )

        expected_watch_args = WatchArgs(
            notebook_path=Path("/jupyter/admin/textbook"),
            include="**/*.ipynb",
            delay=10,
        )

        assert mock_watch.call_count == 1
        call_args = mock_watch.call_args[0]

        # Check the arguments passed to watch_with_full_validation
        assert call_args[0] == expected_watch_args
        assert call_args[1] == expected_extractor_args
        # Third argument is the validator args - just verify it exists
        assert call_args[2] is not None


def test_parse_args_version():
    with patch("sys.argv", ["memeid-extractor", "--version"]), pytest.raises(SystemExit):
        parse_args()


def test_parse_args_help():
    with patch("sys.argv", ["memeid-extractor", "--help"]), pytest.raises(SystemExit):
        parse_args()


def test_pattern_compilation():
    test_args = ["memeid-extractor", "--pattern", r"Question (\d+)"]

    with patch("sys.argv", test_args):
        args = parse_args()

        # Test that the compiled pattern works
        assert isinstance(args.pattern, re.Pattern)
        match = args.pattern.search("Question 5: What is the answer?")
        assert match is not None
        assert match.group(0) == "Question 5"


def test_pattern_multiline_flag():
    test_args = ["memeid-extractor", "--pattern", r"^Question \d+"]

    with patch("sys.argv", test_args):
        args = parse_args()

        # Test multiline matching
        text = "Some text\nQuestion 1\nMore text"
        match = args.pattern.search(text)
        assert match is not None
        assert match.group(0) == "Question 1"
