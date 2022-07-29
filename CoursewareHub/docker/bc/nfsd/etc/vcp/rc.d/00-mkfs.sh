#!/bin/bash

: ${NFS_FS:=xfs}
: ${NFS_MKFS_OPTS:=""}
: ${MAX_RETRY:=180}
: ${EXPORT_DIR:=/exported}

if [[ -n "$NFS_MKFS" ]]; then

NFS_DEV=$(lsblk -P -s -d | egrep -e 'MOUNTPOINTS?=""' | sed -r -n -e '/TYPE="disk"/s/NAME="([^"]+)".*/\1/p' | head -1)
retry=0
while [[ -z "$NFS_DEV" ]]; do
  sleep 10
  retry=$((retry + 1))
  NFS_DEV=$(lsblk -P -s -d | egrep -e 'MOUNTPOINTS?=""' | sed -r -n -e '/TYPE="disk"/s/NAME="([^"]+)".*/\1/p' | head -1)
  if [[ $retry -gt $MAX_RETRY ]]; then
    echo "cannot find block device" >&2
    exit 1
  fi
done

NFS_DEV="/dev/${NFS_DEV}"
retry=0
until [[ -b ${NFS_DEV} ]]; do
  echo "wait ${NFS_DEV}"
  sleep 1
  retry=$((retry + 1))
  if [[ $retry -gt $MAX_RETRY ]]; then
    echo "ERROR!"
    exit 1
  fi
done

mkfs.${NFS_FS} ${NFS_MKFS_OPTS} ${NFS_DEV}
mkdir -p ${EXPORT_DIR}
mount -t ${NFS_FS} ${NFS_DEV} ${EXPORT_DIR}

fi
