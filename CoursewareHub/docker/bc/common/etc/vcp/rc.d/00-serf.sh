#!/bin/bash

set -eu

cat > /etc/sysconfig/serf <<EOF
SERF_NODE_ID=${SERF_NODE_ID}
VCCC_ID=${VCCC_ID}
VCCCTR_IPADDR=${VCCCTR_IPADDR}
PRIVATE_IP=${PRIVATE_IP}
EOF
