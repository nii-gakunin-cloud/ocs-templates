#!/bin/bash

RETRY_MAX=60

wait_device() {
  local dev=$1
  local count=0
  until [[ -b $dev ]]; do
    sleep 1
    if [[ $((count++)) -gt $RETRY_MAX ]]; then
      exit 1
    fi
  done
}

setup() {
  if [[ -n "$NFS_DEV" ]]; then
    wait_device $NFS_DEV
    mkfs.xfs $NFS_DEV
    mkdir -p /exports
    mount $NFS_DEV /exports
    echo "$NFS_DEV /exports xfs defaults 0 0" >> /etc/fstab
  fi
}

setup
