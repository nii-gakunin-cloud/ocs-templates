# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0

"""
Main entry point for memeid-extractor CLI tool.

This module configures logging and delegates execution to the CLI interface when run as a script or module.
"""

import sys

if __name__ == "__main__":
    from memeid_extractor.cli import memeid_extractor

    sys.exit(memeid_extractor())
