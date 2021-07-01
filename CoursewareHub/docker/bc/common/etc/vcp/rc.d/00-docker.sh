#!/bin/bash

set -eu

mkdir -p /etc/docker

cat > /etc/docker/daemon.json <<EOF
{
  "insecure-registries" : ["${VCCCTR_IPADDR}:5000", "${VCCCTR_IPADDR}:5001"]
}
EOF
