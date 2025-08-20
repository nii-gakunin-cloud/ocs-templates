# memeid-extractor

[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](https://github.com/nii-gakunin-cloud/ocs-templates)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## Table of Contents

- [About](#about)
- [Installation](#installation)
- [Features](#features)
- [Usage](#usage)
- [Data Validation](#data-validation)
- [Directory Watching](#directory-watching)
- [Output Format](#output-format)
- [License](#license)

## About

This tool extracts **meme IDs** and related metadata from Jupyter Notebook files with comprehensive data validation. Meme IDs are unique cell identifiers automatically generated and managed by Jupyter extensions that track notebook cell execution and lineage.

### What are Meme IDs?

- **Cell meme IDs** (`lc_cell_meme`): Unique identifiers for individual notebook cells
- **Notebook meme IDs** (`lc_notebook_meme`): Unique identifiers for entire notebooks
- **Purpose**: Enable tracking of cell execution history, lineage, and relationships across notebook sessions

These IDs are essential for educational analytics, reproducible research, and understanding notebook usage patterns in learning environments.

### Required Jupyter Environment

This tool processes notebooks created in Jupyter environments with the following extensions enabled:

- **[Jupyter-LC_wrapper](https://github.com/NII-cloud-operation/Jupyter-LC_wrapper)**: Generates and manages meme IDs in notebook metadata
- **[Jupyter-LC_nblineage](https://github.com/NII-cloud-operation/Jupyter-LC_nblineage)**: Provides lineage tracking and meme ID management commands

Both extensions work together to create notebooks with proper meme ID metadata that this tool can extract and validate.

## Installation

```console
pip install memeid-extractor
```

### Requirements

- Python 3.11 or higher
- Jupyter notebooks created with Jupyter-LC_wrapper and Jupyter-LC_nblineage extensions enabled

## Features

- **Bulk extraction**: Process multiple Jupyter Notebook files at once
- **CSV output**: Generate structured CSV files with customizable formatting
- **Data validation**: Automatic validation with error detection and fix guidance
- **Flexible filtering**: Include/exclude notebooks using glob patterns
- **Question label extraction**: Extract labels from markdown cells using regex patterns
- **Directory watching**: Automatic CSV updates when notebooks change
- **Course server support**: Multi-course deployment support for CoursewareHub
- **Command-line interface**: Easy-to-use CLI with comprehensive options

## Usage

After installation, use the command line:

```console
memeid-extractor --notebook-path <notebook_dir> --csv-file <output.csv> [options]
```

### Basic Examples

```console
# Basic extraction with validation
memeid-extractor --notebook-path ./notebooks --csv-file output.csv

# Disable validation
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --no-validate

# Strict validation (abort on errors)
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --strict-validate

# Include course server column for multi-course deployments
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --course-server

# Extract question labels and sort by modification time
memeid-extractor --notebook-path ./notebooks --csv-file output.csv \
  --pattern "Question \d+" --sort-order mtime
```

### Command Line Options

#### Core Options
- `-n, --notebook-path`   Directory containing Jupyter notebooks (default: `/jupyter/admin/textbook`)
- `-o, --csv-file`        Output CSV file path (default: `meme.csv`)
- `-I, --include`         Glob pattern for files to include (default: `**/*.ipynb`)
- `-X, --exclude`         Glob pattern for files to exclude
- `-F, --format`          Format string for question numbers (default: `{:02}-{:03}`)

#### Data Processing Options
- `-p, --pattern`         Regex pattern to extract question labels from markdown
- `-B, --hold-branch-number`  Keep branch number in meme IDs (default: False)
- `-A, --absolute-path`   Use absolute paths in output (default: False)
- `-C, --course-server`   Include course_server column in CSV output (default: False)
- `-S, --sort-order`      Sort order for processing files: `mtime`, `ctime`, `name` (default: `ctime`)

#### Validation Options
- `--no-validate`         Disable CSV validation (default: validation enabled)
- `--strict-validate`     Enable strict validation mode (stops on first error)
- `-q, --quiet`           Suppress validation result output
- `-v, --verbose`         Show detailed validation results

#### Watch Mode Options
- `-W, --watch`           Watch directory for changes and update CSV automatically
- `-d, --delay`           Delay (seconds) before updating CSV after a change (default: 10)

#### Utility Options
- `-V, --version`         Show the version of memeid_extractor
- `-h, --help`            Show help message and exit

For full CLI help, run:

```console
memeid-extractor --help
```

## Data Validation

memeid-extractor includes comprehensive data validation to ensure CSV output integrity and detect common issues in notebook meme IDs.

### Validation Features

- **Automatic validation**: Enabled by default for all extractions
- **Missing value detection**: Identifies cells/notebooks without required meme IDs
- **Duplicate detection**: Finds duplicate cell meme IDs across the entire dataset
- **1:1 correspondence**: Validates that notebook paths and notebook meme IDs have proper relationships
- **Fix guidance**: Provides specific `jupyter nblineage` commands (from Jupyter-LC_nblineage) to resolve issues

### Validation Modes

```console
# Default: validation enabled with normal output
memeid-extractor --notebook-path ./notebooks --csv-file output.csv

# Disable validation entirely
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --no-validate

# Strict mode: abort CSV generation if validation fails
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --strict-validate

# Quiet mode: suppress validation output (exit code only)
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --quiet

# Verbose mode: detailed validation report
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --verbose
```

### Validation Output Example

```
Validation errors found:
  notebook1.ipynb:
    Missing values: lc_cell_meme
    Duplicate values: lc_notebook_meme
  notebook2.ipynb:
    Path conflicts: notebook1.ipynb

To fix these errors, run:
  jupyter nblineage new-root-meme notebook1.ipynb notebook1.fixed.ipynb
  jupyter nblineage new-root-meme notebook2.ipynb notebook2.fixed.ipynb
```

### Validation Rules

1. **Missing Values**: All cells must have `lc_cell_meme` and notebooks must have `lc_notebook_meme`
2. **Cell Meme Uniqueness**: `lc_cell_meme` values must be unique across all notebooks
3. **Notebook Correspondence**: Each `textbook_path` must correspond to exactly one `lc_notebook_meme`

### Return Codes

- **0**: Success (validation passed or disabled)
- **1**: Validation failed (when validation is enabled)

## Directory Watching

To automatically update the CSV file when notebooks are added/modified/deleted, use the `--watch` option:

```console
# Basic watching with validation
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --watch

# Watch with custom delay and strict validation
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --watch \
  --delay 5 --strict-validate

# Watch in quiet mode (for automated systems)
memeid-extractor --notebook-path ./notebooks --csv-file output.csv --watch --quiet
```

This will monitor the directory and update the CSV after changes, with an optional `--delay` before each update. **Watch mode includes validation by default** - the CSV will be validated after each update.

## Output Format

The generated CSV file contains the following columns:

| Column | Description |
|--------|-------------|
| `qno` | Question number (formatted as specified, e.g., "01-002") |
| `qlabel` | Question label extracted from markdown (if pattern provided) |
| `lc_cell_meme` | Cell meme ID from Jupyter-LC_wrapper |
| `lc_notebook_meme` | Notebook meme ID from Jupyter-LC_wrapper |
| `textbook_path` | Path to the notebook file |
| `course_server` | Course server name (first directory component) - Optional |
| `code` | Source code from the cell |

#### Column Details

- **qlabel**: Question label from markdown (optional, requires `--pattern`)
- **course_server**: Course server name (optional, requires `--course-server`)
- **lc_cell_meme**: Cell meme ID (branch numbers may be removed)
- **textbook_path**: Path to notebook file (relative or absolute)

#### Course Server Column (Optional)

The `course_server` column is **optional** and is only included when the `--course-server` flag is enabled. This feature is designed for [CoursewareHub](https://github.com/NII-cloud-operation/CoursewareHub-LC_platform) multi-course deployments.

When enabled, the `course_server` column contains the first directory component from the `textbook_path`:

- **Relative paths**: `course1/chapter1/test.ipynb` → `course_server = "course1"`
- **Absolute paths**: `/notebooks/course1/chapter1/test.ipynb` → `course_server = "course1"` (relative to notebook_path)
- **No subdirectories**: `test.ipynb` → `course_server = ""` (empty string)

For absolute paths, the tool computes the relative path from the `--notebook-path` directory before extracting the course server name. If the absolute path is outside the notebook directory, a warning is logged and `course_server` is set to an empty string.

**Default behavior**: The `course_server` column is **not included** unless explicitly enabled with `--course-server` or `COURSE_SERVER=true`.

### Environment Variables

You can set default values using environment variables:

```bash
export NB_PATH="/path/to/notebooks"
export MEME_CSV_FILE="output.csv" 
export QLABEL_PATTERN="Question \d+"
export QNO_FORMAT="{:02}-{:03}"
export COURSE_SERVER="true"  # Enable course_server column
```

## License

* Copyright(C) 2025-present NII Gakunin Cloud
* License: Apache License, Version 2.0

---

**memeid-extractor** - Extract meme IDs from Jupyter notebooks for educational analytics and research.