# SPDX-FileCopyrightText: 2025-present NII Gakunin Cloud <cld-office-support@nii.ac.jp>
#
# SPDX-License-Identifier: Apache-2.0
"""
Tests for the validator module.

This module contains comprehensive tests for CSV validation functionality,
including missing value detection, duplicate validation, and error handling.
"""

# pylint: disable=redefined-outer-name, unused-argument
# ruff: noqa: ARG002

import csv
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from memeid_extractor.validator import (
    ValidationError,
    ValidationResult,
    display_validation_results,
)


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        yield Path(f.name)
    Path(f.name).unlink(missing_ok=True)


def create_csv_content(rows: list[dict[str, str]], temp_file: Path) -> None:
    """Helper function to create CSV content."""
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with open(temp_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class TestDisplayValidationResults:
    """Test cases for display_validation_results function."""

    @patch("memeid_extractor.validator.logger")
    def test_display_valid_results_verbose_mode(self, mock_logger):
        """Test display of valid results in verbose mode."""
        result = ValidationResult(is_valid=True, errors=[], total_rows=5, valid_rows=5)

        display_validation_results(result, display_mode="verbose")

        mock_logger.info.assert_called_once_with("CSV validation passed: %d rows validated successfully", 5)

    @patch("memeid_extractor.validator.logger")
    def test_display_valid_results_quiet_mode(self, mock_logger):
        """Test display of valid results in quiet mode."""
        result = ValidationResult(is_valid=True, errors=[], total_rows=5, valid_rows=5)

        display_validation_results(result, display_mode="quiet")

        # Quiet mode: only DEBUG logging, no info/warning output
        mock_logger.debug.assert_called_once_with("CSV validation passed: %d rows", 5)
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()

    @patch("memeid_extractor.validator.logger")
    def test_display_invalid_results_verbose_mode(self, mock_logger):
        """Test display of invalid results in verbose mode."""
        errors = [
            ValidationError(
                error_type="missing_value",
                message="Missing lc_cell_meme value",
                row_number=1,
                field_name="lc_cell_meme",
                field_value="",
                textbook_path="test.ipynb",
                additional_info="textbook_path: test.ipynb",
            ),  # type: ignore[call-arg]
            ValidationError(
                error_type="duplicate_value",
                message="Duplicate lc_cell_meme value: cell-1",
                row_number=2,
                field_name="lc_cell_meme",
                field_value="cell-1",
                textbook_path="test.ipynb",
            ),  # type: ignore[call-arg]
        ]
        result = ValidationResult(is_valid=False, errors=errors, total_rows=5, valid_rows=3)

        display_validation_results(result, display_mode="verbose")

        # Verify verbose mode shows normal mode summary first, then detailed breakdown
        mock_logger.warning.assert_any_call("Validation errors found:")  # Normal mode summary
        mock_logger.warning.assert_any_call("  %s:", "test.ipynb")
        mock_logger.warning.assert_any_call("    Missing values: %s", "lc_cell_meme")
        mock_logger.warning.assert_any_call("    Duplicate values: %s", "lc_cell_meme")
        mock_logger.warning.assert_any_call("")  # Separator line
        mock_logger.warning.assert_any_call("Detailed breakdown:")
        mock_logger.warning.assert_any_call("CSV validation failed: %d error(s) found in %d rows", 2, 5)

    @patch("memeid_extractor.validator.logger")
    def test_display_invalid_results_quiet_mode(self, mock_logger):
        """Test display of invalid results in quiet mode."""
        errors = [
            ValidationError(
                error_type="missing_value",
                message="Missing lc_cell_meme value",
                row_number=1,
                field_name="lc_cell_meme",
                field_value="",
                textbook_path="test.ipynb",
            )  # type: ignore[call-arg]
        ]
        result = ValidationResult(is_valid=False, errors=errors, total_rows=5, valid_rows=4)

        display_validation_results(result, display_mode="quiet")

        # Quiet mode: only DEBUG logging, no info/warning output
        mock_logger.debug.assert_called_once_with("CSV validation failed: %d error(s) in %d rows", 1, 5)
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()

    @patch("memeid_extractor.validator.logger")
    def test_display_many_errors_truncation(self, mock_logger):
        """Test truncation of error display when there are many errors."""
        # Create more than 5 errors of the same type
        errors = [
            ValidationError(
                error_type="missing_value",
                message=f"Missing lc_cell_meme value {i}",
                row_number=i + 1,
                field_name="lc_cell_meme",
                field_value="",
                textbook_path="test.ipynb",
            )  # type: ignore[call-arg]
            for i in range(7)
        ]

        result = ValidationResult(is_valid=False, errors=errors, total_rows=10, valid_rows=3)

        display_validation_results(result, display_mode="verbose")

        # Verify truncation message was displayed
        warning_calls = mock_logger.warning.call_args_list
        # Look for the truncation pattern in the formatted messages
        truncation_found = False
        for call in warning_calls:
            call_args = call[0]
            if (
                len(call_args) > 1
                and "more error(s) of this type" in str(call_args[0])
                and call_args[1] == 2  # We expect 2 more errors (7 total - 5 displayed)
            ):
                truncation_found = True
                break
        assert truncation_found, f"Truncation message not found in calls: {warning_calls}"

    @patch("memeid_extractor.validator.logger")
    def test_display_normal_mode_duplicate_errors(self, mock_logger):
        """Test normal mode display for duplicate_meme_different_path errors."""
        errors = [
            ValidationError(
                error_type="duplicate_meme_different_path",
                message="Different textbook_path has same lc_notebook_meme value",
                row_number=2,
                field_name="textbook_path",
                field_value="notebook1.ipynb",
                textbook_path="notebook1.ipynb",
                additional_info="lc_notebook_meme: meme123, expected path: expected.ipynb (first seen at row 1)",
                structured_data={"expected_path": "expected.ipynb", "first_row": 1, "notebook_meme": "meme123"},
            ),
            ValidationError(
                error_type="duplicate_meme_different_path",
                message="Different textbook_path has same lc_notebook_meme value",
                row_number=3,
                field_name="textbook_path",
                field_value="notebook1.ipynb",
                textbook_path="notebook1.ipynb",
                additional_info="lc_notebook_meme: meme123, expected path: expected.ipynb (first seen at row 1)",
                structured_data={"expected_path": "expected.ipynb", "first_row": 1, "notebook_meme": "meme123"},
            ),
            ValidationError(
                error_type="duplicate_meme_different_path",
                message="Different textbook_path has same lc_notebook_meme value",
                row_number=4,
                field_name="textbook_path",
                field_value="notebook2.ipynb",
                textbook_path="notebook2.ipynb",
                additional_info="lc_notebook_meme: meme456, expected path: other.ipynb (first seen at row 1)",
                structured_data={"expected_path": "other.ipynb", "first_row": 1, "notebook_meme": "meme456"},
            ),
        ]
        result = ValidationResult(is_valid=False, errors=errors, total_rows=5, valid_rows=2)

        display_validation_results(result, display_mode="normal")

        # Verify grouped and deduplicated output
        mock_logger.warning.assert_any_call("Validation errors found:")
        mock_logger.warning.assert_any_call("  %s:", "notebook1.ipynb")
        mock_logger.warning.assert_any_call("    Duplicate values: %s", "textbook_path")
        mock_logger.warning.assert_any_call("    Path conflicts: %s", "expected.ipynb")
        mock_logger.warning.assert_any_call("  %s:", "notebook2.ipynb")
        mock_logger.warning.assert_any_call("    Duplicate values: %s", "textbook_path")
        mock_logger.warning.assert_any_call("    Path conflicts: %s", "other.ipynb")

        # Verify fix guide is called
        mock_logger.info.assert_any_call("")  # Empty line for separation
        mock_logger.info.assert_any_call("To fix these errors, run:")
        mock_logger.info.assert_any_call(
            "  jupyter nblineage new-root-meme %s %s", "notebook1.ipynb", "notebook1.fixed.ipynb"
        )
        mock_logger.info.assert_any_call(
            "  jupyter nblineage new-root-meme %s %s", "notebook2.ipynb", "notebook2.fixed.ipynb"
        )

    @patch("memeid_extractor.validator.logger")
    def test_display_normal_mode_no_duplicate_errors(self, mock_logger):
        """Test normal mode when no duplicate_meme_different_path errors exist."""
        errors = [
            ValidationError(
                error_type="missing_value",
                message="Missing lc_cell_meme value",
                row_number=1,
                field_name="lc_cell_meme",
                field_value="",
                textbook_path="test.ipynb",
            )
        ]
        result = ValidationResult(is_valid=False, errors=errors, total_rows=5, valid_rows=4)

        display_validation_results(result, display_mode="normal")

        # Should display missing values but not warning header
        mock_logger.warning.assert_any_call("Validation errors found:")
        mock_logger.warning.assert_any_call("  %s:", "test.ipynb")
        mock_logger.warning.assert_any_call("    Missing values: %s", "lc_cell_meme")

        # Verify fix guide is called
        mock_logger.info.assert_any_call("")  # Empty line for separation
        mock_logger.info.assert_any_call("To fix these errors, run:")
        mock_logger.info.assert_any_call("  jupyter nblineage new-root-meme %s %s", "test.ipynb", "test.fixed.ipynb")

    @patch("memeid_extractor.validator.logger")
    def test_display_normal_mode_valid_results(self, mock_logger):
        """Test normal mode display for valid results."""
        result = ValidationResult(is_valid=True, errors=[], total_rows=5, valid_rows=5)

        display_validation_results(result, display_mode="normal")

        mock_logger.info.assert_called_once_with("CSV validation passed: %d rows validated successfully", 5)

    @patch("memeid_extractor.validator.logger")
    def test_display_normal_mode_all_error_types(self, mock_logger):
        """Test normal mode display with all error types."""
        errors = [
            ValidationError(
                error_type="missing_value",
                message="Missing lc_cell_meme value",
                row_number=1,
                field_name="lc_cell_meme",
                field_value="",
                textbook_path="notebook1.ipynb",
            ),
            ValidationError(
                error_type="missing_value",
                message="Missing lc_notebook_meme value",
                row_number=2,
                field_name="lc_notebook_meme",
                field_value="",
                textbook_path="notebook1.ipynb",
            ),
            ValidationError(
                error_type="duplicate_value",
                message="Duplicate lc_cell_meme value: cell123",
                row_number=3,
                field_name="lc_cell_meme",
                field_value="cell123",
                textbook_path="notebook1.ipynb",
                additional_info="First occurrence at row 1, textbook_path: notebook1.ipynb",
                structured_data={"first_occurrence_row": 1},
            ),
            ValidationError(
                error_type="duplicate_meme_different_path",
                message="Different textbook_path has same lc_notebook_meme value",
                row_number=4,
                field_name="textbook_path",
                field_value="notebook2.ipynb",
                textbook_path="notebook2.ipynb",
                additional_info="lc_notebook_meme: meme456, expected path: notebook1.ipynb (first seen at row 1)",
                structured_data={"expected_path": "notebook1.ipynb", "first_row": 1, "notebook_meme": "meme456"},
            ),
        ]
        result = ValidationResult(is_valid=False, errors=errors, total_rows=10, valid_rows=6)

        display_validation_results(result, display_mode="normal")

        # Verify comprehensive grouped output
        mock_logger.warning.assert_any_call("Validation errors found:")
        mock_logger.warning.assert_any_call("  %s:", "notebook1.ipynb")
        mock_logger.warning.assert_any_call("    Missing values: %s", "lc_cell_meme, lc_notebook_meme")
        mock_logger.warning.assert_any_call("    Duplicate values: %s", "lc_cell_meme")
        mock_logger.warning.assert_any_call("  %s:", "notebook2.ipynb")
        mock_logger.warning.assert_any_call("    Duplicate values: %s", "textbook_path")
        mock_logger.warning.assert_any_call("    Path conflicts: %s", "notebook1.ipynb")

        # Verify fix guide is called
        mock_logger.info.assert_any_call("")  # Empty line for separation
        mock_logger.info.assert_any_call("To fix these errors, run:")
        mock_logger.info.assert_any_call(
            "  jupyter nblineage new-root-meme %s %s", "notebook1.ipynb", "notebook1.fixed.ipynb"
        )
        mock_logger.info.assert_any_call(
            "  jupyter nblineage new-root-meme %s %s", "notebook2.ipynb", "notebook2.fixed.ipynb"
        )

    @patch("memeid_extractor.validator.logger")
    def test_display_normal_mode_inconsistent_error(self, mock_logger):
        """Test normal mode raises exception for inconsistent_correspondence errors."""
        errors = [
            ValidationError(
                error_type="inconsistent_correspondence",
                message="Same textbook_path has different lc_notebook_meme values",
                row_number=1,
                field_name="lc_notebook_meme",
                field_value="meme123",
                textbook_path="test.ipynb",
                additional_info="textbook_path: test.ipynb, expected: meme456 (first seen at row 1)",
            )
        ]
        result = ValidationResult(is_valid=False, errors=errors, total_rows=5, valid_rows=4)

        with pytest.raises(
            RuntimeError, match="Detected inconsistent_correspondence errors, indicating a bug in the validation logic."
        ):
            display_validation_results(result, display_mode="normal")

    def test_display_invalid_mode(self):
        """Test display_validation_results with invalid display mode."""
        result = ValidationResult(is_valid=True, errors=[], total_rows=5, valid_rows=5)

        with pytest.raises(ValueError, match="Invalid display_mode"):
            display_validation_results(result, display_mode="invalid")


class TestValidationErrorFactories:
    """Test cases for ValidationError factory functions."""

    def test_create_missing_value_error(self):
        """Test _create_missing_value_error factory function."""
        from memeid_extractor.validator import _create_missing_value_error

        error = _create_missing_value_error("lc_cell_meme", 1, "test.ipynb")

        assert error["error_type"] == "missing_value"
        assert error["message"] == "Missing lc_cell_meme value"
        assert error["row_number"] == 1
        assert error["field_name"] == "lc_cell_meme"
        assert error["field_value"] == ""
        assert error["textbook_path"] == "test.ipynb"
        assert error["additional_info"] == "textbook_path: test.ipynb"

    def test_create_duplicate_value_error(self):
        """Test _create_duplicate_value_error factory function."""
        from memeid_extractor.validator import _create_duplicate_value_error

        error = _create_duplicate_value_error("cell-123", 2, 1, "test.ipynb")

        assert error["error_type"] == "duplicate_value"
        assert error["message"] == "Duplicate lc_cell_meme value: cell-123"
        assert error["row_number"] == 2
        assert error["field_name"] == "lc_cell_meme"
        assert error["field_value"] == "cell-123"
        assert error["textbook_path"] == "test.ipynb"
        assert error["additional_info"] == "First occurrence at row 1, textbook_path: test.ipynb"
        assert error["structured_data"]["first_occurrence_row"] == 1

    def test_create_inconsistent_correspondence_error(self):
        """Test _create_inconsistent_correspondence_error factory function."""
        from memeid_extractor.validator import _create_inconsistent_correspondence_error

        error = _create_inconsistent_correspondence_error("test.ipynb", "meme-123", 2, "meme-456", 1)

        assert error["error_type"] == "inconsistent_correspondence"
        assert error["message"] == "Same textbook_path has different lc_notebook_meme values"
        assert error["row_number"] == 2
        assert error["field_name"] == "lc_notebook_meme"
        assert error["field_value"] == "meme-123"
        assert error["textbook_path"] == "test.ipynb"
        assert "expected: meme-456" in error["additional_info"]
        assert error["structured_data"]["expected_meme"] == "meme-456"
        assert error["structured_data"]["first_row"] == 1

    def test_create_duplicate_meme_different_path_error(self):
        """Test _create_duplicate_meme_different_path_error factory function."""
        from memeid_extractor.validator import _create_duplicate_meme_different_path_error

        error = _create_duplicate_meme_different_path_error("meme-123", "test2.ipynb", 2, "test1.ipynb", 1)

        assert error["error_type"] == "duplicate_meme_different_path"
        assert error["message"] == "Different textbook_path has same lc_notebook_meme value"
        assert error["row_number"] == 2
        assert error["field_name"] == "textbook_path"
        assert error["field_value"] == "test2.ipynb"
        assert error["textbook_path"] == "test2.ipynb"
        assert "expected path: test1.ipynb" in error["additional_info"]
        assert error["structured_data"]["expected_path"] == "test1.ipynb"
        assert error["structured_data"]["first_row"] == 1
        assert error["structured_data"]["notebook_meme"] == "meme-123"


class TestValidationHelpers:
    """Test cases for validation helper functions."""

    def test_validate_missing_values_comprehensive(self):
        """Test _validate_missing_values with comprehensive edge cases."""
        from memeid_extractor.validator import _validate_missing_values

        rows = [
            {"lc_cell_meme": "", "lc_notebook_meme": "", "textbook_path": "test1.ipynb"},
            {"lc_cell_meme": "  ", "lc_notebook_meme": "  ", "textbook_path": "test2.ipynb"},  # Whitespace only
            {"lc_cell_meme": "cell-123", "lc_notebook_meme": "", "textbook_path": "test3.ipynb"},
            {"lc_cell_meme": "", "lc_notebook_meme": "notebook-456", "textbook_path": "test4.ipynb"},
        ]

        errors = _validate_missing_values(rows)

        # Should find 6 missing value errors (2 for each of first 2 rows, 1 each for last 2 rows)
        assert len(errors) == 6

        # Check specific error details
        assert all(error["error_type"] == "missing_value" for error in errors)
        assert errors[0]["textbook_path"] == "test1.ipynb"
        assert errors[1]["textbook_path"] == "test1.ipynb"

    def test_validate_cell_meme_duplicates_comprehensive(self):
        """Test _validate_cell_meme_duplicates with comprehensive cases."""
        from memeid_extractor.validator import _validate_cell_meme_duplicates

        rows = [
            {"lc_cell_meme": "cell-123", "textbook_path": "test1.ipynb"},
            {"lc_cell_meme": "cell-456", "textbook_path": "test2.ipynb"},
            {"lc_cell_meme": "cell-123", "textbook_path": "test3.ipynb"},  # Duplicate
            {"lc_cell_meme": "", "textbook_path": "test4.ipynb"},  # Empty, should be skipped
            {"lc_cell_meme": "cell-123", "textbook_path": "test5.ipynb"},  # Another duplicate
        ]

        errors = _validate_cell_meme_duplicates(rows)

        # Should find 2 duplicate errors (rows 3 and 5)
        assert len(errors) == 2
        assert all(error["error_type"] == "duplicate_value" for error in errors)
        assert errors[0]["row_number"] == 3
        assert errors[0]["structured_data"]["first_occurrence_row"] == 1
        assert errors[1]["row_number"] == 5
        assert errors[1]["structured_data"]["first_occurrence_row"] == 1

    def test_validate_notebook_meme_correspondence_edge_cases(self):
        """Test _validate_notebook_meme_correspondence with edge cases."""
        from memeid_extractor.validator import _validate_notebook_meme_correspondence

        rows = [
            {"textbook_path": "", "lc_notebook_meme": "", "other": "data"},  # Empty, should be skipped
            {"textbook_path": "test1.ipynb", "lc_notebook_meme": "meme-123"},
            {"textbook_path": "test1.ipynb", "lc_notebook_meme": "meme-456"},  # Different meme for same path
            {"textbook_path": "test2.ipynb", "lc_notebook_meme": "meme-123"},  # Same meme for different path
        ]

        errors = _validate_notebook_meme_correspondence(rows)

        # Should find 2 errors: inconsistent correspondence and duplicate meme different path
        assert len(errors) == 2
        error_types = {error["error_type"] for error in errors}
        assert "inconsistent_correspondence" in error_types
        assert "duplicate_meme_different_path" in error_types


class TestValidateExtractedData:
    """Test cases for validate_extracted_data function."""

    def test_validate_extracted_data_empty(self):
        """Test validate_extracted_data with empty data."""
        from memeid_extractor.extractor import ExtractedData
        from memeid_extractor.validator import validate_extracted_data

        data = ExtractedData(cells=[], metadata={}, extraction_args={})

        result = validate_extracted_data(data)

        assert result["is_valid"] is True
        assert result["errors"] == []
        assert result["total_rows"] == 0
        assert result["valid_rows"] == 0

    def test_validate_extracted_data_with_none_values(self):
        """Test validate_extracted_data handles None values correctly."""
        from memeid_extractor.extractor import ExtractedCellData, ExtractedData
        from memeid_extractor.validator import validate_extracted_data

        data = ExtractedData(
            cells=[
                ExtractedCellData(
                    qno="01-001",
                    lc_cell_meme=None,  # None value
                    lc_notebook_meme=None,  # None value
                    textbook_path="test.ipynb",
                    code="print('hello')",
                    source_info={},
                )
            ],
            metadata={},
            extraction_args={},
        )

        result = validate_extracted_data(data)

        # Should convert None to empty string and find missing value errors
        assert result["is_valid"] is False
        assert len(result["errors"]) == 2  # Missing cell meme and notebook meme
        assert all(error["error_type"] == "missing_value" for error in result["errors"])


class TestDisplayModeEdgeCases:
    """Test edge cases for display mode functionality."""

    @patch("memeid_extractor.validator.logger")
    def test_display_normal_mode_empty_path_groups(self, mock_logger):
        """Test normal mode when no relevant errors to display."""
        from memeid_extractor.validator import _display_normal_validation_results

        # Only inconsistent_correspondence errors (filtered out in normal mode)
        errors = [
            ValidationError(
                error_type="inconsistent_correspondence",
                message="Same textbook_path has different lc_notebook_meme values",
                row_number=1,
                field_name="lc_notebook_meme",
                field_value="meme123",
                textbook_path="test.ipynb",
            )
        ]
        result = ValidationResult(is_valid=False, errors=errors, total_rows=5, valid_rows=4)

        # Should raise RuntimeError for inconsistent_correspondence
        with pytest.raises(RuntimeError):
            _display_normal_validation_results(result)

    @patch("memeid_extractor.validator.logger")
    def test_display_fix_guide_empty_paths(self, mock_logger):
        """Test _display_fix_guide with empty error paths."""
        from memeid_extractor.validator import _display_fix_guide

        _display_fix_guide([])

        # Should not log anything when no error paths
        mock_logger.info.assert_not_called()
