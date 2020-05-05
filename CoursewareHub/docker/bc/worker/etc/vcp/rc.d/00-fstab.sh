#!/bin/sh
set -e

: ${NFS_SERVER:?"NFS_SERVER must be set!"}

cat >> /etc/fstab <<EOF
${NFS_SERVER}:/home /home nfs rw,_netdev,auto 0 0
${NFS_SERVER}:/exchange /exchange nfs rw,_netdev,auto 0 0
${NFS_SERVER}:/jupyter /jupyter nfs rw,_netdev,auto 0 0
EOF
