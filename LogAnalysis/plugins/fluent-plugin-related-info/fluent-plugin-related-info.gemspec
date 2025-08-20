lib = File.expand_path("../lib", __FILE__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)

Gem::Specification.new do |spec|
  spec.name    = "fluent-plugin-related-info"
  spec.version = "0.5.2"
  spec.authors = ["NII Gakunin Cloud"]
  spec.email   = ["cld-office-support@nii.ac.jp"]

  spec.summary       = %q{Fluentd filter plugin to enrich records with data from CSV/TSV/JSON dictionaries}
  spec.description   = %q{A Fluentd filter plugin that enriches log records with additional information from external dictionary files. Supports CSV, TSV, and JSON formats with automatic file watching, field mapping, and security features. Perfect for adding user information, department data, or any contextual data to your logs based on key lookups.}
  spec.license       = "Apache-2.0"

  test_files, files  = `git ls-files -z`.split("\x0").partition do |f|
    f.match(%r{^(test|spec|features)/})
  end
  spec.files         = files
  spec.executables   = files.grep(%r{^bin/}) { |f| File.basename(f) }
  spec.test_files    = test_files
  spec.require_paths = ["lib"]

  spec.add_development_dependency "bundler", "~> 2.6.9"
  spec.add_development_dependency "rake", "~> 13.2.1"
  spec.add_development_dependency "test-unit", "~> 3.6.8"
  spec.add_development_dependency "ci_reporter_test_unit", "~> 1.0"
  spec.add_runtime_dependency "fluentd", [">= 0.14.10", "< 2"]
  spec.add_runtime_dependency "cool.io", [">= 1.4.5", "< 2.0.0"]
end
