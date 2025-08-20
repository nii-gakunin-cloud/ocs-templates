# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0
"""
CLI entry point for memeid_extractor.

This module provides the main command-line interface entry point for extracting meme IDs
from Jupyter notebooks and writing them to a CSV file.
"""

from logging import basicConfig
from os import getenv

from memeid_extractor.cli.parser import (
    namespace_to_extractor_args,
    namespace_to_validator_args,
    namespace_to_watch_args,
    parse_args,
)
from memeid_extractor.extractor import process_notebooks_once
from memeid_extractor.watch import watch_with_full_validation

basicConfig(
    level=getenv("LOG_LEVEL", "INFO"),
    format=getenv("LOG_FORMAT", "%(message)s"),
)


def memeid_extractor() -> int:
    """
    Main entry point for the memeid_extractor CLI.

    Uses the new architecture: extract data -> validate -> write CSV.
    This ensures proper validation before CSV generation and fixes strict_mode behavior.

    Returns:
        int: Exit code (0=success, 1=failure).
    """
    args = parse_args()
    extractor_args = namespace_to_extractor_args(args)
    validator_args = namespace_to_validator_args(args)

    if args.watch:
        # Start watching mode
        watch_args = namespace_to_watch_args(args)
        watch_with_full_validation(watch_args, extractor_args, validator_args)
        return 0

    # Process notebooks once
    return process_notebooks_once(extractor_args, validator_args)
