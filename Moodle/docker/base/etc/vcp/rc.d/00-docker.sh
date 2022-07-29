#!/bin/bash

: ${LOG_DRIVER:=local}
set -eu

mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<EOF
{
  "insecure-registries" : ["${VCCCTR_IPADDR}:5000", "${VCCCTR_IPADDR}:5001"],
  "log-driver": "${LOG_DRIVER}"
}
EOF
