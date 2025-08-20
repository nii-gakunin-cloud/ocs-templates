# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0
"""
MemeID Extractor Core Module.

This module provides internal functions for extracting meme IDs and related information from Jupyter
notebooks and writing them to a CSV file. It supports filtering, pattern extraction, and branch
number handling. All functions except write_meme_csv are intended for internal use.
"""

import re
from csv import DictWriter
from datetime import UTC, datetime
from logging import getLogger
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import nbformat

from memeid_extractor.validator import ValidatorArgs, display_validation_results, validate_extracted_data

logger = getLogger(__name__)


class CellInfo(TypedDict):
    """Information extracted from a notebook cell."""

    cell_meme: str
    code: str
    markdown: str | None


class ExtractedCellData(TypedDict):
    """Information extracted from a single cell with all metadata."""

    qno: str
    lc_cell_meme: str | None
    lc_notebook_meme: str | None
    textbook_path: str
    code: str
    qlabel: NotRequired[str]
    course_server: NotRequired[str]
    source_info: dict[str, Any]


class ExtractedData(TypedDict):
    """Complete extracted data from notebook processing."""

    cells: list[ExtractedCellData]
    metadata: dict[str, Any]
    extraction_args: "ExtractorArgs"


class ExtractorArgs(TypedDict):
    """Arguments for extractor functions."""

    notebook_path: Path
    csv_file: Path
    include: str
    exclude: NotRequired[str]
    pattern: NotRequired[re.Pattern]
    format: str
    hold_branch_number: bool
    absolute_path: bool
    course_server: NotRequired[bool]
    sort_order: NotRequired[str]


def _sort_notebook_paths(notebook_paths: list[Path], sort_order: str) -> list[Path]:
    """
    Sort notebook paths according to the specified order.

    Args:
        notebook_paths (list[Path]): List of notebook paths to sort.
        sort_order (str): Sort order - "mtime", "ctime", or "name".

    Returns:
        list[Path]: Sorted list of notebook paths.

    Raises:
        ValueError: If sort_order is not one of the valid options.
    """
    match sort_order:
        case "mtime":
            return sorted(notebook_paths, key=lambda p: p.stat().st_mtime)
        case "ctime":
            return sorted(notebook_paths, key=lambda p: p.stat().st_ctime)
        case "name":
            return sorted(notebook_paths)
        case _:
            msg = f"Invalid sort_order: {sort_order}. Must be 'mtime', 'ctime', or 'name'."
            raise ValueError(msg)


def _extract_data_from_notebooks(args: ExtractorArgs) -> ExtractedData:
    """
    Extract meme IDs and related information from multiple Jupyter notebooks.

    This function processes notebooks in the specified directory and returns the extracted data
    without generating any CSV files. The data can be validated and then written to CSV separately.

    Args:
        args (ExtractorArgs): Arguments containing notebook directory, include/exclude patterns,
                             and other extraction settings.

    Returns:
        ExtractedData: All extracted cell data with metadata and extraction arguments.
    """
    cells: list[ExtractedCellData] = []
    nb_path = args["notebook_path"]
    exclude_paths = set(nb_path.glob(ex)) if (ex := args.get("exclude")) else set()
    notebook_paths = _sort_notebook_paths(list(nb_path.glob(args["include"])), args.get("sort_order", "ctime"))

    total_notebooks = len(notebook_paths)
    processed_notebooks = 0

    for notebook_index, notebook_path in enumerate(notebook_paths):
        if notebook_path in exclude_paths:
            continue

        try:
            notebook, nb_meme = _load_notebook(notebook_path)
            textbook_path = (
                notebook_path.resolve() if args["absolute_path"] else notebook_path.relative_to(args["notebook_path"])
            )

            for cell_index, cell_info in enumerate(_extract_cells(notebook)):
                cell_data = _generate_extracted_cell_data(
                    cell_info=cell_info,
                    cell_index=cell_index,
                    notebook_index=notebook_index,
                    textbook_path=textbook_path,
                    notebook_meme=nb_meme,
                    notebook_path=notebook_path,
                    args=args,
                )
                cells.append(cell_data)

            processed_notebooks += 1
        except (nbformat.ValidationError, ValueError, OSError) as e:
            logger.warning("Error processing %s: %s", notebook_path, e)

    metadata = {
        "total_notebooks": total_notebooks,
        "processed_notebooks": processed_notebooks,
        "total_cells": len(cells),
        "extraction_timestamp": _get_current_timestamp(),
    }

    return ExtractedData(cells=cells, metadata=metadata, extraction_args=args)


def _write_csv_from_extracted_data(data: ExtractedData, csv_file: Path) -> None:
    """
    Write extracted data to a CSV file.

    This function takes already extracted and validated data and writes it to a CSV file,
    separated from the extraction logic for better architecture.

    Args:
        data (ExtractedData): Extracted data containing cells and metadata.
        csv_file (Path): Output CSV file path.
    """
    if not data["cells"]:
        logger.info("No cells found in extracted data, creating empty CSV file")
        fieldnames = _get_fieldnames_from_data(data)
        try:
            with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
                writer = DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        except OSError:
            logger.exception("Error writing to %s", csv_file)
        return

    # Get fieldnames from the first cell data
    fieldnames = _get_fieldnames_from_data(data)

    try:
        with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
            writer = DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for cell_data in data["cells"]:
                # Convert ExtractedCellData to CSV row dict (exclude source_info)
                csv_row = {key: value for key, value in cell_data.items() if key != "source_info"}
                # Handle None values
                for key, value in csv_row.items():
                    if value is None:
                        csv_row[key] = ""
                writer.writerow(csv_row)

        logger.info("Successfully wrote %d rows to %s", len(data["cells"]), csv_file)
    except OSError:
        logger.exception("Error writing to %s", csv_file)


def process_notebooks_once(
    extractor_args: ExtractorArgs,
    validator_args: ValidatorArgs,
) -> int:
    """
    Process notebooks once with optional validation.

    Extracts data from notebooks, validates if enabled, and writes CSV.
    This function provides a complete workflow for processing notebooks with validation.

    Validation behavior:
    - If validation is disabled: Always succeeds (exit code 0)
    - If validation is enabled and passes: Succeeds (exit code 0)
    - If validation is enabled and fails:
      * strict_mode=True: Aborts CSV generation, returns exit code 1
      * strict_mode=False: Continues CSV generation, returns exit code 1

    Args:
        extractor_args (ExtractorArgs): Extraction arguments.
        validator_args (ValidatorArgs): Validation arguments including enabled flag and strict mode.

    Returns:
        int: Exit code (0=success, 1=validation failure when validation is enabled).
    """

    # Phase 1: Extract data from notebooks (no CSV generation yet)
    extracted_data = _extract_data_from_notebooks(extractor_args)

    # Phase 2: Validate extracted data if enabled
    validation_failed = False
    if validator_args["enabled"]:
        validation_result = validate_extracted_data(extracted_data)
        display_validation_results(validation_result, display_mode=validator_args.get("display_mode", "normal"))
        validation_failed = not validation_result["is_valid"]

        # Handle strict mode: abort CSV generation if validation fails
        if validator_args["strict_mode"] and validation_failed:
            logger.error("Validation failed in strict mode. CSV generation aborted.")
            return 1

    # Phase 3: Generate CSV from validated data (always generate unless strict mode failed)
    _write_csv_from_extracted_data(extracted_data, extractor_args["csv_file"])

    # Return error code if validation was enabled and failed
    if validator_args["enabled"] and validation_failed:
        return 1

    return 0


def _get_fieldnames_from_data(data: ExtractedData) -> list[str]:
    """
    Get CSV fieldnames from extracted data structure.

    Examines the extracted data to determine which optional fields are present
    and returns the appropriate fieldname list for CSV output.

    Args:
        data (ExtractedData): Extracted data containing cells and metadata.

    Returns:
        list[str]: List of fieldnames for the CSV file.
    """
    fieldnames = ["qno", "lc_cell_meme", "lc_notebook_meme", "textbook_path"]

    # Check if any cell has course_server field
    has_course_server = any("course_server" in cell for cell in data["cells"])
    if has_course_server:
        fieldnames.append("course_server")

    fieldnames.append("code")

    # Check if any cell has qlabel field
    has_qlabel = any("qlabel" in cell for cell in data["cells"])
    if has_qlabel:
        fieldnames.insert(1, "qlabel")

    return fieldnames


def _extract_cells(notebook: nbformat.NotebookNode) -> list[CellInfo]:
    """
    Extract meme ID, code, and preceding markdown from code cells in a notebook.

    Only code cells with a 'lc_cell_meme' metadata entry are included. The preceding markdown cell's
    content is attached to each code cell if present.

    Args:
        notebook (nbformat.NotebookNode): Loaded notebook as a NotebookNode.

    Returns:
        list[CellInfo]: List of dictionaries containing cell information.
    """
    ret: list[CellInfo] = []
    prev_markdown: str | None = None

    for cell in notebook.cells:
        if not cell.source:  # More pythonic empty check
            continue

        match cell.cell_type:
            case "markdown":
                prev_markdown = cell.source
            case "code":
                try:
                    cell_meme = cell.metadata.lc_cell_meme.current
                    ret.append(CellInfo(cell_meme=cell_meme, code=cell.source, markdown=prev_markdown))
                except AttributeError:
                    logger.warning("Missing 'lc_cell_meme' metadata in code cell: %s", cell.source[:100])
                finally:
                    prev_markdown = None
            case _:  # pragma: no cover
                logger.warning("Unsupported cell type '%s' in notebook", cell.cell_type)

    return ret


def _load_notebook(notebook_path: Path) -> tuple[nbformat.NotebookNode, str | None]:
    """
    Load a Jupyter notebook from a file and extract its notebook-level meme ID.

    Args:
        notebook_path (Path): Path to the Jupyter notebook file.

    Returns:
        tuple[nbformat.NotebookNode, str | None]: Tuple of the loaded notebook and its meme ID (or None).
    """
    notebook = nbformat.read(notebook_path, as_version=nbformat.NO_CONVERT)
    try:
        meme_id = notebook.metadata.lc_notebook_meme.current
    except AttributeError:
        logger.warning("No meme ID found in notebook metadata: %s", notebook_path)
        meme_id = None

    return notebook, meme_id


def _extract_course_server(textbook_path: Path, notebook_path: Path) -> str:
    """
    Extract course server name from textbook path.

    For relative paths, use the first directory component directly.
    For absolute paths, compute relative path from notebook_path first.

    Args:
        textbook_path: The path to the notebook file (relative or absolute).
        notebook_path: The base notebook directory path.

    Returns:
        str: Course server name (first directory component) or empty string.
    """
    if textbook_path.is_absolute():
        try:
            relative_path = textbook_path.relative_to(notebook_path)
            return relative_path.parts[0] if len(relative_path.parts) > 1 else ""
        except ValueError:
            logger.warning("Cannot compute relative path for %s from %s", textbook_path, notebook_path)
            return ""
    else:
        return textbook_path.parts[0] if len(textbook_path.parts) > 1 else ""


def _generate_extracted_cell_data(
    cell_info: CellInfo,
    cell_index: int,
    notebook_index: int,
    textbook_path: Path,
    notebook_meme: str | None,
    notebook_path: Path,
    args: ExtractorArgs,
) -> ExtractedCellData:
    """
    Generate ExtractedCellData for a single cell.

    Args:
        cell_info (CellInfo): Information about the cell.
        cell_index (int): Index of the cell within the notebook.
        notebook_index (int): Index of the notebook in processing order.
        textbook_path (Path): Path to the notebook file.
        notebook_meme (str | None): Notebook-level meme ID.
        notebook_path (Path): Full path to the notebook file.
        args (ExtractorArgs): Extraction arguments.

    Returns:
        ExtractedCellData: Complete cell data with all metadata.
    """
    cell_meme = cell_info["cell_meme"]
    if not args["hold_branch_number"] and cell_meme:
        cell_meme = _remove_branch_number(cell_meme)

    textbook_path_str = str(textbook_path)

    cell_data = ExtractedCellData(
        qno=args["format"].format(notebook_index, cell_index),
        lc_cell_meme=cell_meme,
        lc_notebook_meme=notebook_meme,
        textbook_path=textbook_path_str,
        code=cell_info["code"],
        source_info={
            "notebook_path": str(notebook_path),
            "cell_index": cell_index,
            "notebook_index": notebook_index,
            "has_markdown": cell_info["markdown"] is not None,
        },
    )

    # Add optional fields
    if args.get("course_server", False):
        course_server = _extract_course_server(textbook_path, args["notebook_path"])
        cell_data["course_server"] = course_server

    if (pat := args.get("pattern")) and cell_info["markdown"] and (m := re.search(pat, cell_info["markdown"])):
        cell_data["qlabel"] = m.group(0)

    return cell_data


def _get_current_timestamp() -> str:
    """
    Get current timestamp for metadata.

    Returns:
        str: Current timestamp in ISO format.
    """

    return datetime.now(UTC).isoformat()


def _remove_branch_number(meme_id: str) -> str:
    """
    Remove the branch number suffix from a meme ID if present.

    The branch number is defined as the last two hyphen-separated segments of the ID. If the meme ID
    does not contain a branch number, it is returned unchanged.

    Args:
        meme_id (str): Meme ID string.

    Returns:
        str: Meme ID without the branch number suffix.
    """
    if not meme_id or "-" not in meme_id:
        return meme_id
    return "-".join(meme_id.split("-")[0:5])
