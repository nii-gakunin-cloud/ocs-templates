#!/bin/bash

set -e

if [[ -z "${AUTH_FQDN}" ]]; then
  echo "AUTH_FQDN is not set"
else
  /var/www/simplesamlphp/bin/get_idp_proxy_metadata.sh ${AUTH_FQDN}
fi
