#!/bin/bash

: ${NFS_DEV_FS:=xfs}
: ${NFS_DEV_MKFS_OPTS:=""}
: ${MAX_RETRY:=60}

if [ ! -z "$NFS_DEV" ]; then
retry=0
until [ -b ${NFS_DEV} ]; do
  echo "wait ${NFS_DEV}"
  sleep 1
  retry=$((retry + 1))
  if [ $retry -gt $MAX_RETRY ]; then
    echo "ERROR!"
    exit 1
  fi
done

mkfs.${NFS_DEV_FS} ${NFS_DEV_MKFS_OPTS} ${NFS_DEV}
cat >> /etc/fstab <<EOF
${NFS_DEV} /mnt ${NFS_DEV_FS} defaults 0 0
EOF

mkdir -p /mnt
mount /mnt

mkdir -p /mnt/nfs/home
mkdir -p -m 0777 /mnt/nfs/exchange /mnt/nfs/jupyter

fi
