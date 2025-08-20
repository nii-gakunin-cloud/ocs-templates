require "helper"

# Suppress known circular require warning from python-pickle gem
original_verbose = $VERBOSE
$VERBOSE = nil
require "fluent/plugin/filter_attach_file.rb"
$VERBOSE = original_verbose

require "mocha/test_unit"

class AttachFileFilterTest < Test::Unit::TestCase
  setup do
    Fluent::Test.setup
  end

  test "returns record unchanged if key is missing" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {}
    File.stubs(:size).never # No file size check for missing key
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal(record, filtered)
  end

  test "returns record unchanged if key is empty" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => ""}
    File.stubs(:size).never # No file size check for empty key
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal(record, filtered)
  end

  test "logs warning and returns record unchanged if file does not exist" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => "nonexistent_file.txt"}
    File.stubs(:exist?).with("/tmp/nonexistent_file.txt").returns(false)
    File.stubs(:size).never # No file size check for non-existent file
    # Mock File.realpath for security validation - this will fail for non-existent file
    File.stubs(:realpath).with("/tmp/nonexistent_file.txt").raises(Errno::ENOENT, "No such file")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    d.instance.log.expects(:warn).with(regexp_matches(/file or directory not found/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_match(/Warning: Path resolution failed: file or directory not found/, filtered["test_key"])
  end

  test "logs warning and returns record unchanged if file cannot be read" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => "unreadable_file.txt"}
    File.stubs(:exist?).with("/tmp/unreadable_file.txt").returns(true)
    File.stubs(:size).with("/tmp/unreadable_file.txt").returns(512) # Mock file size
    File.stubs(:read).with("/tmp/unreadable_file.txt").raises(Errno::EACCES)
    # Mock File.realpath for security validation
    File.stubs(:realpath).with("/tmp/unreadable_file.txt").returns("/tmp/unreadable_file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    d.instance.log.expects(:warn).with(regexp_matches(/Failed to read file/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal(record, filtered)
  end

  test "updates record with file content if file exists and is readable" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => "valid_file.txt"}
    File.stubs(:exist?).with("/tmp/valid_file.txt").returns(true)
    File.stubs(:size).with("/tmp/valid_file.txt").returns(512) # Mock file size
    File.stubs(:read).with("/tmp/valid_file.txt").returns("file content")
    File.stubs(:realpath).with("/tmp/valid_file.txt").returns("/tmp/valid_file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal("file content", filtered["test_key"])
  end

  test "updates record with file content if file exists and is readable and replace_key is true" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => "valid_file.txt"}
    File.stubs(:exist?).with("/tmp/valid_file.txt").returns(true)
    File.stubs(:size).with("/tmp/valid_file.txt").returns(512)
    File.stubs(:read).with("/tmp/valid_file.txt").returns("file content")
    File.stubs(:realpath).with("/tmp/valid_file.txt").returns("/tmp/valid_file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal("file content", filtered["test_key"])
  end

  test "updates record with file content in output_key if replace_key is false and output_key is set" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key false\noutput_key attached_content")
    record = {"test_key" => "valid_file.txt"}
    File.stubs(:exist?).with("/tmp/valid_file.txt").returns(true)
    File.stubs(:size).with("/tmp/valid_file.txt").returns(512)
    File.stubs(:read).with("/tmp/valid_file.txt").returns("file content")
    File.stubs(:realpath).with("/tmp/valid_file.txt").returns("/tmp/valid_file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal("file content", filtered["attached_content"])
    assert_equal("valid_file.txt", filtered["test_key"])
  end

  test "raises config error if replace_key is false and output_key is not set" do
    assert_raise(Fluent::ConfigError) do
      create_driver("key test_key\nbase_dir /tmp\nreplace_key false")
    end
  end

  test "raises config error if key is empty string" do
    assert_raise(Fluent::ConfigError) do
      create_driver("key \"\"\nbase_dir /tmp\nreplace_key true")
    end
  end

  test "raises config error if key is whitespace only" do
    assert_raise(Fluent::ConfigError) do
      create_driver("key \"   \"\nbase_dir /tmp\nreplace_key true")
    end
  end

  test "updates record with transformed content if python_unpickle is true" do
    d = create_driver("key test_key\nbase_dir /tmp\npython_unpickle true\nreplace_key true")
    record = {"test_key" => "valid_file.txt"}
    File.stubs(:exist?).with("/tmp/valid_file.txt").returns(true)
    File.stubs(:size).with("/tmp/valid_file.txt").returns(512) # Mock file size
    File.stubs(:read).with("/tmp/valid_file.txt").returns("file content")
    File.stubs(:realpath).with("/tmp/valid_file.txt").returns("/tmp/valid_file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    d.instance.stubs(:unpickle).with("file content").returns("transformed content")
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal("transformed content", filtered["test_key"])
  end

  test "updates record with JSON encoded unpickled content if as_json is true and python_unpickle is true" do
    d = create_driver("key test_key\nbase_dir /tmp\npython_unpickle true\nas_json true\nreplace_key true")
    record = {"test_key" => "valid_file.txt"}
    File.stubs(:exist?).with("/tmp/valid_file.txt").returns(true)
    File.stubs(:size).with("/tmp/valid_file.txt").returns(512)
    File.stubs(:read).with("/tmp/valid_file.txt").returns("file content")
    File.stubs(:realpath).with("/tmp/valid_file.txt").returns("/tmp/valid_file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    d.instance.stubs(:unpickle).with("file content").returns('{"foo":"bar"}')
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal('{"foo":"bar"}', filtered["test_key"])
  end

  test "updates record with unpickled content (not JSON) if as_json is false and python_unpickle is true" do
    d = create_driver("key test_key\nbase_dir /tmp\npython_unpickle true\nas_json false\nreplace_key true")
    record = {"test_key" => "valid_file.txt"}
    File.stubs(:exist?).with("/tmp/valid_file.txt").returns(true)
    File.stubs(:size).with("/tmp/valid_file.txt").returns(512)
    File.stubs(:read).with("/tmp/valid_file.txt").returns("file content")
    File.stubs(:realpath).with("/tmp/valid_file.txt").returns("/tmp/valid_file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    d.instance.stubs(:unpickle).with("file content").returns(nil)
    d.instance.stubs(:unpickle).with("file content").returns("unpickled content")
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal("unpickled content", filtered["test_key"])
  end

  test "logs error and updates record with warning if unpickle raises exception" do
    d = create_driver("key test_key\nbase_dir /tmp\npython_unpickle true\nreplace_key true")
    record = {"test_key" => "valid_file.txt"}
    File.stubs(:exist?).with("/tmp/valid_file.txt").returns(true)
    File.stubs(:size).with("/tmp/valid_file.txt").returns(512) # Mock file size
    File.stubs(:read).with("/tmp/valid_file.txt").returns("file content")
    File.stubs(:realpath).with("/tmp/valid_file.txt").returns("/tmp/valid_file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    d.instance.stubs(:unpickle).raises(StandardError, "pickle error")
    d.instance.log.expects(:warn).with(regexp_matches(/pickle error/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_match(/Warning: pickle error/, filtered["test_key"])
  end

  test "logs warning and updates record with warning if file size exceeds max_file_size" do
    d = create_driver("key test_key\nbase_dir /tmp\nmax_file_size 1024\nreplace_key true")
    record = {"test_key" => "large_file.txt"}
    File.stubs(:exist?).with("/tmp/large_file.txt").returns(true)
    File.stubs(:size).with("/tmp/large_file.txt").returns(2048)
    # Mock File.realpath for security validation
    File.stubs(:realpath).with("/tmp/large_file.txt").returns("/tmp/large_file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    d.instance.log.expects(:warn).with(regexp_matches(/File size exceeds maximum allowed size/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_match(/File size exceeds maximum allowed size: large_file.txt/, filtered["test_key"])
  end

  test "removes specified number of directory levels from file path" do
    d = create_driver("key test_key\nbase_dir /tmp\ntrim_path_levels 2\nreplace_key true")
    record = {"test_key" => "/level1/level2/level3/file.txt"}
    File.stubs(:exist?).with("/tmp/level3/file.txt").returns(true)
    File.stubs(:size).with("/tmp/level3/file.txt").returns(512) # Mock file size
    File.stubs(:read).with("/tmp/level3/file.txt").returns("file content")
    File.stubs(:realpath).with("/tmp/level3/file.txt").returns("/tmp/level3/file.txt")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal("file content", filtered["test_key"])
  end

  test "logs warning and returns record unchanged if trim_path_levels exceeds directory levels" do
    d = create_driver("key test_key\nbase_dir /tmp\ntrim_path_levels 5\nreplace_key true")
    record = {"test_key" => "level1/level2/file.txt"}
    File.stubs(:exist?).never # No file existence check for excessive trim_path_levels
    d.instance.log.expects(:warn).with(regexp_matches(/File path is empty/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_equal(record, filtered)
  end

  # Security test cases
  test "logs warning for directory traversal attack with .." do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => "../etc/passwd"}
    d.instance.log.expects(:warn).with(regexp_matches(/potentially unsafe path detected/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_match(/Warning: Invalid file path: potentially unsafe path detected/, filtered["test_key"])
  end

  test "logs warning for directory traversal attack with ./" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => "./sensitive/file.txt"}
    d.instance.log.expects(:warn).with(regexp_matches(/potentially unsafe path detected/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_match(/Warning: Invalid file path: potentially unsafe path detected/, filtered["test_key"])
  end

  test "logs warning for null byte injection attack" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => "file.txt\0.jpg"}
    d.instance.log.expects(:warn).with(regexp_matches(/string contains null byte/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_match(/Warning: string contains null byte/, filtered["test_key"])
  end

  test "logs warning for excessively long path" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    long_path = "a" * 5000  # Exceeds 4096 character limit
    record = {"test_key" => long_path}
    d.instance.log.expects(:warn).with(regexp_matches(/potentially unsafe path detected/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_match(/Warning: Invalid file path: potentially unsafe path detected/, filtered["test_key"])
  end

  test "handles symbolic link loop gracefully" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => "valid_file.txt"}
    File.stubs(:exist?).with("/tmp/valid_file.txt").returns(true)
    File.stubs(:realpath).with("/tmp/valid_file.txt").raises(Errno::ELOOP, "symbolic link loop")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    d.instance.log.expects(:warn).with(regexp_matches(/symbolic link loop detected/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_match(/Warning: Path resolution failed: symbolic link loop detected/, filtered["test_key"])
  end

  test "handles file not found during path resolution" do
    d = create_driver("key test_key\nbase_dir /tmp\nreplace_key true")
    record = {"test_key" => "nonexistent_file.txt"}
    File.stubs(:realpath).with("/tmp/nonexistent_file.txt").raises(Errno::ENOENT, "No such file")
    File.stubs(:realpath).with("/tmp").returns("/tmp")
    d.instance.log.expects(:warn).with(regexp_matches(/file or directory not found/))
    filtered = d.instance.filter("test", Time.now, record)
    assert_match(/Warning: Path resolution failed: file or directory not found/, filtered["test_key"])
  end

  private

  def create_driver(conf)
    Fluent::Test::Driver::Filter.new(Fluent::Plugin::AttachFileFilter).configure(conf)
  end
end
