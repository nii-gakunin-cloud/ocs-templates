group "default" {
  targets = ["nfsd", "node"]
}

target "common" {
  context = "common"
}

target "nfsd" {
  context = "nfsd"
  contexts = {
    cwh-common = "target:common"
  }
  tags = tag("base-nfsd")
}

target "node" {
  context = "node"
  contexts = {
    cwh-common = "target:common"
  }
  tags = tag("base")
}

function "tag" {
  params = [name]
  result = [
    "${REGISTRY}/vcp/coursewarehub:${name}",
    "${REGISTRY}/vcp/coursewarehub:${name}-${formatdate("YYYYMMDD", timestamp())}",
  ]
}

variable "REGISTRY" {
  default = "harbor.vcloud.nii.ac.jp"
}
