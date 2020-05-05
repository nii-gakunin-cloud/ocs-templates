#!/bin/sh
set -e

cat > /etc/sysconfig/docker <<EOF
VCCCTR_IPADDR=${VCCCTR_IPADDR}
EOF

cat > /etc/sysconfig/serf <<EOF
SERF_NODE_ID=${SERF_NODE_ID}
MY_HOST_IF=${MY_HOST_IF}
VCCC_ID=${VCCC_ID}
VCCCTR_IPADDR=${VCCCTR_IPADDR}
EOF
