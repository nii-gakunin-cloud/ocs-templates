#!/bin/sh
set -eu

: ${DONE_FILE:=/var/lib/vcp/.00-fstab}
: ${NFS_SERVER:?"NFS_SERVER must be set!"}

setup_fstab () {
  touch /etc/fstab
  if ! grep -q -e "$NFS_SERVER" /etc/fstab; then
    echo "${NFS_SERVER}:/ /mnt/nfs nfs rw,_netdev,auto 0 0" >> /etc/fstab
  fi

  mount_points=("/jupyter" "/exchange")
  IFS=: mount_points+=(${EXTRA_MOUNT_POINTS:-})

  for mp in "${mount_points[@]}"; do
    src_dir="/mnt/nfs${mp}"
    if ! grep -q -e "$mp" /etc/fstab; then
      echo "$src_dir $mp none bind 0 0" >> /etc/fstab
    fi
  done
}

if [ ! -f "${DONE_FILE}" ]; then
  setup_fstab
  mkdir -p $(dirname "${DONE_FILE}")
  touch "${DONE_FILE}"
fi
