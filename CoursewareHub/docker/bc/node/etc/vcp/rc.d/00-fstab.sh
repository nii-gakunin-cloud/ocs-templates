#!/bin/sh
set -e

: ${NFS_SERVER:?"NFS_SERVER must be set!"}

cat >> /etc/fstab <<EOF
${NFS_SERVER}:/ /mnt/nfs nfs rw,_netdev,auto 0 0
/mnt/nfs/jupyter /jupyter none bind 0 0
/mnt/nfs/exchange /exchange none bind 0 0
/mnt/nfs/share /share none bind 0 0
EOF
