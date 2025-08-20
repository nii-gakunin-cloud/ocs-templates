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

require "fluent/plugin/filter"
require_relative "filter_attach_file_helper"

module Fluent
  module Plugin
    class AttachFileFilter < Fluent::Plugin::Filter
      Fluent::Plugin.register_filter("attach_file", self)

      include Fluent::Plugin::AttachFileFilterHelper

      config_param :key, :string, desc: "The key in the record whose value will be used as the file path."
      config_param :python_unpickle, :bool, default: false, desc: "Whether to unpickle the file content using Python pickle."
      config_param :as_json, :bool, default: false, desc: "Whether to JSON encode the unpickled data."
      config_param :base_dir, :string, default: nil, desc: "The base directory where the files are located."
      config_param :trim_path_levels, :integer, default: 0, desc: "Number of directory levels to remove from the file path."
      config_param :max_file_size, :integer, default: 10 * 1024 * 1024, desc: "Maximum allowed file size in bytes." # Default is 10MB
      config_param :replace_key, :bool, default: false, desc: "Whether to overwrite the existing file content in the record."
      config_param :output_key, :string, default: nil, desc: "The destination key in the record where the file content will be stored."

      def configure(conf)
        super
        raise Fluent::ConfigError, "key cannot be empty" if @key.nil? || @key.strip.empty?
        raise Fluent::ConfigError, "trim_path_levels must be >= 0" if @trim_path_levels < 0
        raise Fluent::ConfigError, "max_file_size must be > 0" if @max_file_size <= 0
        raise Fluent::ConfigError, "output_key must be specified if replace_key is false" if !@replace_key && @output_key.nil?
      end

      def filter(tag, time, record)
        field_value = record[@key]
        return record if field_value.nil? || field_value.empty?

        begin
          content = load_content(field_value)
          update_record(record, content)
        rescue => e
          log.warn "[#{tag}] [#{time}] Failed to process file: #{e.message}"
          update_record(record, "Warning: #{e.message}")
        end
        record
      end

      private

      def update_record(record, content)
        if @replace_key
          record[@key] = content
        else
          record[@output_key] = content
        end
      end
    end
  end
end
