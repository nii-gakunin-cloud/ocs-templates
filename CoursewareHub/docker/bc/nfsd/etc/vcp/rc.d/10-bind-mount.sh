#!/bin/bash

: ${DONE_FILE:=/var/lib/vcp/.10-bind-mount}
: ${HUB_NAME:="$UGROUP_NAME"}
: ${EXPORT_DIR:=/exported}

set -eu

mount_points=("/jupyter" "/exchange")
IFS=: mount_points+=(${EXTRA_MOUNT_POINTS:-})

setup_bind_mount () {
if [ -n "$HUB_NAME" ]; then
  cat > /etc/sysconfig/coursewarehub-dirs <<EOF
EXPORT_DIR=${EXPORT_DIR}
HUB_NAME=${HUB_NAME}
EOF

  touch /etc/fstab
  for mp in "${mount_points[@]}"; do
    src_dir="${EXPORT_DIR}/${HUB_NAME}${mp}"
    mkdir -p "$mp" "$src_dir"
    if ! grep -q -e "$mp" /etc/fstab; then
      echo "$src_dir $mp none bind 0 0" >> /etc/fstab
    fi
  done
else
  rm -f /etc/systemd/system/multi-user.target.wants/coursewarehub-dirs.service
fi
}

if [ ! -f "${DONE_FILE}" ]; then
  setup_bind_mount
  mkdir -p $(dirname "${DONE_FILE}")
  touch "${DONE_FILE}"
fi
