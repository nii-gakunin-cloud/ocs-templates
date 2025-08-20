# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=missing-docstring, protected-access
# ruff: noqa: SLF001
import json
import logging
from pathlib import Path

import nbformat
import pytest

from memeid_extractor import extractor
from memeid_extractor.extractor import CellInfo


def test_extract_cells(sample_notebook: nbformat.NotebookNode) -> None:
    result = extractor._extract_cells(sample_notebook)

    expected = [
        CellInfo(
            cell_meme="test-cell-meme-id-123-456",
            code="print('hello world')\nx = 1 + 1",
            markdown="# Question 1\nThis is a test question.",
        ),
        CellInfo(cell_meme="test-cell-meme-id-789-012", code="y = 2 * 3", markdown=None),
    ]

    assert result == expected


def test_extract_cells_empty_source() -> None:
    notebook = nbformat.reads(
        json.dumps(
            {
                "nbformat": 4,
                "nbformat_minor": 4,
                "cells": [
                    {
                        "cell_type": "code",
                        "source": [],
                        "metadata": {"lc_cell_meme": {"current": "test-id"}},
                        "execution_count": None,
                        "outputs": [],
                    }
                ],
                "metadata": {},
            }
        ),
        as_version=nbformat.NO_CONVERT,
    )

    result = extractor._extract_cells(notebook)
    assert not result


def test_extract_cells_non_code_cell() -> None:
    """Test that non-code cells are ignored by extract_cells."""
    notebook = nbformat.reads(
        json.dumps(
            {
                "nbformat": 4,
                "nbformat_minor": 4,
                "cells": [{"cell_type": "markdown", "source": ["# md"], "metadata": {}}],
                "metadata": {},
            }
        ),
        as_version=nbformat.NO_CONVERT,
    )
    result = extractor._extract_cells(notebook)
    assert not result


def test_extract_cells_no_lc_cell_meme() -> None:
    """Test that code cells without lc_cell_meme are ignored."""
    notebook = nbformat.reads(
        json.dumps(
            {
                "nbformat": 4,
                "nbformat_minor": 4,
                "cells": [
                    {
                        "cell_type": "code",
                        "source": ["print('x')"],
                        "metadata": {},
                        "execution_count": None,
                        "outputs": [],
                    }
                ],
                "metadata": {},
            }
        ),
        as_version=nbformat.NO_CONVERT,
    )
    result = extractor._extract_cells(notebook)
    assert not result


def test_load_notebook(tmp_path, sample_notebook: dict) -> None:
    notebook_file = tmp_path / "test.ipynb"
    with open(notebook_file, "w", encoding="utf-8") as f:
        json.dump(sample_notebook, f)

    notebook, meme_id = extractor._load_notebook(notebook_file)

    assert isinstance(notebook, nbformat.NotebookNode)
    assert meme_id == "notebook-meme-id-abc-def"


def test_load_notebook_no_meme_id(tmp_path) -> None:
    notebook_data: dict = {"nbformat": 4, "nbformat_minor": 4, "cells": [], "metadata": {}}
    notebook_file = tmp_path / "test.ipynb"
    with open(notebook_file, "w", encoding="utf-8") as f:
        json.dump(notebook_data, f)
    notebook, meme_id = extractor._load_notebook(notebook_file)
    assert isinstance(notebook, nbformat.NotebookNode)
    assert meme_id is None


def test_load_notebook_file_not_found() -> None:
    """Test that load_notebook raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        extractor._load_notebook(Path("/no/such/file.ipynb"))


def test_remove_branch_number() -> None:
    meme_id = "test-cell-meme-id-123-456-789"
    result = extractor._remove_branch_number(meme_id)
    expected = "test-cell-meme-id-123"

    assert result == expected


def test_remove_branch_number_short_id() -> None:
    meme_id = "test-cell-meme-id"
    result = extractor._remove_branch_number(meme_id)
    expected = "test-cell-meme-id"

    assert result == expected


@pytest.mark.parametrize(
    ("meme_id", "expected"),
    [
        ("", ""),
        (None, None),  # type: ignore
    ],
)
def test_remove_branch_number_none_or_empty(meme_id: str, expected: str) -> None:
    """Test remove_branch_number with None and empty string."""
    assert extractor._remove_branch_number(meme_id) == expected


def test_extract_course_server_relative_path_with_subdirs() -> None:
    """Test _extract_course_server with relative path containing subdirectories."""
    textbook_path = Path("course1/chapter1/test.ipynb")
    notebook_path = Path("/notebooks")

    result = extractor._extract_course_server(textbook_path, notebook_path)

    assert result == "course1"


def test_extract_course_server_relative_path_no_subdirs() -> None:
    """Test _extract_course_server with relative path without subdirectories."""
    textbook_path = Path("test.ipynb")
    notebook_path = Path("/notebooks")

    result = extractor._extract_course_server(textbook_path, notebook_path)

    assert result == ""


def test_extract_course_server_absolute_path_within_notebook() -> None:
    """Test _extract_course_server with absolute path within notebook directory."""
    textbook_path = Path("/notebooks/course1/chapter1/test.ipynb")
    notebook_path = Path("/notebooks")

    result = extractor._extract_course_server(textbook_path, notebook_path)

    assert result == "course1"


def test_extract_course_server_absolute_path_no_subdirs() -> None:
    """Test _extract_course_server with absolute path without subdirectories."""
    textbook_path = Path("/notebooks/test.ipynb")
    notebook_path = Path("/notebooks")

    result = extractor._extract_course_server(textbook_path, notebook_path)

    assert result == ""


def test_extract_course_server_absolute_path_outside_notebook() -> None:
    """Test _extract_course_server with absolute path outside notebook directory."""
    textbook_path = Path("/other/course1/test.ipynb")
    notebook_path = Path("/notebooks")

    result = extractor._extract_course_server(textbook_path, notebook_path)

    assert result == ""


def test_extract_course_server_multiple_levels() -> None:
    """Test _extract_course_server with multiple directory levels."""
    textbook_path = Path("server1/course2/chapter3/section4/test.ipynb")
    notebook_path = Path("/notebooks")

    result = extractor._extract_course_server(textbook_path, notebook_path)

    assert result == "server1"


def test_extract_course_server_absolute_path_outside_notebook_logs_warning(caplog) -> None:
    """Test _extract_course_server logs warning when absolute path is outside notebook directory."""

    textbook_path = Path("/other/course1/test.ipynb")
    notebook_path = Path("/notebooks")

    with caplog.at_level(logging.WARNING, logger="memeid_extractor.extractor"):
        result = extractor._extract_course_server(textbook_path, notebook_path)

    assert result == ""
    assert any(
        record.levelno == logging.WARNING and "Cannot compute relative path" in record.getMessage()
        for record in caplog.records
    )
    assert "/other/course1/test.ipynb" in caplog.text
    assert "/notebooks" in caplog.text


def test_sort_notebook_paths_by_name(tmp_path):
    """Test _sort_notebook_paths with name sorting."""
    # Create test files with specific names
    file_c = tmp_path / "c_notebook.ipynb"
    file_a = tmp_path / "a_notebook.ipynb"
    file_b = tmp_path / "b_notebook.ipynb"

    for file in [file_c, file_a, file_b]:
        file.write_text("{}")

    paths = [file_c, file_a, file_b]
    result = extractor._sort_notebook_paths(paths, "name")

    assert result == [file_a, file_b, file_c]


def test_sort_notebook_paths_by_mtime(tmp_path):
    """Test _sort_notebook_paths with modification time sorting."""
    import time

    # Create test files with different modification times
    file1 = tmp_path / "file1.ipynb"
    file2 = tmp_path / "file2.ipynb"
    file3 = tmp_path / "file3.ipynb"

    file1.write_text("{}")
    time.sleep(0.01)  # Small delay to ensure different timestamps
    file2.write_text("{}")
    time.sleep(0.01)
    file3.write_text("{}")

    paths = [file3, file1, file2]
    result = extractor._sort_notebook_paths(paths, "mtime")

    # Should be sorted by modification time (oldest first)
    assert result == [file1, file2, file3]


def test_sort_notebook_paths_by_ctime(tmp_path):
    """Test _sort_notebook_paths with creation time sorting."""
    import time

    # Create test files with different creation times
    file1 = tmp_path / "file1.ipynb"
    file2 = tmp_path / "file2.ipynb"
    file3 = tmp_path / "file3.ipynb"

    file1.write_text("{}")
    time.sleep(0.01)  # Small delay to ensure different timestamps
    file2.write_text("{}")
    time.sleep(0.01)
    file3.write_text("{}")

    paths = [file3, file1, file2]
    result = extractor._sort_notebook_paths(paths, "ctime")

    # Should be sorted by creation time (oldest first)
    assert result == [file1, file2, file3]


def test_sort_notebook_paths_invalid_order():
    """Test _sort_notebook_paths raises ValueError for invalid sort order."""
    from pathlib import Path

    paths = [Path("test.ipynb")]

    with pytest.raises(ValueError, match="Invalid sort_order: invalid. Must be 'mtime', 'ctime', or 'name'."):
        extractor._sort_notebook_paths(paths, "invalid")


def test_generate_extracted_cell_data_basic():
    """Test _generate_extracted_cell_data with basic arguments."""
    from pathlib import Path

    cell_info = extractor.CellInfo(cell_meme="cell-123-456-789-abc-def", code="print('hello')", markdown=None)

    args = extractor.ExtractorArgs(
        notebook_path=Path("/notebooks"),
        csv_file=Path("output.csv"),
        include="**/*.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=False,
        absolute_path=False,
    )

    result = extractor._generate_extracted_cell_data(
        cell_info=cell_info,
        cell_index=2,
        notebook_index=1,
        textbook_path=Path("test.ipynb"),
        notebook_meme="notebook-123",
        notebook_path=Path("/notebooks/test.ipynb"),
        args=args,
    )

    assert result["qno"] == "01-002"
    assert result["lc_cell_meme"] == "cell-123-456-789-abc"  # Branch number removed
    assert result["lc_notebook_meme"] == "notebook-123"
    assert result["textbook_path"] == "test.ipynb"
    assert result["code"] == "print('hello')"
    assert "course_server" not in result
    assert "qlabel" not in result


def test_generate_extracted_cell_data_with_course_server():
    """Test _generate_extracted_cell_data with course_server enabled."""
    from pathlib import Path

    cell_info = extractor.CellInfo(cell_meme="cell-123", code="x = 1", markdown=None)

    args = extractor.ExtractorArgs(
        notebook_path=Path("/notebooks"),
        csv_file=Path("output.csv"),
        include="**/*.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=True,
        absolute_path=False,
        course_server=True,
    )

    result = extractor._generate_extracted_cell_data(
        cell_info=cell_info,
        cell_index=0,
        notebook_index=0,
        textbook_path=Path("server1/test.ipynb"),
        notebook_meme="notebook-456",
        notebook_path=Path("/notebooks/server1/test.ipynb"),
        args=args,
    )

    assert result["lc_cell_meme"] == "cell-123"  # Branch number preserved
    assert result["course_server"] == "server1"


def test_generate_extracted_cell_data_with_qlabel():
    """Test _generate_extracted_cell_data with question label pattern."""
    import re
    from pathlib import Path

    cell_info = extractor.CellInfo(cell_meme="cell-789", code="y = 2", markdown="## Question 5: Calculate the sum")

    args = extractor.ExtractorArgs(
        notebook_path=Path("/notebooks"),
        csv_file=Path("output.csv"),
        include="**/*.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=False,
        absolute_path=False,
        pattern=re.compile(r"Question \d+", re.MULTILINE),
    )

    result = extractor._generate_extracted_cell_data(
        cell_info=cell_info,
        cell_index=1,
        notebook_index=2,
        textbook_path=Path("test.ipynb"),
        notebook_meme=None,
        notebook_path=Path("/notebooks/test.ipynb"),
        args=args,
    )

    assert result["qlabel"] == "Question 5"
    assert result["lc_notebook_meme"] is None


def test_generate_extracted_cell_data_no_pattern_match():
    """Test _generate_extracted_cell_data when pattern doesn't match."""
    import re
    from pathlib import Path

    cell_info = extractor.CellInfo(cell_meme="cell-999", code="z = 3", markdown="Some random text")

    args = extractor.ExtractorArgs(
        notebook_path=Path("/notebooks"),
        csv_file=Path("output.csv"),
        include="**/*.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=False,
        absolute_path=False,
        pattern=re.compile(r"Question \d+", re.MULTILINE),
    )

    result = extractor._generate_extracted_cell_data(
        cell_info=cell_info,
        cell_index=0,
        notebook_index=0,
        textbook_path=Path("test.ipynb"),
        notebook_meme="notebook-999",
        notebook_path=Path("/notebooks/test.ipynb"),
        args=args,
    )

    assert "qlabel" not in result


def test_get_current_timestamp():
    """Test _get_current_timestamp returns valid ISO format."""
    from datetime import datetime

    timestamp = extractor._get_current_timestamp()

    # Should be a valid ISO format timestamp
    assert isinstance(timestamp, str)
    assert "T" in timestamp  # ISO format contains T

    # Should be parseable as datetime
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert isinstance(parsed, datetime)


def test_get_fieldnames_from_data_basic():
    """Test _get_fieldnames_from_data with basic fields."""
    data = extractor.ExtractedData(
        cells=[
            extractor.ExtractedCellData(
                qno="01-001",
                lc_cell_meme="cell-123",
                lc_notebook_meme="notebook-456",
                textbook_path="test.ipynb",
                code="print('hello')",
                source_info={},
            )
        ],
        metadata={},
        extraction_args={},
    )

    fieldnames = extractor._get_fieldnames_from_data(data)

    expected = ["qno", "lc_cell_meme", "lc_notebook_meme", "textbook_path", "code"]
    assert fieldnames == expected


def test_get_fieldnames_from_data_with_qlabel():
    """Test _get_fieldnames_from_data with qlabel field."""
    data = extractor.ExtractedData(
        cells=[
            extractor.ExtractedCellData(
                qno="01-001",
                lc_cell_meme="cell-123",
                lc_notebook_meme="notebook-456",
                textbook_path="test.ipynb",
                code="print('hello')",
                qlabel="Question 1",
                source_info={},
            )
        ],
        metadata={},
        extraction_args={},
    )

    fieldnames = extractor._get_fieldnames_from_data(data)

    expected = ["qno", "qlabel", "lc_cell_meme", "lc_notebook_meme", "textbook_path", "code"]
    assert fieldnames == expected


def test_get_fieldnames_from_data_with_course_server():
    """Test _get_fieldnames_from_data with course_server field."""
    data = extractor.ExtractedData(
        cells=[
            extractor.ExtractedCellData(
                qno="01-001",
                lc_cell_meme="cell-123",
                lc_notebook_meme="notebook-456",
                textbook_path="test.ipynb",
                code="print('hello')",
                course_server="server1",
                source_info={},
            )
        ],
        metadata={},
        extraction_args={},
    )

    fieldnames = extractor._get_fieldnames_from_data(data)

    expected = ["qno", "lc_cell_meme", "lc_notebook_meme", "textbook_path", "course_server", "code"]
    assert fieldnames == expected


def test_get_fieldnames_from_data_with_all_fields():
    """Test _get_fieldnames_from_data with all optional fields."""
    data = extractor.ExtractedData(
        cells=[
            extractor.ExtractedCellData(
                qno="01-001",
                lc_cell_meme="cell-123",
                lc_notebook_meme="notebook-456",
                textbook_path="test.ipynb",
                code="print('hello')",
                qlabel="Question 1",
                course_server="server1",
                source_info={},
            )
        ],
        metadata={},
        extraction_args={},
    )

    fieldnames = extractor._get_fieldnames_from_data(data)

    expected = ["qno", "qlabel", "lc_cell_meme", "lc_notebook_meme", "textbook_path", "course_server", "code"]
    assert fieldnames == expected


def test_get_fieldnames_from_data_empty():
    """Test _get_fieldnames_from_data with empty cells."""
    data = extractor.ExtractedData(cells=[], metadata={}, extraction_args={})

    fieldnames = extractor._get_fieldnames_from_data(data)

    expected = ["qno", "lc_cell_meme", "lc_notebook_meme", "textbook_path", "code"]
    assert fieldnames == expected


def test_write_csv_from_extracted_data_basic(tmp_path):
    """Test _write_csv_from_extracted_data with basic data."""
    import csv

    data = extractor.ExtractedData(
        cells=[
            extractor.ExtractedCellData(
                qno="01-001",
                lc_cell_meme="cell-123",
                lc_notebook_meme="notebook-456",
                textbook_path="test.ipynb",
                code="print('hello')",
                source_info={"notebook_path": "/test.ipynb", "cell_index": 0},
            )
        ],
        metadata={"total_cells": 1},
        extraction_args={},
    )

    csv_file = tmp_path / "output.csv"

    extractor._write_csv_from_extracted_data(data, csv_file)

    # Verify CSV was created and has correct content
    assert csv_file.exists()

    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["qno"] == "01-001"
    assert rows[0]["lc_cell_meme"] == "cell-123"
    assert rows[0]["lc_notebook_meme"] == "notebook-456"
    assert rows[0]["textbook_path"] == "test.ipynb"
    assert rows[0]["code"] == "print('hello')"


def test_write_csv_from_extracted_data_with_optional_fields(tmp_path):
    """Test _write_csv_from_extracted_data with optional fields."""
    import csv

    data = extractor.ExtractedData(
        cells=[
            extractor.ExtractedCellData(
                qno="01-001",
                lc_cell_meme="cell-123",
                lc_notebook_meme="notebook-456",
                textbook_path="test.ipynb",
                code="print('hello')",
                qlabel="Question 1",
                course_server="server1",
                source_info={"notebook_path": "/test.ipynb", "cell_index": 0},
            )
        ],
        metadata={"total_cells": 1},
        extraction_args={},
    )

    csv_file = tmp_path / "output.csv"

    extractor._write_csv_from_extracted_data(data, csv_file)

    # Verify CSV was created and has correct content with optional fields
    assert csv_file.exists()

    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["qno"] == "01-001"
    assert rows[0]["qlabel"] == "Question 1"
    assert rows[0]["lc_cell_meme"] == "cell-123"
    assert rows[0]["lc_notebook_meme"] == "notebook-456"
    assert rows[0]["textbook_path"] == "test.ipynb"
    assert rows[0]["course_server"] == "server1"
    assert rows[0]["code"] == "print('hello')"


def test_write_csv_from_extracted_data_empty_cells(tmp_path):
    """Test _write_csv_from_extracted_data with empty cells."""
    import csv

    data = extractor.ExtractedData(cells=[], metadata={"total_cells": 0}, extraction_args={})

    csv_file = tmp_path / "output.csv"

    extractor._write_csv_from_extracted_data(data, csv_file)

    # Verify empty CSV was created with headers
    assert csv_file.exists()

    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 0
    assert reader.fieldnames == ["qno", "lc_cell_meme", "lc_notebook_meme", "textbook_path", "code"]


def test_write_csv_from_extracted_data_none_values(tmp_path):
    """Test _write_csv_from_extracted_data handles None values correctly."""
    import csv

    data = extractor.ExtractedData(
        cells=[
            extractor.ExtractedCellData(
                qno="01-001",
                lc_cell_meme=None,
                lc_notebook_meme=None,
                textbook_path="test.ipynb",
                code="print('hello')",
                source_info={"notebook_path": "/test.ipynb", "cell_index": 0},
            )
        ],
        metadata={"total_cells": 1},
        extraction_args={},
    )

    csv_file = tmp_path / "output.csv"

    extractor._write_csv_from_extracted_data(data, csv_file)

    # Verify None values are converted to empty strings
    assert csv_file.exists()

    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["qno"] == "01-001"
    assert rows[0]["lc_cell_meme"] == ""
    assert rows[0]["lc_notebook_meme"] == ""
    assert rows[0]["textbook_path"] == "test.ipynb"
    assert rows[0]["code"] == "print('hello')"


def test_extract_data_from_notebooks_basic(tmp_path):
    """Test _extract_data_from_notebooks with basic functionality."""
    import json

    # Create test notebook
    notebook_data = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {"lc_notebook_meme": {"current": "notebook-123"}},
        "cells": [
            {
                "cell_type": "code",
                "source": "print('hello')",
                "metadata": {"lc_cell_meme": {"current": "cell-456"}},
                "execution_count": None,
                "outputs": [],
            }
        ],
    }

    notebook_file = tmp_path / "test.ipynb"
    with open(notebook_file, "w", encoding="utf-8") as f:
        json.dump(notebook_data, f)

    args = extractor.ExtractorArgs(
        notebook_path=tmp_path,
        csv_file=tmp_path / "output.csv",
        include="*.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=False,
        absolute_path=False,
    )

    result = extractor._extract_data_from_notebooks(args)

    assert len(result["cells"]) == 1
    assert result["cells"][0]["lc_cell_meme"] == "cell-456"
    assert result["cells"][0]["lc_notebook_meme"] == "notebook-123"
    assert result["cells"][0]["textbook_path"] == "test.ipynb"
    assert result["cells"][0]["code"] == "print('hello')"
    assert result["metadata"]["total_notebooks"] == 1
    assert result["metadata"]["processed_notebooks"] == 1
    assert result["metadata"]["total_cells"] == 1


def test_extract_data_from_notebooks_with_exclusion(tmp_path):
    """Test _extract_data_from_notebooks with file exclusion."""
    import json

    # Create test notebooks
    for i, name in enumerate(["test1.ipynb", "test2.ipynb", "excluded.ipynb"]):
        notebook_data = {
            "nbformat": 4,
            "nbformat_minor": 4,
            "metadata": {"lc_notebook_meme": {"current": f"notebook-{i}"}},
            "cells": [
                {
                    "cell_type": "code",
                    "source": f"print('test{i}')",
                    "metadata": {"lc_cell_meme": {"current": f"cell-{i}"}},
                    "execution_count": None,
                    "outputs": [],
                }
            ],
        }

        notebook_file = tmp_path / name
        with open(notebook_file, "w", encoding="utf-8") as f:
            json.dump(notebook_data, f)

    args = extractor.ExtractorArgs(
        notebook_path=tmp_path,
        csv_file=tmp_path / "output.csv",
        include="*.ipynb",
        exclude="excluded.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=False,
        absolute_path=False,
    )

    result = extractor._extract_data_from_notebooks(args)

    # Should process 2 files (excluding excluded.ipynb)
    assert len(result["cells"]) == 2
    assert result["metadata"]["total_notebooks"] == 3
    assert result["metadata"]["processed_notebooks"] == 2


def test_extract_data_from_notebooks_error_handling(tmp_path, caplog):
    """Test _extract_data_from_notebooks error handling for invalid notebooks."""
    import json

    # Create valid notebook
    valid_notebook = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {"lc_notebook_meme": {"current": "notebook-123"}},
        "cells": [
            {
                "cell_type": "code",
                "source": "print('hello')",
                "metadata": {"lc_cell_meme": {"current": "cell-456"}},
                "execution_count": None,
                "outputs": [],
            }
        ],
    }

    valid_file = tmp_path / "valid.ipynb"
    with open(valid_file, "w", encoding="utf-8") as f:
        json.dump(valid_notebook, f)

    # Create invalid notebook (invalid JSON)
    invalid_file = tmp_path / "invalid.ipynb"
    with open(invalid_file, "w", encoding="utf-8") as f:
        f.write("invalid json content")

    args = extractor.ExtractorArgs(
        notebook_path=tmp_path,
        csv_file=tmp_path / "output.csv",
        include="*.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=False,
        absolute_path=False,
    )

    result = extractor._extract_data_from_notebooks(args)

    # Should process only valid notebook, log error for invalid
    assert len(result["cells"]) == 1
    assert result["metadata"]["total_notebooks"] == 2
    assert result["metadata"]["processed_notebooks"] == 1

    # Check that error was logged
    assert any("Error processing" in record.message for record in caplog.records)


def test_write_csv_error_handling(tmp_path, caplog):
    """Test _write_csv_from_extracted_data error handling for file write errors."""
    from unittest.mock import mock_open, patch

    data = extractor.ExtractedData(
        cells=[
            extractor.ExtractedCellData(
                qno="01-001",
                lc_cell_meme="cell-123",
                lc_notebook_meme="notebook-456",
                textbook_path="test.ipynb",
                code="print('hello')",
                source_info={"notebook_path": "/test.ipynb", "cell_index": 0},
            )
        ],
        metadata={"total_cells": 1},
        extraction_args={},
    )

    csv_file = tmp_path / "output.csv"

    # Mock open to raise OSError
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = OSError("Permission denied")

        extractor._write_csv_from_extracted_data(data, csv_file)

        # Should log the error
        assert any("Error writing" in record.message for record in caplog.records)


def test_process_notebooks_once_basic(tmp_path):
    """Test process_notebooks_once with basic functionality."""
    import json

    # Create test notebook
    notebook_data = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {"lc_notebook_meme": {"current": "notebook-123"}},
        "cells": [
            {
                "cell_type": "code",
                "source": "print('hello')",
                "metadata": {"lc_cell_meme": {"current": "cell-456"}},
                "execution_count": None,
                "outputs": [],
            }
        ],
    }

    notebook_file = tmp_path / "test.ipynb"
    with open(notebook_file, "w", encoding="utf-8") as f:
        json.dump(notebook_data, f)

    csv_file = tmp_path / "output.csv"

    extractor_args = extractor.ExtractorArgs(
        notebook_path=tmp_path,
        csv_file=csv_file,
        include="*.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=False,
        absolute_path=False,
    )

    validator_args = {"enabled": False, "strict_mode": False, "csv_file": csv_file}

    exit_code = extractor.process_notebooks_once(extractor_args, validator_args)

    assert exit_code == 0
    assert csv_file.exists()


def test_process_notebooks_once_with_validation_success(tmp_path):
    """Test process_notebooks_once with validation enabled and passing."""
    import json

    # Create test notebook
    notebook_data = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {"lc_notebook_meme": {"current": "notebook-123"}},
        "cells": [
            {
                "cell_type": "code",
                "source": "print('hello')",
                "metadata": {"lc_cell_meme": {"current": "cell-456"}},
                "execution_count": None,
                "outputs": [],
            }
        ],
    }

    notebook_file = tmp_path / "test.ipynb"
    with open(notebook_file, "w", encoding="utf-8") as f:
        json.dump(notebook_data, f)

    csv_file = tmp_path / "output.csv"

    extractor_args = extractor.ExtractorArgs(
        notebook_path=tmp_path,
        csv_file=csv_file,
        include="*.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=False,
        absolute_path=False,
    )

    validator_args = {"enabled": True, "strict_mode": False, "csv_file": csv_file}

    exit_code = extractor.process_notebooks_once(extractor_args, validator_args)

    assert exit_code == 0
    assert csv_file.exists()


def test_process_notebooks_once_validation_failure_strict_mode(tmp_path):
    """Test process_notebooks_once with validation failure in strict mode."""
    import json

    # Create test notebooks with duplicate cell meme (will cause validation error)
    notebook_data1 = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {"lc_notebook_meme": {"current": "notebook-123"}},
        "cells": [
            {
                "cell_type": "code",
                "source": "print('hello')",
                "metadata": {"lc_cell_meme": {"current": "cell-duplicate"}},
                "execution_count": None,
                "outputs": [],
            }
        ],
    }

    notebook_data2 = {
        "nbformat": 4,
        "nbformat_minor": 4,
        "metadata": {"lc_notebook_meme": {"current": "notebook-456"}},
        "cells": [
            {
                "cell_type": "code",
                "source": "print('world')",
                "metadata": {"lc_cell_meme": {"current": "cell-duplicate"}},  # Same cell meme
                "execution_count": None,
                "outputs": [],
            }
        ],
    }

    notebook_file1 = tmp_path / "test1.ipynb"
    with open(notebook_file1, "w", encoding="utf-8") as f:
        json.dump(notebook_data1, f)

    notebook_file2 = tmp_path / "test2.ipynb"
    with open(notebook_file2, "w", encoding="utf-8") as f:
        json.dump(notebook_data2, f)

    csv_file = tmp_path / "output.csv"

    extractor_args = extractor.ExtractorArgs(
        notebook_path=tmp_path,
        csv_file=csv_file,
        include="*.ipynb",
        format="{:02d}-{:03d}",
        hold_branch_number=False,
        absolute_path=False,
    )

    validator_args = {"enabled": True, "strict_mode": True, "csv_file": csv_file}

    exit_code = extractor.process_notebooks_once(extractor_args, validator_args)

    # Should return exit code 1 and not create CSV in strict mode
    assert exit_code == 1
    assert not csv_file.exists()
