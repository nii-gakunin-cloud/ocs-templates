#!/bin/bash

setup_fstab() {
  if [ -f /var/lib/vcp/.10-nfs_client ]; then
    return
  fi
  cat >> /etc/fstab <<EOF
${MASTER_HOSTNAME}:/ohpc/pub /opt/ohpc/pub nfs nfsvers=4,ro,nodev  0 0
${MASTER_HOSTNAME}:/home     /home         nfs nfsvers=4,rw,nodev  0 0
EOF
  mkdir -p /var/lib/vcp
  touch /var/lib/vcp/.10-nfs_client
}

setup_fstab
