#
# Copyright 2024- NII Gakunin Cloud
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

require "fluent/plugin/parser"

require "json"

module Fluent
  module Plugin
    class LcWrapperParser < Fluent::Plugin::Parser
      Fluent::Plugin.register_parser("lc_wrapper", self)

      config_set_default :types, {
        'uid' => 'integer',
        'gid' => 'integer',
        'start_time' => 'time',
        'end_time' => 'time',
      }
      config_set_default :time_format, '%Y-%m-%d %H:%M:%S(%Z)'

      SEPARATOR = /----\n/m
      CHUNKS_KEYWORDS_TEXT = "chunks with matched keywords or errors"

      OUTPUT_PATTERN = %r{
        (?<head>.+?)                     # Header part
        gid:\s*(?<gid>\d+)\s*\n          # Extract gid
        start\s+time:\s*(?<start_time>[^\n]+)\n # Start time
        #{SEPARATOR}                     # Separator
        (?<output>.*)                    # Output part (greedy - will backtrack)
        #{SEPARATOR}                     # Separator
        end\s+time:\s*(?<end_time>[^\n]+)\n # End time
        \d+\s+#{Regexp.escape(CHUNKS_KEYWORDS_TEXT)}\n # Fixed string
        #{SEPARATOR}                     # Separator
        (?<foot>.+)                      # Footer part
      }mx

      INPUT_PATTERN = %r{
        (?<input>.*)                     # Input part (greedy - will backtrack)
        #{SEPARATOR}                     # Separator
        path:\s*(?<path>[^\n]+)\n        # Extract path
        (?<foot>.+)                      # Footer part
      }mx

      def parse(text)
        values = parse_lc_wrapper(text)
        time, record = convert_values(parse_time(values), values)
        yield time, record
      end

      private

      # Extracts key-value pairs from footer sections
      # Note: When called multiple times (OUTPUT_PATTERN and INPUT_PATTERN),
      # later values will overwrite earlier ones for duplicate keys
      def extract_foot_params(foot)
        foot.lines(chomp: true).each_with_object({}) do |line, params|
          key, value = line.split(/:\s*/, 2)
          params[key] = value if key && value
        end
      end

      def parse_lc_wrapper(text)
        params = {}
        head, rest = text.split(SEPARATOR, 2)

        if cell_meme?(head)
          params['lc_cell_meme'] = cell_meme_id(head)
        else
          rest = text
        end

        m = OUTPUT_PATTERN.match(rest)
        raise Fluent::Plugin::Parser::ParserError, "Failed to parse output pattern" if m.nil?

        params.merge!(
          'gid' => m[:gid],
          'start_time' => m[:start_time],
          'end_time' => m[:end_time],
          'output' => m[:output]
        )
        params.merge!(extract_foot_params(m[:foot]))

        rest = m[:head]
        m = INPUT_PATTERN.match(rest)
        raise Fluent::Plugin::Parser::ParserError, "Failed to parse input pattern" if m.nil?

        params.merge!(
          'input' => m[:input],
          'path' => m[:path]
        )
        params.merge!(extract_foot_params(m[:foot]))

        params
      end

      def cell_meme?(text)
        begin
          value = JSON.parse(text)
          if value.is_a?(Hash) && value.key?("lc_cell_meme")
            meme = value["lc_cell_meme"]
            return meme.is_a?(Hash) && meme.key?("current")
          end
          return false
        rescue
          return false
        end
      end

      def cell_meme_id(text)
        begin
          value = JSON.parse(text)
          return value["lc_cell_meme"]["current"]
        rescue JSON::ParserError, StandardError
          return nil
        end
      end
    end
  end
end
