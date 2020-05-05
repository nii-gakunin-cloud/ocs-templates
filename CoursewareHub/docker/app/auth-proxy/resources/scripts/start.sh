#!/bin/bash
set -e

/config.py
/usr/bin/supervisord -n -c /etc/supervisord.conf
