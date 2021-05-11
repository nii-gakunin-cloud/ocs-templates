#!/bin/bash
set -e

if [ -z "${MY_HOST_IF}" ]; then

cat > /etc/sysconfig/serf <<EOF
SERF_NODE_ID=${SERF_NODE_ID}
VCCC_ID=${VCCC_ID}
VCCCTR_IPADDR=${VCCCTR_IPADDR}
PRIVATE_IP=${PRIVATE_IP}
EOF

else

cat > /etc/sysconfig/serf <<EOF
SERF_NODE_ID=${SERF_NODE_ID}
MY_HOST_IF=${MY_HOST_IF}
VCCC_ID=${VCCC_ID}
VCCCTR_IPADDR=${VCCCTR_IPADDR}
EOF
sed -i -r -e '/^ExecStart=/s%-bind=[^ \t]+%-iface=${MY_HOST_IF}%' /etc/systemd/system/serf.service

fi

