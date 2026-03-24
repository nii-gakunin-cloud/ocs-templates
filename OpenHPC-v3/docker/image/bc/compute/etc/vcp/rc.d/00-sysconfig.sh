#!/bin/bash

# Export environment variables for systemd services
# This script generates /etc/sysconfig files for services that need environment variables

setup_hostname_env() {
  if [ -f /var/lib/vcp/.00-sysconfig ]; then
    return
  fi

  # Export PRIVATE_IP for hostname-setup service
  cat > /etc/sysconfig/hostname-setup <<EOF
PRIVATE_IP=${PRIVATE_IP}
EOF

  mkdir -p /var/lib/vcp
  touch /var/lib/vcp/.00-sysconfig
}

setup_hostname_env
