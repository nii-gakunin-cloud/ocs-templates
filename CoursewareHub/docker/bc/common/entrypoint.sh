#!/bin/bash

set -e

for rc in /etc/vcp/rc.d/*.sh; do
  if [ -x $rc ]; then
    $rc
  fi
done

if [ $# -eq 0 -o "${1#-}" != "$1" ]; then
  set -- /usr/sbin/init "$@"
fi

exec "$@"
