lib = File.expand_path("../lib", __FILE__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)

Gem::Specification.new do |spec|
  spec.name    = "fluent-plugin-lc-wrapper"
  spec.version = "0.2.2"
  spec.authors = ["NII Gakunin Cloud"]
  spec.email   = ["cld-office-support@nii.ac.jp"]

  spec.summary       = %q{fluentd parser plugin for lc-wrapper}
  spec.description   = %q{A robust Fluentd parser plugin for processing LC Wrapper logs from Jupyter notebook executions.}
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
end
