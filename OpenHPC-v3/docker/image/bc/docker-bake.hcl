group "default" {
  targets = ["master", "compute", "compute-gpu"]
}

target "common" {
  context = "common"
}

target "master" {
  context = "master"
  contexts = {
    ohpc-common = "target:common"
  }
  tags = tag("master")
}

target "compute" {
  context = "compute"
  contexts = {
    ohpc-common = "target:common"
  }
  tags = tag("compute")
}

target "compute-gpu" {
  context = "compute-gpu"
  contexts = {
    ohpc-compute = "target:compute"
  }
  tags = tag("compute-gpu")
}

function "tag" {
  params = [name]
  result = [
    "${REGISTRY}/vcp/openhpc:${name}-${TAG}-dyn",
    "${REGISTRY}/vcp/openhpc:${name}-${TAG}-dyn-${formatdate("YYYYMMDD", timestamp())}",
  ]
}

variable "REGISTRY" {
  default = "harbor.vcloud.nii.ac.jp"
}

variable "TAG" {
  default = "3.4"
}

