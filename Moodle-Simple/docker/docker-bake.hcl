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
        version = "5.1.1"
        php = "8.4"
      },
      {
        version = "5.0.4"
        php = "8.4"
        target = "v4"
      },
      {
        version = "4.5.8"
        php = "8.3"
        target = "v4"
      },
      {
        version = "4.4.12"
        php = "8.3"
        target = "v4"
      },
      {
        version = "4.1.22"
        php = "8.1"
        target = "v4"
      },
    ]
  }
  context = "./moodle"
  target = try(item.target, null)
  args = {
    MOODLE_VERSION = item.version
    PHP_VERSION = item.php
  }
  tags = moodle_tag(item.version)
}

target "ssl" {
  name = "ssl-${item.variant}"
  matrix = {
    item = [
      {
        variant = "v4"
        target = "v4"
      },
      {
        variant = "v5"
      },
    ]
  }
  context = "./ssl"
  target = try(item.target, null)
  tags = date_tag("ssl-${item.variant}")
}

target "shibboleth" {
  name = "shibboleth-${item.variant}"
  matrix = {
    item = [
      {
        variant = "v4"
        target = "v4"
      },
      {
        variant = "v5"
      },
    ]
  }
  context = "./shibboleth"
  target = try(item.target, null)
  tags = date_tag("shibboleth-${item.variant}")
}

target "base" {
  context = "./base"
  tags = date_tag("base")
}
