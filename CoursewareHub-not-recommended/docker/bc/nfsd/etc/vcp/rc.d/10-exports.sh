#!/bin/sh

: ${HUB_NAME:="$UGROUP_NAME"}
: ${NFS_EXPORT_HOSTS:="*"}
: ${EXPORT_DIR:=/exported}

if [ -n "$HUB_NAME" ]; then
mkdir -p /etc/exports.d
cat > /etc/exports.d/${HUB_NAME}.exports <<EOF
${EXPORT_DIR}/${HUB_NAME}          ${NFS_EXPORT_HOSTS}(rw,fsid=0,no_root_squash,no_subtree_check,sync,crossmnt)
EOF
fi
