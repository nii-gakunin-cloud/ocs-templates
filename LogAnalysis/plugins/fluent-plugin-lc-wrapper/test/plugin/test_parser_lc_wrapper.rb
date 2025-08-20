require "helper"
require "fluent/plugin/parser_lc_wrapper.rb"

class LcWrapperParserTest < Test::Unit::TestCase
  setup do
    Fluent::Test.setup
  end

  SERVER_SIGNATURE = '9d315e0a-11b7-11ef-a0d3-02420a64000e'
  NOTEBOOK_MEME = 'b9f187ae-2c65-11ef-8eda-02420a64000d'
  NOTEBOOK_PATH = 'Untitled.ipynb'
  CELL_MEME = 'cb98905e-35b8-11ef-bcb4-02420a64001e'
  UID = 1001
  GID = 100

  OUTPUT = <<EOS
PING 172.30.2.160 (172.30.2.160) 56(84) bytes of data.
64 bytes from 172.30.2.160: icmp_seq=1 ttl=63 time=0.186 ms
64 bytes from 172.30.2.160: icmp_seq=2 ttl=63 time=0.177 ms
64 bytes from 172.30.2.160: icmp_seq=3ttl=63 time=0.211 ms

--- 172.30.2.160 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2037ms
rtt min/avg/max/mdev = 0.177/0.191/0.211/0.014 ms

EOS

  TEXT_OK = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
!ping -c 3 -v 172.30.2.160
----
path: /home/adminx96614e/.log/20240629/20240629-022507-0651.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 02:25:07(UTC)
----
#{OUTPUT}
----
end time: 2024-06-29 02:25:09(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS

  TEXT_ERR = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
raise "error"
----
path: /home/adminx96614e/.log/20240629/20240629-024734-0189.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 02:47:34(UTC)
----

----
end time: 2024-06-29 02:47:34(UTC)
0 chunks with matched keywords or errors
----
result: /home/adminx96614e/.log/20240629/20240629-024734-0189-0.pkl
execute_reply_status: error
EOS

  INPUT2 = <<EOS
print('''
start time: 2024-06-29 14:38:06(UTC)
----

----
abc
xyz
----


----
end time: 2024-06-29 14:38:06(UTC)
''')
EOS
  OUTPUT2 = <<EOS
start time: 2024-06-29 14:38:06(UTC)
----

----
abc
xyz
----


----
end time: 2024-06-29 14:38:06(UTC)


EOS
  TEXT2 = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
#{INPUT2}
----
path: /home/adminx96614e/.log/20240629/20240629-151005-0395.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 15:10:05(UTC)
----
#{OUTPUT2}
----
end time: 2024-06-29 15:10:05(UTC)
1 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS

  sub_test_case "normal case" do
    test "text" do
      d = create_driver()
      d.instance.parse(TEXT_OK) do |time, record|
        assert_equal UID, record['uid']
        assert_equal GID, record['gid']
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal "!ping -c 3 -v 172.30.2.160\n", record['input']
        assert_equal "#{OUTPUT}\n", record['output']
        assert_equal '/home/adminx96614e/.log/20240629/20240629-022507-0651.log', record['path']
        assert_equal NOTEBOOK_PATH, record['notebook_path']
        assert_equal NOTEBOOK_MEME, record['lc_notebook_meme']
        assert_equal SERVER_SIGNATURE, record['server_signature']
        assert_equal 'ok', record['execute_reply_status']
        assert_equal Fluent::EventTime.from_time(Time.utc(2024,6,29,2,25,7)), record['start_time']
        assert_equal Fluent::EventTime.from_time(Time.utc(2024,6,29,2,25,9)), record['end_time']
      end
    end

    test "text2" do
      d = create_driver()
      d.instance.parse(TEXT2) do |time, record|
        assert_equal UID, record['uid']
        assert_equal GID, record['gid']
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal "#{INPUT2}\n", record['input']
        assert_equal "#{OUTPUT2}\n", record['output']
        assert_equal NOTEBOOK_PATH, record['notebook_path']
        assert_equal NOTEBOOK_MEME, record['lc_notebook_meme']
        assert_equal SERVER_SIGNATURE, record['server_signature']
        assert_equal 'ok', record['execute_reply_status']
        assert_equal Fluent::EventTime.from_time(Time.utc(2024,6,29,15,10,5)), record['start_time']
        assert_equal Fluent::EventTime.from_time(Time.utc(2024,6,29,15,10,5)), record['end_time']
      end
    end

    test "error log" do
      d = create_driver()
      d.instance.parse(TEXT_ERR) do |time, record|
        assert_equal UID, record['uid']
        assert_equal GID, record['gid']
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal "raise \"error\"\n", record['input']
        assert_equal "\n", record['output']
        assert_equal '/home/adminx96614e/.log/20240629/20240629-024734-0189.log', record['path']
        assert_equal NOTEBOOK_PATH, record['notebook_path']
        assert_equal NOTEBOOK_MEME, record['lc_notebook_meme']
        assert_equal SERVER_SIGNATURE, record['server_signature']
        assert_equal 'error', record['execute_reply_status']
        assert_equal '/home/adminx96614e/.log/20240629/20240629-024734-0189-0.pkl', record['result']
        assert_equal Fluent::EventTime.from_time(Time.utc(2024,6,29,2,47,34)), record['start_time']
        assert_equal Fluent::EventTime.from_time(Time.utc(2024,6,29,2,47,34)), record['end_time']
      end
    end
  end

  sub_test_case "error case" do
    test "empty log" do
      d = create_driver()
      assert_raises Fluent::Plugin::Parser::ParserError do
        d.instance.parse('')
      end
    end

    test "invalid JSON header" do
      d = create_driver()
      invalid_json_text = <<EOS
{"invalid_json": broken
----
!ping -c 1 172.30.2.160
----
path: /home/test/.log/test.log
uid: 1001
gid: 100
start time: 2024-06-29 02:25:07(UTC)
----
PING output
----
end time: 2024-06-29 02:25:09(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS
      d.instance.parse(invalid_json_text) do |time, record|
        assert_nil record['lc_cell_meme']
        # When JSON header is invalid, the entire text including the broken JSON is treated as input
        assert_equal "{\"invalid_json\": broken\n----\n!ping -c 1 172.30.2.160\n", record['input']
      end
    end

    test "malformed JSON structure" do
      d = create_driver()
      malformed_json_text = <<EOS
{"lc_cell_meme": "not_a_hash"}
----
!ping -c 1 172.30.2.160
----
path: /home/test/.log/test.log
uid: 1001
gid: 100
start time: 2024-06-29 02:25:07(UTC)
----
PING output
----
end time: 2024-06-29 02:25:09(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS
      d.instance.parse(malformed_json_text) do |time, record|
        assert_nil record['lc_cell_meme']
        # When JSON structure is malformed, the entire text including the JSON is treated as input
        assert_equal "{\"lc_cell_meme\": \"not_a_hash\"}\n----\n!ping -c 1 172.30.2.160\n", record['input']
      end
    end

    test "output containing SEPARATOR" do
      d = create_driver()
      text_with_separator_in_output = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
echo "test output"
----
path: /home/test/.log/test.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
Command output:
----
Separator in output
----
More output after separator
----
end time: 2024-06-29 10:00:01(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS
      d.instance.parse(text_with_separator_in_output) do |time, record|
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal "echo \"test output\"\n", record['input']
        # The output should include all content between the separators, including internal separators
        expected_output = "Command output:\n----\nSeparator in output\n----\nMore output after separator\n"
        assert_equal expected_output, record['output']
        assert_equal 'ok', record['execute_reply_status']
      end
    end

    test "output containing end time pattern" do
      d = create_driver()
      text_with_end_time_in_output = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
echo "log analysis"
----
path: /home/test/.log/test.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
Log entry: end time: 2024-06-29 09:59:59(UTC) found in previous execution
Actual command output here
end time: 2024-06-29 09:58:58(UTC) in another log
Final output line
----
end time: 2024-06-29 10:00:01(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS
      d.instance.parse(text_with_end_time_in_output) do |time, record|
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal "echo \"log analysis\"\n", record['input']
        # The output should include all content, including fake "end time" patterns
        expected_output = "Log entry: end time: 2024-06-29 09:59:59(UTC) found in previous execution\nActual command output here\nend time: 2024-06-29 09:58:58(UTC) in another log\nFinal output line\n"
        assert_equal expected_output, record['output']
        assert_equal 'ok', record['execute_reply_status']
        # The real end_time should be parsed correctly
        assert_equal Fluent::EventTime.from_time(Time.utc(2024,6,29,10,0,1)), record['end_time']
      end
    end

    test "input containing SEPARATOR" do
      d = create_driver()
      text_with_separator_in_input = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
echo "First line
----
Second line with separator
----
Third line"
----
path: /home/test/.log/test.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
First line
----
Second line with separator
----
Third line
----
end time: 2024-06-29 10:00:01(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS
      d.instance.parse(text_with_separator_in_input) do |time, record|
        assert_equal CELL_MEME, record['lc_cell_meme']
        # The input should include the complete command with internal separators
        expected_input = "echo \"First line\n----\nSecond line with separator\n----\nThird line\"\n"
        assert_equal expected_input, record['input']
        # The output should also include separators
        expected_output = "First line\n----\nSecond line with separator\n----\nThird line\n"
        assert_equal expected_output, record['output']
        assert_equal 'ok', record['execute_reply_status']
      end
    end

    test "output containing complete end pattern (dangerous case)" do
      d = create_driver()
      # This case contains the exact pattern that should only appear at the real end
      dangerous_text = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
echo "simulating log analysis"
----
path: /home/test/.log/test.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
Analyzing previous execution log:
----
end time: 2024-06-29 09:59:58(UTC)
0 chunks with matched keywords or errors
----
Log analysis complete. Processing next command...
Actual command output here
----
end time: 2024-06-29 10:00:01(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS
      d.instance.parse(dangerous_text) do |time, record|
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal "echo \"simulating log analysis\"\n", record['input']
        # The output should include ALL content until the REAL end pattern
        expected_output = "Analyzing previous execution log:\n----\nend time: 2024-06-29 09:59:58(UTC)\n0 chunks with matched keywords or errors\n----\nLog analysis complete. Processing next command...\nActual command output here\n"
        assert_equal expected_output, record['output']
        assert_equal 'ok', record['execute_reply_status']
        # The REAL end_time should be parsed correctly (not the fake one in output)
        assert_equal Fluent::EventTime.from_time(Time.utc(2024,6,29,10,0,1)), record['end_time']
      end
    end

    test "input containing fake path pattern (dangerous case)" do
      d = create_driver()
      # This case contains a fake path pattern that could confuse non-greedy matching
      dangerous_input_text = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
cat <<EOF
----
path: /tmp/fake.log
notebook_path: fake.ipynb
lc_notebook_meme: fake-meme-id
server_signature: fake-signature
uid: 999
gid: 999
start time: 2024-01-01 00:00:00(UTC)
EOF
echo "This is the real command after fake pattern"
----
path: /home/test/.log/real.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
Command executed successfully
----
end time: 2024-06-29 10:00:01(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS
      d.instance.parse(dangerous_input_text) do |time, record|
        assert_equal CELL_MEME, record['lc_cell_meme']
        # The input should include the COMPLETE command including the fake pattern
        expected_input = "cat <<EOF\n----\npath: /tmp/fake.log\nnotebook_path: fake.ipynb\nlc_notebook_meme: fake-meme-id\nserver_signature: fake-signature\nuid: 999\ngid: 999\nstart time: 2024-01-01 00:00:00(UTC)\nEOF\necho \"This is the real command after fake pattern\"\n"
        assert_equal expected_input, record['input']
        # The REAL path should be parsed correctly (not the fake one)
        assert_equal '/home/test/.log/real.log', record['path']
        assert_equal NOTEBOOK_PATH, record['notebook_path']
        assert_equal 'ok', record['execute_reply_status']
      end
    end

    test "input with multiple fake path patterns" do
      d = create_driver()
      # This case contains multiple fake path patterns to test non-greedy robustness
      multiple_fake_text = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
echo "First fake pattern:"
cat <<EOF1
----
path: /tmp/first_fake.log
EOF1
echo "Second fake pattern:"
cat <<EOF2
----
path: /tmp/second_fake.log
notebook_path: second_fake.ipynb
EOF2
echo "Real command execution"
----
path: /home/test/.log/real_multiple.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
All commands executed
----
end time: 2024-06-29 10:00:01(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS
      d.instance.parse(multiple_fake_text) do |time, record|
        assert_equal CELL_MEME, record['lc_cell_meme']
        # The input should include ALL fake patterns until the real separator
        expected_input = "echo \"First fake pattern:\"\ncat <<EOF1\n----\npath: /tmp/first_fake.log\nEOF1\necho \"Second fake pattern:\"\ncat <<EOF2\n----\npath: /tmp/second_fake.log\nnotebook_path: second_fake.ipynb\nEOF2\necho \"Real command execution\"\n"
        assert_equal expected_input, record['input']
        # The REAL path should be the last one (not any of the fake ones)
        assert_equal '/home/test/.log/real_multiple.log', record['path']
        assert_equal NOTEBOOK_PATH, record['notebook_path']
        assert_equal 'ok', record['execute_reply_status']
      end
    end
  end
  private

  def create_driver(conf = {})
    Fluent::Test::Driver::Parser.new(Fluent::Plugin::LcWrapperParser).configure(conf)
  end
end
