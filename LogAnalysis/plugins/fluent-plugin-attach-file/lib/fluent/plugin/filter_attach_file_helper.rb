#
# Copyright 2025- NII Gakunin Cloud <cld-office-support@nii.ac.jp>
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

require "json"
# Note: python-pickle gem may show circular require warnings during loading
# This is a known issue with the gem and does not affect functionality
require "python/pickle"

module Fluent
  module Plugin
    module AttachFileFilterHelper

      def load_content(field_value)
        file_path = get_file_path(field_value)
        validate_file_size(file_path, @max_file_size, field_value)
        content = File.read(file_path)
        content = unpickle(content) if @python_unpickle
        content
      rescue Errno::ENOENT, Errno::EACCES => e
        raise "Failed to read file #{field_value}: #{e.message}"
      end

      private

      def unpickle(pickle_data)
        data = Python::Pickle.load(pickle_data)
        if @as_json
          JSON.generate(data)
        else
          data
        end
      end

      def get_file_path(field_value)
        if @trim_path_levels > 0 
          file_path_parts = field_value.split(File::SEPARATOR)
          file_path_parts.shift if file_path_parts[0].empty? # Remove leading empty element if present
          file_path = file_path_parts.drop(@trim_path_levels).join(File::SEPARATOR)
          if file_path.empty?
            raise "File path is empty after removing directory levels: #{field_value}"
          end
        else
          file_path = field_value
        end

        file_path = File.join(@base_dir, file_path) if @base_dir
        
        # Security validation before file system access
        validate_file_path(file_path, @base_dir) if @base_dir
        
        unless File.exist?(file_path)
          raise "File not found: #{field_value}"
        end

        file_path
      end

      def validate_file_size(file_path, max_file_size, field_value)
        if File.size(file_path) > max_file_size
          raise "File size exceeds maximum allowed size: #{field_value}"
        end
      end

      def validate_file_path(file_path, base_dir)
        # Pre-validation: Detect dangerous patterns
        if file_path.include?("..") || file_path.include?("./") || 
           file_path.include?("\0") || file_path.length > 4096
          raise "Invalid file path: potentially unsafe path detected"
        end
        
        begin
          # Resolve symbolic links and normalize paths
          resolved_file_path = File.realpath(file_path)
          resolved_base_dir = File.realpath(base_dir)
        rescue Errno::ENOENT => e
          raise "Path resolution failed: file or directory not found"
        rescue Errno::ELOOP => e
          raise "Path resolution failed: symbolic link loop detected"
        rescue => e
          raise "Path resolution failed: #{e.class}"
        end
        
        # Strict path validation
        unless resolved_file_path.start_with?(resolved_base_dir + File::SEPARATOR) || 
               resolved_file_path == resolved_base_dir
          raise "File access denied: path is outside allowed directory"
        end
      end
    end
  end
end
