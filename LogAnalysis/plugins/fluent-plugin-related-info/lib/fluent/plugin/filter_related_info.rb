#
# Copyright (C) 2024- NII Gakunin Cloud
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

require 'fluent/plugin/filter'
require 'fluent/plugin_helper'
require 'cool.io'
require 'pathname'

module Fluent
  module Plugin
    # RelatedInfoFilter enriches log records with additional information from external dictionary files.
    # 
    # This filter plugin performs lookups in CSV, TSV, or JSON files and merges matching data into
    # incoming records. It supports field mapping, automatic file reloading, and security features.
    # 
    # @example Basic usage with CSV file
    #   <filter application.logs>
    #     @type related_info
    #     key user_id
    #     <map>
    #       path /path/to/users.csv
    #       header true
    #       key uid
    #       value name, email
    #     </map>
    #   </filter>
    # 
    # @see https://github.com/your-org/fluent-plugin-related-info for more examples
    class RelatedInfoFilter < Fluent::Plugin::Filter
      include PluginHelper::Mixin
      Fluent::Plugin.register_filter("related_info", self)

      helpers :event_loop

      desc 'Key field name in incoming records to match against dictionary keys. If not specified, uses map.key value.'
      config_param :key, :string, default: nil

      desc 'Rename fields when adding to records. Format: "original_name:new_name,field2:renamed_field2"'
      config_param :names_map, :hash, default: {}, value_type: :string

      desc 'Maximum dictionary file size in bytes. Protects against loading extremely large files (default: 1MB)'
      config_param :max_file_size, :integer, default: 1048576

      desc 'Require absolute paths for dictionary files to prevent path traversal attacks (recommended: true)'
      config_param :strict_path_validation, :bool, default: true

      desc 'Show loading progress for large dictionaries with more entries than this threshold'
      config_param :progress_threshold, :integer, default: 1000

      config_section :map, required: true, multi: false do
        desc 'Path to the dictionary file (CSV, TSV, or JSON). Use absolute paths when strict_path_validation is enabled.'
        config_param :path, :string
        desc 'Dictionary file format. Auto-detected from file extension if not specified. (csv|tsv|json)'
        config_param :format, :enum, list: [:csv, :tsv, :json], default: nil

        desc 'Whether the CSV file has a header row with field names (CSV only)'
        config_param :header, :bool, default: false
        desc 'Custom delimiter for CSV files. Default: "," for CSV, "\t" for TSV (CSV/TSV only)'
        config_param :delimiter, :string, default: nil

        desc 'Field names for CSV/TSV files without headers. Order must match file columns.'
        config_param :field_names, :array, value_type: :string, default: []

        desc 'Field name in dictionary file to use as lookup key'
        config_param :key, :string
        desc 'List of field names in dictionary file to add to records when key matches'
        config_param :value, :array, value_type: :string
      end

      # Configure the plugin with validation and dictionary loading
      # 
      # @param conf [Fluent::Config::Element] Configuration element
      # @raise [Fluent::ConfigError] When configuration is invalid
      def configure(conf)
        super
        # Auto-detect file format from extension if not specified
        @map["format"] = file_format(@map.path) if @map.format.nil?
        check_params
        @dict = setup_dict
      end

      # Start the plugin and set up file watching for dictionary updates
      def start
        super
        # Watch dictionary file for changes and reload automatically
        watcher = StatWatcher.new(@map.path, @log) do |_prev, _cur|
          @dict = setup_dict
        end
        event_loop_attach(watcher)
      end

      # Filter incoming records by enriching them with dictionary data
      # 
      # @param tag [String] Record tag (unused)
      # @param time [Fluent::EventTime] Record timestamp (unused)
      # @param record [Hash] The record to enrich
      # @return [Hash] The enriched record
      def filter(tag, time, record)
        key = record[@key]
        # Merge dictionary data if key exists and has corresponding entry
        record.merge!(@dict[key]) if key && @dict[key]
        record
      end

      private

      # Auto-detect file format from file extension
      # 
      # @param file [String] File path
      # @return [Symbol] Detected format (:csv, :tsv, :json)
      def file_format(file)
        case File.extname(file)
        when '.csv'
          :csv
        when '.tsv'
          :tsv
        when '.json'
          :json
        else
          :csv  # Default to CSV for unknown extensions
        end
      end


      # Format byte size in human-readable format
      # 
      # @param bytes [Integer] Size in bytes
      # @return [String] Formatted size (e.g., "1.50 MB")
      def format_bytes(bytes)
        units = ['B', 'KB', 'MB', 'GB']
        size = bytes.to_f
        unit_index = 0
        
        while size >= 1024 && unit_index < units.length - 1
          size /= 1024
          unit_index += 1
        end
        
        "%.2f %s" % [size, units[unit_index]]
      end

      def validate_file_path(path)
        return unless @strict_path_validation
        
        unless Pathname.new(path).absolute?
          raise Fluent::ConfigError, "Dictionary file path must be absolute when strict_path_validation is enabled. Got relative path: '#{path}'. Please use an absolute path like '/path/to/your/dictionary.csv' or set strict_path_validation to false."
        end
        
        resolved_path = File.expand_path(path)
        if path != resolved_path
          raise Fluent::ConfigError, "Dictionary file path contains potentially dangerous path traversal characters: '#{path}'. This could be a security risk. Please use a clean absolute path without '..' or symbolic links."
        end
      end

      def validate_file_size(path)
        return unless File.exist?(path)
        
        file_size = File.size(path)
        if file_size > @max_file_size
          raise Fluent::ConfigError, "Dictionary file is too large: #{format_bytes(file_size)} exceeds the limit of #{format_bytes(@max_file_size)}. File: '#{path}'. Consider increasing max_file_size or using a smaller dictionary file."
        end
        
        @log.info("dictionary file size: #{file_size} bytes (limit: #{@max_file_size} bytes)")
      end

      def validate_config_consistency
        # CSV/TSV specific validations
        unless @map.format == :csv
          raise Fluent::ConfigError, "Configuration error: map.header=true is only supported for CSV format, but format is set to '#{@map.format}'. Please remove 'header true' or change format to 'csv'." if @map.header
          raise Fluent::ConfigError, "Configuration error: map.delimiter is only supported for CSV/TSV formats, but format is set to '#{@map.format}'. Please remove the delimiter setting or change format to 'csv'." if @map.delimiter
        end

        # Value field validation
        if @map.value.empty?
          raise Fluent::ConfigError, "Configuration error: map.value must specify at least one field name to extract from the dictionary. Example: value name,email"
        end

        # Key field validation
        if @map.key.nil? || @map.key.empty?
          raise Fluent::ConfigError, "Configuration error: map.key must be specified to identify which field to use for lookups. Example: key user_id"
        end

        # Field names vs header consistency check for CSV/TSV
        if (@map.format == :csv || @map.format == :tsv) && @map.header && !@map.field_names.empty?
          @log.warn("Both map.header=true and map.field_names are specified. map.field_names will override header.")
        end

        # Check for reasonable max_file_size
        if @max_file_size <= 0
          raise Fluent::ConfigError, "Configuration error: max_file_size must be a positive number, got #{@max_file_size}. Please set a positive value like 1048576 (1MB)."
        end

        if @max_file_size < 1024
          @log.warn("max_file_size is very small (#{@max_file_size} bytes). Consider increasing if dictionary loading fails.")
        end
      end

      def validate_file_existence
        unless File.exist?(@map.path)
          raise Fluent::ConfigError, "Dictionary file not found: '#{@map.path}'. Please check the file path exists and is accessible. Use absolute paths when strict_path_validation is enabled."
        end

        unless File.readable?(@map.path)
          raise Fluent::ConfigError, "Dictionary file is not readable: '#{@map.path}'. Please check file permissions. The Fluentd process needs read access to this file."
        end
      end

      def check_params
        validate_config_consistency
        @key = @map.key if @key.nil?
        
        validate_file_path(@map.path)
        validate_file_existence
        validate_file_size(@map.path)
      end

      # Load dictionary from file and build lookup hash
      # 
      # @return [Hash] Dictionary hash for lookups
      def setup_dict
        start_time = Time.now
        validate_file_size(@map.path)
        @log.info("loading dictionary file: #{@map.path} (format: #{@map.format})")
        
        begin
          ret = case @map.format
          when :csv, :tsv
            load_csv_dict
          when :json
            load_json_dict
          else
            raise "Unsupported dictionary format '#{@map.format}' for file '#{@map.path}'. Supported formats are: csv, tsv, json."
          end

          dict_hash = {}
          valid_rows = 0
          invalid_rows = 0
          duplicate_keys = 0
          missing_fields = Hash.new(0)
          
          total_rows = ret.size
          show_progress = total_rows > @progress_threshold
          last_progress_time = Time.now
          progress_interval = 2.0  # seconds
          
          if show_progress
            @log.info("Processing large dictionary: #{total_rows} entries (showing progress every #{progress_interval}s)")
          end

          ret.each_with_index do |row, index|
            # Show progress for large files
            if show_progress && (Time.now - last_progress_time) >= progress_interval
              processed = index + 1
              percentage = (processed.to_f / total_rows * 100).round(1)
              rate = processed / (Time.now - start_time)
              eta_seconds = (total_rows - processed) / rate
              eta_text = eta_seconds > 60 ? "#{(eta_seconds / 60).round(0)}m" : "#{eta_seconds.round(0)}s"
              
              @log.info("Progress: #{processed}/#{total_rows} (#{percentage}%) - #{rate.round(0)} entries/sec - ETA: #{eta_text}")
              last_progress_time = Time.now
            end
            begin
              key = row[@map.key]
              if key.nil?
                @log.warn("Row #{index + 1}: missing key field '#{@map.key}', skipping")
                invalid_rows += 1
                next
              end

              # Check for duplicate keys
              if dict_hash.key?(key)
                @log.warn("Row #{index + 1}: duplicate key '#{key}' found, overriding previous entry")
                duplicate_keys += 1
              end

              values = {}
              @map.value.each do |field_name|
                if row[field_name]
                  mapped_name = @names_map[field_name] || field_name
                  values[mapped_name] = row[field_name]
                else
                  missing_fields[field_name] += 1
                end
              end

              if values.empty?
                @log.warn("Row #{index + 1}: no valid value fields found for key '#{key}', skipping")
                invalid_rows += 1
                next
              end

              dict_hash[key] = values
              valid_rows += 1
            rescue => e
              @log.warn("Row #{index + 1}: failed to process (#{e.class}: #{e.message}), skipping")
              invalid_rows += 1
            end
          end

          load_time = Time.now - start_time
          
          @log.info("dictionary loaded successfully in #{load_time.round(3)}s: #{valid_rows} valid rows, #{invalid_rows} invalid rows")
          
          if duplicate_keys > 0
            @log.warn("Found #{duplicate_keys} duplicate keys during dictionary loading")
          end
          
          # Report missing fields summary
          unless missing_fields.empty?
            missing_fields.each do |field, count|
              percentage = (count.to_f / (valid_rows + invalid_rows) * 100).round(1)
              @log.info("Field '#{field}' was missing in #{count} rows (#{percentage}%)")
            end
          end

          # Performance metrics
          entries_per_second = ((valid_rows + invalid_rows) / load_time).round(0)
          @log.info("Performance: #{entries_per_second} entries/sec, #{dict_hash.size} entries loaded")

          dict_hash
        rescue => e
          load_time = Time.now - start_time
          @log.error("Failed to load dictionary after #{load_time.round(3)}s: #{e.class}: #{e.message}")
          @log.error("File: #{@map.path}, Format: #{@map.format}, Key field: #{@map.key}")
          @log.error("Value fields: #{@map.value.join(', ')}")
          @log.error(e.backtrace.join("\n"))
          {}
        end
      end

      def load_csv_dict
        require 'csv'
        options = { converters: :numeric }
        options[:headers] = @map.header if @map.header
        options[:headers] = @map.field_names unless @map.field_names.empty?
        options[:col_sep] = (@map.format == :tsv ? "\t" : @map.delimiter) if @map.delimiter || @map.format == :tsv
        
        # Add safety options for CSV parsing
        options[:liberal_parsing] = false
        options[:skip_blanks] = true
        
        CSV.read(@map.path, **options)
      rescue CSV::MalformedCSVError => e
        raise "Failed to parse CSV file '#{@map.path}': #{e.message}. Please check the file format, delimiter settings, and ensure proper CSV structure."
      end

      def load_json_dict
        require 'json'
        content = File.read(@map.path)
        JSON.parse(content)
      rescue JSON::ParserError => e
        raise "Failed to parse JSON file '#{@map.path}': #{e.message}. Please check the file contains valid JSON syntax."
      end
    
      # StatWatcher monitors dictionary files for changes and triggers reloads
      # 
      # This class extends Coolio::StatWatcher to provide robust file monitoring
      # with error tracking and status reporting.
      class StatWatcher < Coolio::StatWatcher
        # Initialize the file watcher
        # 
        # @param path [String] Path to file to watch
        # @param log [Fluent::Log] Logger instance
        # @param callback [Proc] Callback to execute on file changes
        def initialize(path, log, &callback)
          @path = path
          @log = log
          @callback = callback
          @last_success_time = Time.now
          @last_error_time = nil
          @error_count = 0
          super(@path)
        end

        # Handle file change events
        # 
        # @param prev [File::Stat] Previous file status
        # @param cur [File::Stat] Current file status
        def on_change(prev, cur)
          begin
            @log.debug("File change detected: #{@path} (size: #{cur.size}, mtime: #{cur.mtime})")
            @callback.call(prev, cur)
            
            # Reset error tracking on success
            @last_success_time = Time.now
            if @error_count > 0
              @log.info("Dictionary reload succeeded after #{@error_count} previous error(s)")
              @error_count = 0
              @last_error_time = nil
            end
          rescue => e
            @error_count += 1
            @last_error_time = Time.now

            @log.error("StatWatcher callback failed: #{e.class}: #{e.message}")
            @log.error("File: #{@path}, Previous size: #{prev&.size}, Current size: #{cur&.size}")
            @log.error("Error count: #{@error_count}, Last success: #{@last_success_time}")
            @log.error("This error is likely due to file format issues or configuration problems.")
            @log.error("Manual intervention may be required to fix the dictionary file.")
            @log.error(e.backtrace.join("\n"))
          end
        end

        # Check if the watcher is in a healthy state
        # 
        # @return [Boolean] true if healthy, false if experiencing persistent errors
        def healthy?
          # Consider unhealthy if there have been recent errors without success
          return true if @last_error_time.nil?
          return false if @error_count >= 5  # Many consecutive errors
          
          # Consider unhealthy if errors persist for more than 60 seconds
          Time.now - @last_error_time < 60
        end

        # Get current status description
        # 
        # @return [String] Human-readable status description
        def status
          if @last_error_time.nil?
            "healthy (last success: #{@last_success_time})"
          else
            "error (#{@error_count} errors since #{@last_success_time})"
          end
        end
      end
    end
  end
end
