#!/bin/sh
set -e

: ${NFS_EXPORT_HOSTS:="*"}

cat >> /etc/exports <<EOF
/mnt/nfs          ${NFS_EXPORT_HOSTS}(rw,fsid=0,no_root_squash,no_subtree_check,sync)
/mnt/nfs/home     ${NFS_EXPORT_HOSTS}(rw,nohide,no_root_squash,no_subtree_check,sync)
/mnt/nfs/exchange ${NFS_EXPORT_HOSTS}(rw,nohide,no_root_squash,no_subtree_check,sync)
/mnt/nfs/jupyter  ${NFS_EXPORT_HOSTS}(rw,nohide,no_root_squash,no_subtree_check,sync)
EOF
