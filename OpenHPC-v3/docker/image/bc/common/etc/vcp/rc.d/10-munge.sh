#!/bin/bash

: ${MUNGE_KEY_PATH:=/etc/munge/munge.key}

setup_munge_key() {
  if [[ -n "$MUNGE_KEY" ]]; then
    touch $MUNGE_KEY_PATH
    chown munge:munge $MUNGE_KEY_PATH
    chmod 0400 $MUNGE_KEY_PATH
    truncate -s 0 $MUNGE_KEY_PATH
    echo $MUNGE_KEY | base64 -d >> $MUNGE_KEY_PATH
  fi
}

setup_munge_service() {
  local service_path=/usr/lib/systemd/system/munge.service
  if [[ -f $service_path ]]; then
    sed -i -e '/ExecStart=/s/--syslog//' $service_path
    sed -ri -e "/^PIDFile=/s#PIDFile=/var/run/#PIDFile=/run/#" $service_path
  fi
}

setup() {
  setup_munge_key
  setup_munge_service
}

setup
