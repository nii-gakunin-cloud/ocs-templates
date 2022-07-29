#!/bin/bash

DEBUG_LOG=/var/log/vcp_rc-debug.log

exec_scripts() {
  for rc in /etc/vcp/rc.d/*.sh; do
    [ -x $rc ] && $rc
  done
}

exec_scripts_debug() {
  touch $DEBUG_LOG
  for rc in /etc/vcp/rc.d/*.sh; do
    echo "${rc} :-----" >> $DEBUG_LOG
    [ -x $rc ] && bash -x $rc &>> $DEBUG_LOG
  done
}

if [[ -z "$DEBUG_VCP_RC" ]]; then
  exec_scripts
else
  exec_scripts_debug
fi

if [ "$#" -eq 0 -o "${1#-}" != "$1" ]; then
  set -- /usr/sbin/init "$@"
fi

exec "$@"
