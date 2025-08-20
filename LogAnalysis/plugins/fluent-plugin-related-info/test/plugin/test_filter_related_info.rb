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

require "helper"
require "fluent/plugin/filter_related_info.rb"
require "csv"
require "json"

class RelatedInfoFilterTest < Test::Unit::TestCase
  setup do
    Fluent::Test.setup
  end

  sub_test_case "filter" do
    sub_test_case "csv_dict" do
      setup do
        text = <<~'EOF'
          1001,user01,user01@example.org
          1002,user02,user02@example.org
          1003,user03,user03@example.org
        EOF
        File.write("test.csv", text)
      end

      teardown do
        File.unlink("test.csv")
      end

      test "add email" do
        d = create_driver(%[
          <map>
            path #{File.expand_path("test.csv")}
            field_names uid, name, email
            key uid
            value email
          </map>
        ])
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
          d.feed("test", 2, {"uid" => 1002, "message" => "hello 1002"})
          d.feed("test", 3, {"uid" => 1003, "message" => "hello 1003"})
        end
        d.filtered_records.each do |record|
          assert_true(record.has_key?("email"))
        end
      end
    end

    sub_test_case "etc_passwd" do
      setup do
        text = <<~'EOF'
          user01:x:1001:1001:user01:/home/user01:/bin/bash
          user02:x:1002:1002:user02:/home/user02:/bin/bash
          user03:x:1003:1003:user03:/home/user03:/bin/bash
        EOF
        File.write("etc_passwd", text)
      end

      teardown do
        File.unlink("etc_passwd")
      end

      test "add email" do
        d = create_driver(%[
          <map>
            path #{File.expand_path("etc_passwd")}
            delimiter ":"
            field_names name, x, uid
            key uid
            value name
          </map>
        ])
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
          d.feed("test", 2, {"uid" => 1002, "message" => "hello 1002"})
          d.feed("test", 3, {"uid" => 1003, "message" => "hello 1003"})
        end
        d.filtered_records.each do |record|
          assert_true(record.has_key?("name"))
        end
      end
    end

    sub_test_case "csv_header_dict" do
      setup do
        text = <<~'EOF'
          uid,name,email
          1001,user01,user01@example.org
          1002,user02,user02@example.org
          1003,user03,user03@example.org
        EOF
        File.write("test.csv", text)
      end

      teardown do
        File.unlink("test.csv")
      end

      test "add email" do
        d = create_driver(%[
          <map>
            path #{File.expand_path("test.csv")}
            header true
            key uid
            value email
          </map>
        ])
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
          d.feed("test", 2, {"uid" => 1002, "message" => "hello 1002"})
          d.feed("test", 3, {"uid" => 1003, "message" => "hello 1003"})
        end
        d.filtered_records.each do |record|
          assert_true(record.has_key?("email"))
        end
      end
    end

    sub_test_case "tsv_dict" do
      setup do
        text = <<~"EOF"
          1001\tuser01\tuser01@example.org
          1002\tuser02\tuser02@example.org
          1003\tuser03\tuser03@example.org
        EOF
        File.write("test.tsv", text)
      end

      teardown do
        File.unlink("test.tsv")
      end

      test "add email" do
        d = create_driver(%[
          <map>
            path #{File.expand_path("test.tsv")}
            field_names uid, name, email
            key uid
            value email
          </map>
        ])
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
          d.feed("test", 2, {"uid" => 1002, "message" => "hello 1002"})
          d.feed("test", 3, {"uid" => 1003, "message" => "hello 1003"})
        end
        d.filtered_records.each do |record|
          assert_true(record.has_key?("email"))
        end
      end
    end

    sub_test_case "json" do
      setup do
        text = <<~'EOF'
          [
            {"uid": 1001, "name": "user01", "email": "user01@example.org"},
            {"uid": 1002, "name": "user02", "email": "user02@example.org"},
            {"uid": 1003, "name": "user03", "email": "user03@example.org"}
          ]
        EOF
        File.write("test.json", text)
      end

      teardown do
        File.unlink("test.json")
      end

      test "add email" do
        d = create_driver(%[
          <map>
            path #{File.expand_path("test.json")}
            key uid
            value email
          </map>
        ])
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
          d.feed("test", 2, {"uid" => 1002, "message" => "hello 1002"})
          d.feed("test", 3, {"uid" => 1003, "message" => "hello 1003"})
        end
        d.filtered_records.each do |record|
          assert_true(record.has_key?("email"))
        end
      end

      test "rename field names" do
        d = create_driver(%[
          names_map email:mail,name:user_name
          <map>
            path #{File.expand_path("test.json")}
            key uid
            value email, name
          </map>
        ])
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
          d.feed("test", 2, {"uid" => 1002, "message" => "hello 1002"})
          d.feed("test", 3, {"uid" => 1003, "message" => "hello 1003"})
        end
        d.filtered_records.each do |record|
          assert_true(record.has_key?("mail"))
          assert_true(record.has_key?("user_name"))
        end
      end

      test "ref key name" do
        d = create_driver(%[
          key id
          <map>
            path #{File.expand_path("test.json")}
            key uid
            value email
          </map>
        ])
        d.run do
          d.feed("test", 1, {"id" => 1001, "message" => "hello 1001"})
          d.feed("test", 2, {"id" => 1002, "message" => "hello 1002"})
          d.feed("test", 3, {"id" => 1003, "message" => "hello 1003"})
        end
        d.filtered_records.each do |record|
          assert_true(record.has_key?("email"))
        end
      end
    end

    sub_test_case "security_features" do
      setup do
        text = <<~'EOF'
          {"uid": 1001, "name": "user01", "email": "user01@example.org"}
        EOF
        File.write("test.json", text)
        
        # Create a large file for size limit testing
        large_content = "["
        1000.times do |i|
          large_content << "{\"uid\": #{i}, \"name\": \"user#{i}\", \"email\": \"user#{i}@example.org\"}"
          large_content << "," unless i == 999
        end
        large_content << "]"
        File.write("large_test.json", large_content)
      end

      teardown do
        File.unlink("test.json") if File.exist?("test.json")
        File.unlink("large_test.json") if File.exist?("large_test.json")
      end

      test "strict_path_validation with relative path" do
        assert_raise(Fluent::ConfigError) do
          create_driver(%[
            strict_path_validation true
            <map>
              path test.json
              key uid
              value email
            </map>
          ])
        end
      end

      test "strict_path_validation with absolute path" do
        absolute_path = File.expand_path("test.json")
        d = create_driver(%[
          strict_path_validation true
          <map>
            path #{absolute_path}
            key uid
            value email
          </map>
        ])
        assert_nothing_raised { d }
      end

      test "strict_path_validation can be disabled" do
        d = create_driver(%[
          strict_path_validation false
          <map>
            path test.json
            key uid
            value email
          </map>
        ])
        assert_nothing_raised { d }
      end

      test "max_file_size limit" do
        file_size = File.size("large_test.json")
        assert_raise(Fluent::ConfigError) do
          create_driver(%[
            max_file_size #{file_size - 1}
            strict_path_validation false
            <map>
              path large_test.json
              key uid
              value email
            </map>
          ])
        end
      end

      test "max_file_size within limit" do
        file_size = File.size("test.json")
        d = create_driver(%[
          max_file_size #{file_size + 1000}
          strict_path_validation false
          <map>
            path test.json
            key uid
            value email
          </map>
        ])
        assert_nothing_raised { d }
      end

      test "malformed json handling" do
        File.write("malformed.json", '{"uid": 1001, "name": "user01", "email": "user01@example.org"')  # Missing closing brace
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path malformed.json
            key uid
            value email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
        end
        
        # Should not crash, should return original record without additional fields
        assert_equal(1, d.filtered_records.size)
        assert_equal({"uid" => 1001, "message" => "hello 1001"}, d.filtered_records[0])
        
        File.unlink("malformed.json") if File.exist?("malformed.json")
      end
    end

    sub_test_case "error_handling" do
      setup do
        text = <<~'EOF'
          [
            {"uid": 1001, "name": "user01", "email": "user01@example.org"},
            {"uid": 1002, "name": "user02", "email": "user02@example.org"}
          ]
        EOF
        File.write("valid_test.json", text)
        
        # Create a CSV with missing key fields for testing
        csv_text = <<~'EOF'
          uid,name,email
          1001,user01,user01@example.org
          ,user02,user02@example.org
          1003,user03,user03@example.org
        EOF
        File.write("missing_key.csv", csv_text)
        
        # Create a CSV with duplicate keys
        csv_dup_text = <<~'EOF'
          uid,name,email
          1001,user01,user01@example.org
          1001,user01_duplicate,user01_dup@example.org
          1002,user02,user02@example.org
        EOF
        File.write("duplicate_key.csv", csv_dup_text)
      end

      teardown do
        File.unlink("valid_test.json") if File.exist?("valid_test.json")
        File.unlink("missing_key.csv") if File.exist?("missing_key.csv")
        File.unlink("duplicate_key.csv") if File.exist?("duplicate_key.csv")
        File.unlink("nonexistent.json") if File.exist?("nonexistent.json")
      end

      test "missing key field validation" do
        assert_raise(Fluent::ConfigError) do
          create_driver(%[
            strict_path_validation false
            <map>
              path #{File.expand_path("valid_test.json")}
              value email
            </map>
          ])
        end
      end

      test "empty value field validation" do
        assert_raise(Fluent::ConfigError) do
          create_driver(%[
            strict_path_validation false
            <map>
              path #{File.expand_path("valid_test.json")}
              key uid
            </map>
          ])
        end
      end

      test "negative max_file_size validation" do
        assert_raise(Fluent::ConfigError) do
          create_driver(%[
            max_file_size -1
            strict_path_validation false
            <map>
              path #{File.expand_path("valid_test.json")}
              key uid
              value email
            </map>
          ])
        end
      end

      test "nonexistent file validation" do
        assert_raise(Fluent::ConfigError) do
          create_driver(%[
            strict_path_validation false
            <map>
              path nonexistent.json
              key uid
              value email
            </map>
          ])
        end
      end

      test "duplicate key handling" do
        d = create_driver(%[
          strict_path_validation false
          <map>
            path #{File.expand_path("duplicate_key.csv")}
            header true
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
          d.feed("test", 2, {"uid" => 1002, "message" => "hello 1002"})
        end
        
        # Should handle duplicates gracefully (last one wins)
        assert_equal(2, d.filtered_records.size)
        # The duplicate key should have the last entry's data
        record_1001 = d.filtered_records.find { |r| r["uid"] == 1001 }
        assert_equal("user01_duplicate", record_1001["name"])
      end

      test "missing key rows handling" do
        d = create_driver(%[
          strict_path_validation false
          <map>
            path #{File.expand_path("missing_key.csv")}
            header true
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
          d.feed("test", 2, {"uid" => 1002, "message" => "hello 1002"})
          d.feed("test", 3, {"uid" => 1003, "message" => "hello 1003"})
        end
        
        # Should skip rows with missing keys but process valid ones
        assert_equal(3, d.filtered_records.size)
        
        # Check that valid records got their data
        record_1001 = d.filtered_records.find { |r| r["uid"] == 1001 }
        assert_true(record_1001.has_key?("name"))
        assert_equal("user01", record_1001["name"])
        
        # Record with missing key should not get additional data
        record_1002 = d.filtered_records.find { |r| r["uid"] == 1002 }
        assert_false(record_1002.has_key?("name"))
        
        record_1003 = d.filtered_records.find { |r| r["uid"] == 1003 }
        assert_true(record_1003.has_key?("name"))
        assert_equal("user03", record_1003["name"])
      end
    end

    sub_test_case "performance_monitoring" do
      setup do
        # Create a large JSON file for performance testing
        large_entries = []
        200.times do |i|
          large_entries << {
            "uid" => 2000 + i,
            "name" => "user_large_#{i}" * 10,  # Make strings longer
            "email" => "user_large_#{i}" * 5 + "@example.org",
            "department" => "Engineering Department with Long Name" * 3,
            "location" => "Tokyo Office Building Floor #{i % 20}" * 2,
            "description" => ("This is a test user with a very long description field for testing purposes. " * 3)
          }
        end
        File.write("large_test_perf.json", JSON.generate(large_entries))
        
        # Create a small JSON for testing
        small_entries = [
          {"uid" => 3001, "name" => "user_small", "email" => "small@example.org"}
        ]
        File.write("small_test_perf.json", JSON.generate(small_entries))
      end

      teardown do
        File.unlink("large_test_perf.json") if File.exist?("large_test_perf.json")
        File.unlink("small_test_perf.json") if File.exist?("small_test_perf.json")
      end


      test "progress threshold configuration" do
        # Test with low progress threshold to trigger progress display
        d = create_driver(%[
          progress_threshold 10
          strict_path_validation false
          <map>
            path #{File.expand_path("large_test_perf.json")}
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 2001, "message" => "hello"})
        end
        
        # Should process successfully
        assert_equal(1, d.filtered_records.size)
        record = d.filtered_records[0]
        assert_equal("user_large_1" * 10, record["name"])
      end

    end

    sub_test_case "edge_cases" do
      teardown do
        ["empty.csv", "single_row.json", "unicode_test.csv", "special_chars.json", "large_keys.json"].each do |file|
          File.unlink(file) if File.exist?(file)
        end
      end

      test "empty dictionary file" do
        File.write("empty.csv", "")
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path empty.csv
            field_names uid, name, email
            key uid
            value email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "hello 1001"})
        end
        
        # Should not crash, should return original record
        assert_equal(1, d.filtered_records.size)
        assert_equal({"uid" => 1001, "message" => "hello 1001"}, d.filtered_records[0])
      end

      test "single row dictionary" do
        File.write("single_row.json", '[{"uid": 9999, "name": "single_user", "email": "single@example.org"}]')
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path single_row.json
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 9999, "message" => "hello single"})
          d.feed("test", 2, {"uid" => 8888, "message" => "hello missing"})
        end
        
        # Only matching record should get additional data
        assert_equal(2, d.filtered_records.size)
        
        matching_record = d.filtered_records.find { |r| r["uid"] == 9999 }
        assert_true(matching_record.has_key?("name"))
        assert_equal("single_user", matching_record["name"])
        
        non_matching_record = d.filtered_records.find { |r| r["uid"] == 8888 }
        assert_false(non_matching_record.has_key?("name"))
      end

      test "unicode and special characters" do
        text = <<~'EOF'
          uid,name,email
          1001,山田太郎,yamada@日本.jp
          1002,田中花子,tanaka@example.org
          1003,"Smith, John",john.smith@example.com
        EOF
        File.write("unicode_test.csv", text)
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path unicode_test.csv
            header true
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "test unicode"})
          d.feed("test", 2, {"uid" => 1003, "message" => "test comma"})
        end
        
        assert_equal(2, d.filtered_records.size)
        
        unicode_record = d.filtered_records.find { |r| r["uid"] == 1001 }
        assert_equal("山田太郎", unicode_record["name"])
        assert_equal("yamada@日本.jp", unicode_record["email"])
        
        comma_record = d.filtered_records.find { |r| r["uid"] == 1003 }
        assert_equal("Smith, John", comma_record["name"])
      end

      test "very long field values" do
        long_name = "VeryLongUserName" * 50  # 800 characters
        long_email = "very.long.email.address" * 20 + "@example.org"  # ~500 characters
        
        json_data = [{"uid" => 5001, "name" => long_name, "email" => long_email}]
        File.write("large_keys.json", JSON.generate(json_data))
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path large_keys.json
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 5001, "message" => "test long fields"})
        end
        
        assert_equal(1, d.filtered_records.size)
        record = d.filtered_records[0]
        assert_equal(long_name, record["name"])
        assert_equal(long_email, record["email"])
      end

      test "null and empty string handling" do
        json_data = [
          {"uid" => 6001, "name" => nil, "email" => "null@example.org"},
          {"uid" => 6002, "name" => "", "email" => "empty@example.org"},
          {"uid" => 6003, "name" => "valid", "email" => ""}
        ]
        File.write("special_chars.json", JSON.generate(json_data))
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path special_chars.json
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 6001, "message" => "test null"})
          d.feed("test", 2, {"uid" => 6002, "message" => "test empty"})
          d.feed("test", 3, {"uid" => 6003, "message" => "test partial"})
        end
        
        assert_equal(3, d.filtered_records.size)
        
        # Record with null name should only get email
        null_record = d.filtered_records.find { |r| r["uid"] == 6001 }
        assert_false(null_record.has_key?("name"))
        assert_equal("null@example.org", null_record["email"])
        
        # Record with empty name should get both (empty string is valid)
        empty_record = d.filtered_records.find { |r| r["uid"] == 6002 }
        assert_equal("", empty_record["name"])
        assert_equal("empty@example.org", empty_record["email"])
        
        # Record with empty email should get both (empty string is valid)
        partial_record = d.filtered_records.find { |r| r["uid"] == 6003 }
        assert_equal("valid", partial_record["name"])
        assert_equal("", partial_record["email"])
      end

      test "numeric key handling" do
        # Test both string and numeric keys
        json_data = [
          {"uid" => "str_key", "name" => "string_key_user", "email" => "str@example.org"},
          {"uid" => 123, "name" => "numeric_key_user", "email" => "num@example.org"}
        ]
        File.write("numeric_keys.json", JSON.generate(json_data))
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path numeric_keys.json
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => "str_key", "message" => "test string key"})
          d.feed("test", 2, {"uid" => 123, "message" => "test numeric key"})
        end
        
        assert_equal(2, d.filtered_records.size)
        
        str_record = d.filtered_records.find { |r| r["uid"] == "str_key" }
        assert_equal("string_key_user", str_record["name"])
        
        num_record = d.filtered_records.find { |r| r["uid"] == 123 }
        assert_equal("numeric_key_user", num_record["name"])
        
        File.unlink("numeric_keys.json") if File.exist?("numeric_keys.json")
      end
    end

    sub_test_case "comprehensive_error_scenarios" do
      teardown do
        ["malformed.csv", "invalid_delimiter.csv", "mixed_format.json", "permission_test.csv"].each do |file|
          File.unlink(file) if File.exist?(file)
        end
      end

      test "malformed CSV with inconsistent columns" do
        # CSV with varying number of columns
        text = <<~'EOF'
          uid,name,email
          1001,user01,user01@example.org
          1002,user02
          1003,user03,user03@example.org,extra_column
        EOF
        File.write("malformed.csv", text)
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path malformed.csv
            header true
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "test"})
          d.feed("test", 2, {"uid" => 1002, "message" => "test"})
          d.feed("test", 3, {"uid" => 1003, "message" => "test"})
        end
        
        # Should handle gracefully, processing valid rows
        assert_equal(3, d.filtered_records.size)
        
        valid_record = d.filtered_records.find { |r| r["uid"] == 1001 }
        assert_equal("user01", valid_record["name"])
        
        incomplete_record = d.filtered_records.find { |r| r["uid"] == 1002 }
        assert_equal("user02", incomplete_record["name"])
        assert_false(incomplete_record.has_key?("email"))
      end

      test "CSV with wrong delimiter specified" do
        # TSV content but CSV delimiter specified
        text = "uid\tname\temail\n1001\tuser01\tuser01@example.org\n"
        File.write("invalid_delimiter.csv", text)
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path invalid_delimiter.csv
            header true
            delimiter ","
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => "uid\tname\temail", "message" => "test"})
        end
        
        # Should not crash but may not find expected keys
        assert_equal(1, d.filtered_records.size)
      end

      test "JSON with mixed data types" do
        # JSON with inconsistent data types
        json_data = [
          {"uid" => 1001, "name" => "user01", "email" => "user01@example.org"},
          {"uid" => "1002", "name" => 123, "email" => true},
          {"uid" => 1003, "name" => ["array", "name"], "email" => {"nested" => "object"}}
        ]
        File.write("mixed_format.json", JSON.generate(json_data))
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path mixed_format.json
            key uid
            value name, email
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 1001, "message" => "test"})
          d.feed("test", 2, {"uid" => "1002", "message" => "test"})
          d.feed("test", 3, {"uid" => 1003, "message" => "test"})
        end
        
        # Should handle mixed types gracefully
        assert_equal(3, d.filtered_records.size)
        
        normal_record = d.filtered_records.find { |r| r["uid"] == 1001 }
        assert_equal("user01", normal_record["name"])
        
        mixed_record = d.filtered_records.find { |r| r["uid"] == "1002" }
        assert_equal(123, mixed_record["name"])
        assert_equal(true, mixed_record["email"])
      end

      test "configuration conflicts" do
        File.write("test_config.csv", "uid,name\n1001,user01\n")
        
        # Test header=true with TSV format
        assert_raise(Fluent::ConfigError) do
          create_driver(%[
            strict_path_validation false
            <map>
              path test_config.csv
              format tsv
              header true
              key uid
              value name
            </map>
          ])
        end
        
        # Test delimiter with JSON format
        assert_raise(Fluent::ConfigError) do
          create_driver(%[
            strict_path_validation false
            <map>
              path test_config.csv
              format json
              delimiter ","
              key uid
              value name
            </map>
          ])
        end
        
        File.unlink("test_config.csv")
      end

      test "extremely large progress threshold" do
        File.write("small_for_progress.json", '[{"uid": 1, "name": "test"}]')
        
        d = create_driver(%[
          progress_threshold 1000000
          strict_path_validation false
          <map>
            path small_for_progress.json
            key uid
            value name
          </map>
        ])
        
        d.run do
          d.feed("test", 1, {"uid" => 1, "message" => "test"})
        end
        
        # Should work without progress display
        assert_equal(1, d.filtered_records.size)
        
        File.unlink("small_for_progress.json")
      end
    end

    sub_test_case "integration_tests" do
      teardown do
        ["users.csv", "departments.json", "locations.tsv"].each do |file|
          File.unlink(file) if File.exist?(file)
        end
      end

      test "real-world CSV processing" do
        # Simulate a realistic user database CSV
        csv_content = <<~'EOF'
          employee_id,full_name,email,department_id,hire_date,status
          E001,"Smith, John",john.smith@company.com,D001,2023-01-15,active
          E002,"Johnson, Mary",mary.johnson@company.com,D002,2023-02-20,active
          E003,"Williams, Bob",bob.williams@company.com,D001,2023-03-10,inactive
          E004,"Brown, Alice",alice.brown@company.com,D003,2023-04-05,active
        EOF
        File.write("users.csv", csv_content)
        
        d = create_driver(%[
          key employee_id
          names_map full_name:name,email:contact_email,department_id:dept
          strict_path_validation false
          <map>
            path users.csv
            header true
            key employee_id
            value full_name, email, department_id, status
          </map>
        ])
        
        d.run do
          d.feed("access_log", Time.now.to_i, {"employee_id" => "E001", "action" => "login", "timestamp" => "2023-05-01T09:00:00Z"})
          d.feed("access_log", Time.now.to_i, {"employee_id" => "E003", "action" => "logout", "timestamp" => "2023-05-01T17:30:00Z"})
          d.feed("access_log", Time.now.to_i, {"employee_id" => "E999", "action" => "login", "timestamp" => "2023-05-01T10:15:00Z"})
        end
        
        assert_equal(3, d.filtered_records.size)
        
        # Active user record
        active_record = d.filtered_records.find { |r| r["employee_id"] == "E001" }
        assert_equal("Smith, John", active_record["name"])
        assert_equal("john.smith@company.com", active_record["contact_email"])
        assert_equal("D001", active_record["dept"])
        assert_equal("active", active_record["status"])
        
        # Inactive user record
        inactive_record = d.filtered_records.find { |r| r["employee_id"] == "E003" }
        assert_equal("inactive", inactive_record["status"])
        
        # Non-existent user record (should not have additional fields)
        missing_record = d.filtered_records.find { |r| r["employee_id"] == "E999" }
        assert_false(missing_record.has_key?("name"))
        assert_equal("login", missing_record["action"])
      end

      test "multiple value fields with field mapping" do
        json_content = [
          {"dept_id" => "D001", "dept_name" => "Engineering", "location" => "Tokyo", "manager" => "Tanaka", "budget" => 1000000},
          {"dept_id" => "D002", "dept_name" => "Sales", "location" => "Osaka", "manager" => "Suzuki", "budget" => 800000},
          {"dept_id" => "D003", "dept_name" => "HR", "location" => "Tokyo", "manager" => "Yamada", "budget" => 500000}
        ]
        File.write("departments.json", JSON.generate(json_content))
        
        d = create_driver(%[
          key department_id
          names_map dept_name:department,location:office,manager:dept_manager
          strict_path_validation false
          <map>
            path departments.json
            key dept_id
            value dept_name, location, manager, budget
          </map>
        ])
        
        d.run do
          d.feed("expense_report", Time.now.to_i, {"department_id" => "D001", "expense" => 50000, "category" => "equipment"})
          d.feed("expense_report", Time.now.to_i, {"department_id" => "D002", "expense" => 30000, "category" => "travel"})
        end
        
        assert_equal(2, d.filtered_records.size)
        
        eng_record = d.filtered_records.find { |r| r["department_id"] == "D001" }
        assert_equal("Engineering", eng_record["department"])
        assert_equal("Tokyo", eng_record["office"])
        assert_equal("Tanaka", eng_record["dept_manager"])
        assert_equal(1000000, eng_record["budget"])
        assert_equal(50000, eng_record["expense"])
        
        sales_record = d.filtered_records.find { |r| r["department_id"] == "D002" }
        assert_equal("Sales", sales_record["department"])
        assert_equal("Osaka", sales_record["office"])
      end

      test "TSV with custom delimiter processing" do
        tsv_content = "location_id|city|country|timezone|population\n"
        tsv_content += "L001|Tokyo|Japan|JST|13960000\n"
        tsv_content += "L002|Osaka|Japan|JST|19110000\n"
        tsv_content += "L003|New York|USA|EST|8400000\n"
        File.write("locations.tsv", tsv_content)
        
        d = create_driver(%[
          strict_path_validation false
          <map>
            path locations.tsv
            format csv
            delimiter "|"
            header true
            key location_id
            value city, country, timezone
          </map>
        ])
        
        d.run do
          d.feed("user_activity", Time.now.to_i, {"location_id" => "L001", "user_id" => "U001", "activity" => "login"})
          d.feed("user_activity", Time.now.to_i, {"location_id" => "L003", "user_id" => "U002", "activity" => "purchase"})
        end
        
        assert_equal(2, d.filtered_records.size)
        
        tokyo_record = d.filtered_records.find { |r| r["location_id"] == "L001" }
        assert_equal("Tokyo", tokyo_record["city"])
        assert_equal("Japan", tokyo_record["country"])
        assert_equal("JST", tokyo_record["timezone"])
        
        ny_record = d.filtered_records.find { |r| r["location_id"] == "L003" }
        assert_equal("New York", ny_record["city"])
        assert_equal("USA", ny_record["country"])
      end
    end
  end

  private

  def create_driver(conf)
    Fluent::Test::Driver::Filter.new(Fluent::Plugin::RelatedInfoFilter).configure(conf)
  end
end
