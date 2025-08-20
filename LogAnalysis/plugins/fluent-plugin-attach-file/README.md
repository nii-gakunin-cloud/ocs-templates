# fluent-plugin-attach-file

[Fluentd](https://fluentd.org/) filter plugin to attach file content to log records.

This plugin reads the content of a file specified in a log record, optionally unpickles the content, and updates the record with the file's content. It supports configuration options for base directory, directory trimming, maximum file size, overwrite/destination key, and more.

## Installation

### RubyGems

```
$ gem install fluent-plugin-attach-file
```

### Bundler

Add the following line to your Gemfile:

```ruby
gem "fluent-plugin-attach-file"
```

And then execute:

```
$ bundle
```

## Configuration

### Example Configuration

```conf
<filter **>
  @type attach_file
  key result
  base_dir /jupyter/users
  trim_path_levels 1
  max_file_size 10240 # 10KiB
  python_unpickle true
  as_json true
  replace_key false
  output_key attached_content
</filter>
```

### Parameters

#### Required Parameters
- `key` (string, required): The key in the record whose value will be used as the file path. Cannot be empty or whitespace only.

#### Security Parameters
- `base_dir` (string, optional): The base directory where the files are located. **Highly recommended** for security. Defaults to `nil`.
- `max_file_size` (integer, optional): Maximum allowed file size in bytes. Helps prevent DoS attacks. Defaults to `10 * 1024 * 1024` (10MB).

#### Path Processing Parameters
- `trim_path_levels` (integer, optional): Number of directory levels to remove from the file path. Must be >= 0. Defaults to `0`.

#### Content Processing Parameters
- `python_unpickle` (bool, optional): Whether to unpickle the file content using Python pickle. Defaults to `false`.
- `as_json` (bool, optional): Whether to JSON encode the unpickled data. If `true`, the unpickled Python object will be converted to a JSON string. Defaults to `false`.

#### Output Parameters
- `replace_key` (bool, optional): Whether to overwrite the existing file content in the record. Defaults to `false`.
- `output_key` (string, optional): The destination key in the record where the file content will be stored. **Required** if `replace_key` is `false`.

### Configuration Validation

The plugin performs comprehensive validation of configuration parameters:

- **Empty key validation**: Prevents empty or whitespace-only `key` values
- **Numeric range validation**: Ensures `trim_path_levels >= 0` and `max_file_size > 0`
- **Output configuration validation**: Requires `output_key` when `replace_key` is `false`

Invalid configurations will result in `Fluent::ConfigError` with descriptive error messages.

## Features

- Reads file content based on a key in the log record.
- Supports unpickling of file content (as Ruby object or JSON string).
- Can JSON encode unpickled data for easier downstream processing.
- Validates file size and ensures it does not exceed the configured maximum.
- Removes specified directory levels from the file path.
- Ensures file paths are within the base directory to prevent directory traversal attacks.
- Supports writing file content to a different key (`output_key`) or to the original key (when `replace_key` is true).

## Security Features

This plugin includes enhanced security measures to protect against various attack vectors:

### Path Validation
- **Directory Traversal Protection**: Prevents access using `../` or `./` patterns
- **Null Byte Injection Protection**: Blocks null byte characters in file paths
- **Path Length Limits**: Restricts file paths to reasonable lengths (4096 characters)
- **Symbolic Link Resolution**: Resolves and validates symbolic links to prevent unauthorized access

### Access Control
- **Base Directory Enforcement**: All file access is restricted to the specified `base_dir`
- **Real Path Validation**: Uses `File.realpath` to normalize and validate paths
- **File Size Limits**: Configurable maximum file size to prevent resource exhaustion

### Input Validation
- **Configuration Validation**: Comprehensive validation of all configuration parameters
- **Runtime Input Checks**: Validates file paths and parameters during execution
- **Error Handling**: Secure error messages that don't leak sensitive information

### Security Best Practices

When using this plugin in production:

1. **Always set `base_dir`** to restrict file access to a specific directory
2. **Use appropriate `max_file_size` limits** for your environment to prevent DoS attacks
3. **Monitor log output** for security warnings and suspicious activity
4. **Regularly update** the plugin to receive latest security enhancements
5. **Validate input sources** to ensure only trusted log sources can specify file paths

## License

* Copyright(C) 2025- NII Gakunin Cloud
* License: Apache License, Version 2.0
