group "default" {
  targets = ["app", "base"]
}

group "app" {
  targets = ["moodle", "ssl", "shibboleth"]
}

variable "image_name" {
  default = "harbor.vcloud.nii.ac.jp/vcp/moodle-simple"
}

function "moodle_tag" {
  params = [version]
  result = [
    "${image_name}:${version}",
    "${image_name}:${join(".", slice(split(".", version), 0, 2))}"
  ]
}

function "date_tag" {
  params = [tag]
  result = [
    "${image_name}:${tag}",
    "${image_name}:${tag}-${formatdate("YYYYMMDD", timestamp())}"
  ]
}

target "moodle" {
  name = "moodle-${replace(item.version, ".", "-")}"
  matrix = {
    item = [
      {
        version = "5.0.2"
        php = "8.4"
      },
      {
        version = "4.5.6"
        php = "8.3"
      },
      {
        version = "4.4.10"
        php = "8.3"
      },
      {
        version = "4.1.20"
        php = "8.1"
      },
    ]
  }
  context = "./moodle"
  args = {
    MOODLE_VERSION = item.version
    PHP_VERSION = item.php
  }
  tags = moodle_tag(item.version)
}

target "ssl" {
  context = "./ssl"
  tags = date_tag("ssl")
}

target "shibboleth" {
  context = "./shibboleth"
  tags = date_tag("shibboleth")
}

target "base" {
  context = "./base"
  tags = date_tag("base")
}
