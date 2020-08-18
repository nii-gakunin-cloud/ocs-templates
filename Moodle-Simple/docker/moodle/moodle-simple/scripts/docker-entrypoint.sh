#!/bin/bash

: ${WAIT_FOR:="db:3306"}

set -- /usr/local/bin/wait-for-it.sh --timeout=${WAIT_FOR_TIMEOUT:-150} ${WAIT_FOR} -- "$@"

exec "$@"
