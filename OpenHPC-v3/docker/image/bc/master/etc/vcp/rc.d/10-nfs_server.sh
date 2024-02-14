#!/bin/bash

: ${EXPORTS_DIR:=/exports}
: ${EXPORTS_MACHINE_NAME:=*}
: ${FS_TYPE:=xfs}

OHPC_PUB_DIR=/opt/ohpc/pub

fstype() {
  local target_dir=$1
  df --output=fstype ${target_dir} | tail -1
}

setup_ohpc_pub() {
  if [[ -n $SKIP_OHPC_PUB_COPY ]]; then
    return
  fi
  if [[ $(fstype $OHPC_PUB_DIR) = "overlay" ]]; then
    copy_and_bind $OHPC_PUB_DIR ${EXPORTS_DIR}/ohpc/pub
  fi
}

copy_and_bind() {
  local src_dir=$1
  local dst_dir=$2
  local dst_pdir=$(dirname $dst_dir)

  mkdir -p $dst_dir
  if [[ $(fstype $dst_pdir) = "overlay" ]]; then
    echo "BAD filesystem: $(fstype $dst_pdir)"
    exit 1
  fi

  rsync -a $src_dir $dst_pdir
  if ! grep -q -e "$dst_dir" /etc/fstab; then
    echo "$dst_dir $src_dir none bind,noauto,x-systemd.automount 0 0" >> /etc/fstab
  fi
  mount --bind $dst_dir $src_dir
  [ $(fstype $src_dir) = "$FS_TYPE" ]
}

setup_home() {
  mkdir -p ${EXPORTS_DIR}/home
  if ! grep -q -e "/home" /etc/fstab; then
    echo "$EXPORTS_DIR/home /home none bind,noauto,x-systemd.automount 0 0" >> /etc/fstab
  fi
  mount --bind ${EXPORTS_DIR}/home /home
  [ $(fstype /home) = "$FS_TYPE" ]
}

create_etc_exports() {
  if [ -f /var/lib/vcp/.10-nfs_server-exports ]; then
    return
  fi
  cat > /etc/exports <<EOF
${EXPORTS_DIR}            ${EXPORTS_MACHINE_NAME}(rw,no_subtree_check,fsid=0)
${EXPORTS_DIR}/home       ${EXPORTS_MACHINE_NAME}(rw,no_subtree_check,nohide)
${EXPORTS_DIR}/ohpc/pub   ${EXPORTS_MACHINE_NAME}(ro,no_subtree_check,nohide)
EOF
  mkdir -p /var/lib/vcp
  touch /var/lib/vcp/.10-nfs_server-exports
}

setup() {
  setup_ohpc_pub
  setup_home
  create_etc_exports
}

setup
