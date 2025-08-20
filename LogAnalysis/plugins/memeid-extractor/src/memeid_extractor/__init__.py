# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0

"""
MemeID Extractor Package.

A CLI tool to extract IDs and metadata from Jupyter Notebooks and Python scripts.
This package provides functionality to process Jupyter notebooks in bulk,
extract meme IDs and related metadata, and output results to CSV files.
"""

from memeid_extractor.__about__ import __version__
from memeid_extractor.extractor import (
    ExtractedCellData,
    ExtractedData,
    ExtractorArgs,
    process_notebooks_once,
)
from memeid_extractor.validator import (
    ValidationError,
    ValidationResult,
    ValidatorArgs,
    display_validation_results,
    validate_extracted_data,
)
from memeid_extractor.watch import WatchArgs, watch_with_full_validation

__all__ = [
    "__version__",
    "ExtractedCellData",
    "ExtractedData",
    "ExtractorArgs",
    "ValidatorArgs",
    "ValidationError",
    "ValidationResult",
    "WatchArgs",
    "process_notebooks_once",
    "validate_extracted_data",
    "display_validation_results",
    "watch_with_full_validation",
]
