#!/bin/bash

setup_localtime() {
  if [ -n "$TZ" -a -f /usr/share/zoneinfo/$TZ ]; then
    cd /etc
    ln -sf ../usr/share/zoneinfo/$TZ localtime
  fi
}

setup_localtime
