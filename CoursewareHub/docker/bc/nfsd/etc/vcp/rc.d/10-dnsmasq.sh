#!/bin/sh

: ${DONE_FILE:=/var/lib/vcp/.10-dnsmasq}
: ${CFG_FILE:=/etc/dnsmasq.d/addn-hosts.conf}
: ${HOSTS_FILE:=/etc/hosts-dnsmasq}
: ${SERVER_ADDRESS:=127.10.0.53}

set -eu

setup_dnsmasq () {
  touch "${HOSTS_FILE}"
  cat > "${CFG_FILE}" << EOF
listen-address=${SERVER_ADDRESS},${PRIVATE_IP}
bind-interfaces
no-resolv
addn-hosts=${HOSTS_FILE}
server=8.8.8.8
server=8.8.4.4
EOF
}

if [ ! -f "${DONE_FILE}" ]; then
  setup_dnsmasq
  mkdir -p $(dirname "${DONE_FILE}")
  touch "${DONE_FILE}"
fi

