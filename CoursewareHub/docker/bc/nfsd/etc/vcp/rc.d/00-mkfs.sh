#!/bin/bash
: ${DONE_FILE:=/var/lib/vcp/.00-mkfs}
: ${NFS_FS:=xfs}
: ${NFS_MKFS_OPTS:=""}
: ${MAX_RETRY:=180}
: ${EXPORT_DIR:=/exported}

get_nfs_dev() {
  lsblk -J | jq -r '.blockdevices[] | select(.type=="disk" and (.children|not)) | .name' | sort -r | head -1
}

check_device () {
  NFS_DEV=$(get_nfs_dev)
  retry=0
  while [[ -z "$NFS_DEV" ]]; do
    sleep 10
    retry=$((retry + 1))
    NFS_DEV=$(get_nfs_dev)
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
}

mkfs_nfs_dev () {
  if [ ! -f "${DONE_FILE}" ]; then
    mkfs.${NFS_FS} ${NFS_MKFS_OPTS} ${NFS_DEV}
    mkdir -p $(dirname "${DONE_FILE}")
    touch "${DONE_FILE}"
  fi
}

mount_export_dir () {
  mkdir -p ${EXPORT_DIR}
  mount -t ${NFS_FS} ${NFS_DEV} ${EXPORT_DIR}
}

if [[ -n "$NFS_MKFS" ]]; then
  check_device
  mkfs_nfs_dev
  mount_export_dir
fi
