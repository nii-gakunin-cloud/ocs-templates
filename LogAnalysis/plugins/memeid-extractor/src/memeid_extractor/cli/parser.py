# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0
"""
CLI argument parsing and conversion utilities for memeid_extractor.

This module provides functions for parsing command line arguments and converting them
to typed dictionaries used by various components of the memeid_extractor.
"""

import re
from argparse import ArgumentParser, Namespace
from logging import getLogger
from os import getenv
from pathlib import Path

from memeid_extractor.__about__ import __version__
from memeid_extractor.extractor import ExtractorArgs
from memeid_extractor.validator import ValidatorArgs
from memeid_extractor.watch import WatchArgs

logger = getLogger(__name__)


def parse_args() -> Namespace:
    """
    Parse command line arguments for memeid_extractor CLI.

    Returns:
        Namespace: Parsed command line arguments with all options for extraction and watching.
    """
    parser = ArgumentParser(description="Extract meme IDs from Jupyter notebooks and write to a CSV file.")
    parser.add_argument(
        "-n",
        "--notebook-path",
        default=getenv("NB_PATH", "/jupyter/admin/textbook"),
        help="Path to the Jupyter notebook directory (default: /jupyter/admin/textbook)",
    )
    parser.add_argument(
        "-o",
        "--csv-file",
        default=getenv("MEME_CSV_FILE", "meme.csv"),
        help="Output CSV file name (default: meme.csv)",
    )
    parser.add_argument(
        "-I",
        "--include",
        default="**/*.ipynb",
        help="Include pattern for notebook files (default: '**/*.ipynb')",
    )
    parser.add_argument(
        "-X",
        "--exclude",
        help="Exclude pattern for notebook files",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default=getenv("QLABEL_PATTERN"),
        help="Pattern for extracting question labels from markdown cell",
    )
    parser.add_argument(
        "-F",
        "--format",
        default=getenv("QNO_FORMAT", "{:02}-{:03}"),
        help="Format string for question numbers (default: '{:02}-{:03}')",
    )
    parser.add_argument(
        "-B",
        "--hold-branch-number",
        action="store_true",
        help="Holds the branch number of the meme ID (default: False)",
    )
    parser.add_argument(
        "-A",
        "--absolute-path",
        action="store_true",
        help="Output the absolute path of the textbook (default: False)",
    )
    parser.add_argument(
        "-C",
        "--course-server",
        action="store_true",
        default=getenv("COURSE_SERVER", "false").lower() in ("true", "1", "yes"),
        help="Include course_server column in CSV output (default: False)",
    )
    parser.add_argument(
        "-S",
        "--sort-order",
        choices=["mtime", "ctime", "name"],
        default="ctime",
        help="Sort order for processing notebook files (default: ctime)",
    )
    parser.add_argument(
        "-d",
        "--delay",
        default=10,
        type=int,
        help="Delay in seconds between updates (default: 10)",
    )
    parser.add_argument(
        "-W",
        "--watch",
        action="store_true",
        help="Watch a directory for changes and update the CSV file (default: False)",
    )
    validation_group = parser.add_mutually_exclusive_group()
    validation_group.add_argument(
        "--no-validate",
        action="store_true",
        help="Disable CSV validation (default: validation enabled)",
    )
    validation_group.add_argument(
        "--strict-validate",
        action="store_true",
        help="Enable strict validation mode (stops on first error)",
    )
    display_group = parser.add_mutually_exclusive_group()
    display_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress validation result output",
    )
    display_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed validation results",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the version of the memeid_extractor",
    )
    args = parser.parse_args()
    if args.pattern:
        try:
            args.pattern = re.compile(args.pattern, re.MULTILINE)
        except re.error:
            logger.exception("Invalid regex pattern")
            raise

    return args


def namespace_to_extractor_args(args: Namespace) -> ExtractorArgs:
    """
    Convert Namespace to ExtractorArgs TypedDict.

    Args:
        args (Namespace): Parsed command line arguments.

    Returns:
        ExtractorArgs: Converted extractor arguments.
    """
    ret = ExtractorArgs(
        notebook_path=Path(args.notebook_path),
        csv_file=Path(args.csv_file),
        include=args.include,
        format=args.format,
        hold_branch_number=args.hold_branch_number,
        absolute_path=args.absolute_path,
        course_server=args.course_server,
        sort_order=args.sort_order,
    )
    if args.exclude:
        ret["exclude"] = args.exclude
    if args.pattern:
        ret["pattern"] = args.pattern
    return ret


def namespace_to_watch_args(args: Namespace) -> WatchArgs:
    """
    Convert Namespace to WatchArgs TypedDict.

    Args:
        args (Namespace): Parsed command line arguments.

    Returns:
        WatchArgs: Converted watch arguments.
    """
    return WatchArgs(
        notebook_path=Path(args.notebook_path),
        include=args.include,
        delay=args.delay,
    )


def namespace_to_validator_args(args: Namespace) -> ValidatorArgs:
    """
    Convert Namespace to ValidatorArgs TypedDict.

    Args:
        args (Namespace): Parsed command line arguments.

    Returns:
        ValidatorArgs: Converted validator arguments.
    """
    # Determine display mode from CLI flags
    if args.quiet:
        display_mode = "quiet"
    elif args.verbose:
        display_mode = "verbose"
    else:
        display_mode = "normal"

    return ValidatorArgs(
        csv_file=Path(args.csv_file),
        strict_mode=args.strict_validate,
        enabled=not args.no_validate,
        display_mode=display_mode,
    )
