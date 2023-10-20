#!/bin/sh

: ${DONE_FILE:=/var/lib/vcp/.10-exports}
: ${HUB_NAME:="$UGROUP_NAME"}
: ${NFS_EXPORT_HOSTS:="*"}
: ${EXPORT_DIR:=/exported}

set -eu

setup_exports () {
  if [ -n "$HUB_NAME" ]; then
    mkdir -p /etc/exports.d
    echo "${EXPORT_DIR}/${HUB_NAME}  ${NFS_EXPORT_HOSTS}(rw,fsid=0,no_root_squash,no_subtree_check,sync,crossmnt)" > /etc/exports.d/${HUB_NAME}.exports 
  fi
}

if [ ! -f "${DONE_FILE}" ]; then
  setup_exports
  mkdir -p $(dirname "${DONE_FILE}")
  touch "${DONE_FILE}"
fi
