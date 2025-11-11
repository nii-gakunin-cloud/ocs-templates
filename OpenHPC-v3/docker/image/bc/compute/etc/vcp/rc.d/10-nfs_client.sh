#!/bin/bash

validate_and_append_nfs_entries() {
  if [ -z "$OPTIONAL_NFS_FSTAB_BASE64" ]; then
    return
  fi

  local decoded
  if ! decoded=$(echo "$OPTIONAL_NFS_FSTAB_BASE64" | base64 -d 2>/dev/null); then
    echo "Warning: Failed to decode OPTIONAL_NFS_FSTAB_BASE64" >&2
    return
  fi

  echo "$decoded" | while IFS= read -r line; do
    if [ -z "$line" ]; then
      continue
    fi
    if [[ "$line" =~ ^[[:space:]]*# ]]; then
      continue
    fi

    # Validate fstab format (should have 6 fields)
    local field_count=$(echo "$line" | awk '{print NF}')
    if [ "$field_count" -lt 6 ]; then
      echo "Warning: Invalid fstab format (insufficient fields): $line" >&2
      continue
    fi

    local fs_type=$(echo "$line" | awk '{print $3}')
    if [[ "$fs_type" != "nfs" && "$fs_type" != "nfs4" ]]; then
      echo "Warning: Not an NFS entry (fs_type=$fs_type): $line" >&2
      continue
    fi

    local mount_point=$(echo "$line" | awk '{print $2}')
    mkdir -p "$mount_point"

    echo "$line" >> /etc/fstab
  done
}

setup_fstab() {
  if [ -f /var/lib/vcp/.10-nfs_client ]; then
    return
  fi

  # Append default NFS entries
  cat >> /etc/fstab <<EOF
${MASTER_HOSTNAME}:/ohpc/pub /opt/ohpc/pub nfs nfsvers=4,ro,nodev  0 0
${MASTER_HOSTNAME}:/home     /home         nfs nfsvers=4,rw,nodev  0 0
EOF

  # Append additional NFS entries if provided
  validate_and_append_nfs_entries

  mkdir -p /var/lib/vcp
  touch /var/lib/vcp/.10-nfs_client
}

setup_fstab
