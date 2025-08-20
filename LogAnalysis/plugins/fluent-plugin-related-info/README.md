# fluent-plugin-related-info

[Fluentd](https://fluentd.org/) filter plugin to enrich records with additional information from an external dictionary file (CSV, TSV, or JSON).

This plugin adds fields to incoming records by looking up a key in a dictionary file and merging the corresponding values.

## Features
- **Multiple file formats**: Supports CSV, TSV, and JSON dictionary files with auto-detection
- **Flexible field mapping**: Specify key and value fields, rename fields during merge
- **Real-time updates**: Watches dictionary file and reloads automatically on changes
- **Security features**: Path validation and file size limits to prevent security issues
- **Performance optimization**: Progress display for large files, efficient memory usage
- **Robust error handling**: Graceful handling of malformed files and missing data

## Installation

### RubyGems

```
$ gem install fluent-plugin-related-info
```

### Bundler

Add following line to your Gemfile:

```ruby
gem "fluent-plugin-related-info"
```

And then execute:

```
$ bundle
```

## Configuration Examples

### Basic CSV Configuration
```xml
<filter your.tag>
  @type related_info
  key uid
  <map>
    path /path/to/users.csv
    header true
    key uid
    value name, email
  </map>
</filter>
```

### Advanced Configuration with Security and Field Mapping
```xml
<filter your.tag>
  @type related_info
  key user_id
  names_map name:full_name,email:contact_email
  max_file_size 5242880        # 5MB limit
  strict_path_validation true  # Require absolute paths
  progress_threshold 500       # Show progress for large files
  <map>
    path /var/lib/fluentd/dictionaries/users.csv
    format csv
    header true
    key uid
    value name, email, department
  </map>
</filter>
```

### JSON Configuration
```xml
<filter application.logs>
  @type related_info
  key employee_id
  <map>
    path /etc/fluentd/employee_data.json
    key emp_id
    value full_name, department, location
  </map>
</filter>
```

### TSV with Custom Delimiter
```xml
<filter access.logs>
  @type related_info
  <map>
    path /data/user_info.txt
    format csv
    delimiter "|"
    field_names user_id,username,role,created_at
    key user_id
    value username, role
  </map>
</filter>
```

## Configuration Parameters

### Global Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | string | `map.key` | Field name in incoming records to match against dictionary keys |
| `names_map` | hash | `{}` | Rename fields when adding to records (format: `"original:new,field2:renamed"`) |
| `max_file_size` | integer | `1048576` | Maximum dictionary file size in bytes (1MB default) |
| `strict_path_validation` | bool | `true` | Require absolute paths to prevent path traversal attacks |
| `progress_threshold` | integer | `1000` | Show loading progress for dictionaries with more entries than this |

### Map Section Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | ✅ | Path to dictionary file (CSV, TSV, or JSON) |
| `format` | enum | | File format (`csv`, `tsv`, `json`). Auto-detected from extension if not specified |
| `header` | bool | | Whether CSV file has header row (CSV only) |
| `delimiter` | string | | Custom delimiter for CSV files (CSV/TSV only) |
| `field_names` | array | | Field names for files without headers (CSV/TSV only) |
| `key` | string | ✅ | Field name in dictionary file to use as lookup key |
| `value` | array | ✅ | List of field names in dictionary file to add to records |

## Dictionary File Formats

### CSV Format (with header)
```csv
uid,name,email,department
1001,"Smith, John",john.smith@company.com,Engineering
1002,Mary Johnson,mary.j@company.com,Sales
1003,Bob Wilson,bob.w@company.com,Engineering
```

### TSV Format (tab-separated, no header)
```tsv
1001	John Smith	john.smith@company.com	Engineering
1002	Mary Johnson	mary.j@company.com	Sales
1003	Bob Wilson	bob.w@company.com	Engineering
```

### JSON Format
```json
[
  {
    "uid": 1001,
    "name": "John Smith",
    "email": "john.smith@company.com",
    "department": "Engineering",
    "location": "Tokyo"
  },
  {
    "uid": 1002,
    "name": "Mary Johnson",
    "email": "mary.j@company.com",
    "department": "Sales",
    "location": "Osaka"
  }
]
```

## Security Considerations

- **Path Validation**: By default, only absolute paths are allowed (`strict_path_validation=true`)
- **File Size Limits**: Dictionary files are limited to 1MB by default to prevent memory issues
- **Error Handling**: Plugin gracefully handles malformed files and continues processing

## Performance Notes

- Dictionary files are loaded into memory for fast lookups
- File changes are detected automatically and trigger reloads
- Large files show progress during loading
- Memory usage is optimized for typical dictionary sizes

## Troubleshooting

### Common Error Messages

**"Dictionary file path must be absolute"**
- Solution: Use absolute paths like `/path/to/file.csv` or set `strict_path_validation false`

**"Dictionary file is too large"**
- Solution: Increase `max_file_size` or reduce dictionary file size

**"Failed to parse CSV file"**
- Solution: Check file format, delimiter settings, and CSV structure

**"Configuration error: map.key must be specified"**
- Solution: Add `key field_name` in the `<map>` section

## Development

### Running Tests
```bash
bundle install
bundle exec rake test
```

### Building the Gem
```bash
bundle exec rake build
```

## License

* Copyright(C) 2024- NII Gakunin Cloud
* License: Apache License, Version 2.0
