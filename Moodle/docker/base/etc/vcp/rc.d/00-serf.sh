#!/bin/bash
set -eu
cfg=/etc/sysconfig/serf

touch $cfg
sed -r -i -e '/VCCC_ID|VCCCTR_IPADDR|PRIVATE_IP|SERF_NODE_ID/d' $cfg
cat >> $cfg <<EOF
VCCC_ID=${VCCC_ID}
VCCCTR_IPADDR=${VCCCTR_IPADDR}
PRIVATE_IP=${PRIVATE_IP}
SERF_NODE_ID=${SERF_NODE_ID}
EOF
