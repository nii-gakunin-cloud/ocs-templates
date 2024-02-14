#!/bin/bash
set -eu
cfg=/etc/sysconfig/fluentd

touch $cfg
sed -r -i -e '/VCCC_ID|VCCCTR_IPADDR|PRIVATE_IP/d' $cfg
cat >> $cfg <<EOF
VCCC_ID=${VCCC_ID}
VCCCTR_IPADDR=${VCCCTR_IPADDR}
PRIVATE_IP=${PRIVATE_IP}
EOF
