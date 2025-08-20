require "helper"
require "fluent/plugin/parser_lc_wrapper.rb"

class LcWrapperParserPerformanceTest < Test::Unit::TestCase
  setup do
    omit "Performance tests disabled. Set PERFORMANCE_TESTS=1 to enable" unless ENV['PERFORMANCE_TESTS'] == '1'
    Fluent::Test.setup
  end

  # Constants from main test file
  SERVER_SIGNATURE = '9d315e0a-11b7-11ef-a0d3-02420a64000e'
  NOTEBOOK_MEME = 'b9f187ae-2c65-11ef-8eda-02420a64000d'
  NOTEBOOK_PATH = 'Untitled.ipynb'
  CELL_MEME = 'cb98905e-35b8-11ef-bcb4-02420a64001e'
  UID = 1001
  GID = 100

  # Performance test constants
  PERFORMANCE_TIMEOUT = 10.0  # Maximum allowed execution time in seconds
  LARGE_DATA_SIZE = 1000      # Number of fake patterns to generate

  sub_test_case "INPUT_PATTERN performance tests" do
    test "massive fake path patterns" do
      d = create_driver()
      
      # Generate 1000 fake path patterns that could cause backtracking issues
      # These are embedded within the command content, not as separate LC Wrapper sections
      fake_patterns = (1..LARGE_DATA_SIZE).map do |i|
        "echo \"Processing fake#{i}.log\"\ncat <<EOF#{i}\n----\npath: /tmp/fake#{i}.log\nnotebook_path: fake#{i}.ipynb\nEOF#{i}"
      end.join("\n")
      
      # Create test text with massive fake patterns followed by real pattern
      massive_input_text = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
echo "Processing large dataset"
#{fake_patterns}
echo "Real command after fake patterns"
----
path: /home/test/.log/real_performance.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
Large dataset processed successfully
----
end time: 2024-06-29 10:00:05(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS

      # Measure execution time
      start_time = Time.now
      
      d.instance.parse(massive_input_text) do |time, record|
        execution_time = Time.now - start_time
        
        # Performance assertion
        assert execution_time < PERFORMANCE_TIMEOUT, 
               "INPUT_PATTERN performance degradation detected: #{execution_time}s (max: #{PERFORMANCE_TIMEOUT}s)"
        
        # Correctness assertions
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal '/home/test/.log/real_performance.log', record['path']
        assert_equal NOTEBOOK_PATH, record['notebook_path']
        assert_equal 'ok', record['execute_reply_status']
        
        # Verify the input contains all fake patterns (greedy matching worked correctly)
        expected_input_start = "echo \"Processing large dataset\"\necho \"Processing fake1.log\""
        assert record['input'].include?(expected_input_start), 
               "INPUT_PATTERN should include all fake patterns"
        
        expected_input_end = "echo \"Real command after fake patterns\"\n"
        assert record['input'].end_with?(expected_input_end), 
               "INPUT_PATTERN should end at the correct position"
      end
      
      puts "INPUT_PATTERN massive fake patterns test completed in #{Time.now - start_time}s"
    end

    test "gigantic input data" do
      d = create_driver()
      
      # Generate several MB of input data
      large_script = "# Large script with #{LARGE_DATA_SIZE * 10} lines\n" + 
                     (1..(LARGE_DATA_SIZE * 10)).map do |i|
                       "echo \"Line #{i}: This is a long line with various content to simulate real-world large scripts or data processing commands. Line #{i} contains enough text to make this a substantial performance test.\""
                     end.join("\n")
      
      gigantic_input_text = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
#{large_script}
----
path: /home/test/.log/gigantic_performance.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
Gigantic script executed successfully
----
end time: 2024-06-29 10:00:10(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS

      start_time = Time.now
      
      d.instance.parse(gigantic_input_text) do |time, record|
        execution_time = Time.now - start_time
        
        assert execution_time < PERFORMANCE_TIMEOUT, 
               "Gigantic input performance degradation detected: #{execution_time}s"
        
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal '/home/test/.log/gigantic_performance.log', record['path']
        assert record['input'].include?("Line 1:"), "Should contain beginning of large script"
        assert record['input'].include?("Line #{LARGE_DATA_SIZE * 10}:"), "Should contain end of large script"
      end
      
      puts "INPUT_PATTERN gigantic data test completed in #{Time.now - start_time}s"
    end
  end

  sub_test_case "OUTPUT_PATTERN performance tests" do
    test "massive fake end patterns" do
      d = create_driver()
      
      # Generate 1000 fake end patterns that could cause backtracking issues
      fake_end_patterns = (1..LARGE_DATA_SIZE).map do |i|
        "----\nend time: 2024-06-29 #{format('%02d', (i % 24).to_i)}:#{format('%02d', (i % 60).to_i)}:#{format('%02d', ((i * 17) % 60).to_i)}(UTC)\n#{i} chunks with matched keywords or errors\n----\nFake end pattern #{i} content"
      end.join("\n")
      
      massive_output_text = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
echo "Processing massive output"
----
path: /home/test/.log/massive_output_performance.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
Output processing started
#{fake_end_patterns}
Real output content ends here
----
end time: 2024-06-29 10:00:15(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS

      start_time = Time.now
      
      d.instance.parse(massive_output_text) do |time, record|
        execution_time = Time.now - start_time
        
        assert execution_time < PERFORMANCE_TIMEOUT, 
               "OUTPUT_PATTERN performance degradation detected: #{execution_time}s"
        
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal "echo \"Processing massive output\"\n", record['input']
        assert_equal '/home/test/.log/massive_output_performance.log', record['path']
        assert_equal 'ok', record['execute_reply_status']
        
        # Verify the real end_time was parsed (not any fake one)
        assert_equal Fluent::EventTime.from_time(Time.utc(2024,6,29,10,0,15)), record['end_time']
        
        # Verify output contains all fake patterns (greedy matching worked correctly)
        assert record['output'].include?("Fake end pattern 1 content"), 
               "OUTPUT_PATTERN should include all fake end patterns"
        assert record['output'].include?("Fake end pattern #{LARGE_DATA_SIZE} content"), 
               "OUTPUT_PATTERN should include all fake end patterns"
        assert record['output'].end_with?("Real output content ends here\n"), 
               "OUTPUT_PATTERN should end at the correct position"
      end
      
      puts "OUTPUT_PATTERN massive fake end patterns test completed in #{Time.now - start_time}s"
    end

    test "gigantic output data" do
      d = create_driver()
      
      # Generate several MB of output data
      large_output = (1..(LARGE_DATA_SIZE * 10)).map do |i|
        "Output line #{i}: This is a substantial output line that simulates large log files, data processing results, or command outputs that could stress the OUTPUT_PATTERN regex. Line #{i} adds to the overall size."
      end.join("\n")
      
      gigantic_output_text = <<EOS
{"lc_cell_meme": {"current": "#{CELL_MEME}"}}
----
echo "Generating massive output"
----
path: /home/test/.log/gigantic_output_performance.log
notebook_path: #{NOTEBOOK_PATH}
lc_notebook_meme: #{NOTEBOOK_MEME}
server_signature: #{SERVER_SIGNATURE}
uid: #{UID}
gid: #{GID}
start time: 2024-06-29 10:00:00(UTC)
----
#{large_output}
----
end time: 2024-06-29 10:00:20(UTC)
0 chunks with matched keywords or errors
----
execute_reply_status: ok
EOS

      start_time = Time.now
      
      d.instance.parse(gigantic_output_text) do |time, record|
        execution_time = Time.now - start_time
        
        assert execution_time < PERFORMANCE_TIMEOUT, 
               "Gigantic output performance degradation detected: #{execution_time}s"
        
        assert_equal CELL_MEME, record['lc_cell_meme']
        assert_equal "echo \"Generating massive output\"\n", record['input']
        assert_equal '/home/test/.log/gigantic_output_performance.log', record['path']
        assert record['output'].include?("Output line 1:"), "Should contain beginning of large output"
        assert record['output'].include?("Output line #{LARGE_DATA_SIZE * 10}:"), "Should contain end of large output"
      end
      
      puts "OUTPUT_PATTERN gigantic data test completed in #{Time.now - start_time}s"
    end
  end

  private

  def create_driver(conf = {})
    Fluent::Test::Driver::Parser.new(Fluent::Plugin::LcWrapperParser).configure(conf)
  end
end