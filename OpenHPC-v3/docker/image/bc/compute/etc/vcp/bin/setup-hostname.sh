#!/bin/bash

# Hostname Setup Script for Compute Nodes
#
# This script sets the hostname by reading from NFS-shared hosts file.
# Called by: hostname-setup.service (after mount-nfs.service)
#
# Prerequisites:
#   - NFS mount at /opt/ohpc/pub must be available
#   - Master node must have generated /opt/ohpc/pub/etc/hosts.ohpc
#   - PRIVATE_IP environment variable must be set (passed from systemd service)

# Wait for NFS mount to be ready
wait_for_nfs_mount() {
  local mount_point="/opt/ohpc/pub"
  local max_wait=30

  for i in $(seq 1 $max_wait); do
    if mountpoint -q "$mount_point"; then
      echo "NFS mount confirmed at $mount_point"
      return 0
    fi
    echo "Waiting for NFS mount at $mount_point... ($i/$max_wait)"
    sleep 1
  done

  echo "Error: Timeout waiting for NFS mount at $mount_point" >&2
  return 1
}

get_hostname_from_nfs_hosts() {
  local ip="$1"
  local nfs_hosts="/opt/ohpc/pub/etc/hosts.ohpc"

  if [ -z "$ip" ]; then
    echo "Error: IP address is empty (PRIVATE_IP not set?)" >&2
    return 1
  fi

  if [ ! -f "$nfs_hosts" ]; then
    echo "Error: NFS hosts file not found: $nfs_hosts" >&2
    echo "Check if NFS is properly mounted and master node has generated the hosts file." >&2
    return 1
  fi

  # IPアドレスからホスト名を抽出
  local hostname=$(grep "^${ip}[[:space:]]" "$nfs_hosts" | awk '{print $2}')
  if [ -n "$hostname" ]; then
    echo "$hostname"
    return 0
  fi

  # IPアドレスがhostsファイルに見つからない場合
  echo "Error: IP address $ip not found in $nfs_hosts" >&2
  echo "Run Ansible playbook to register this compute node." >&2
  return 1
}

setup_hostname() {
  local hostname

  # Wait for NFS mount
  if ! wait_for_nfs_mount; then
    echo "Error: Cannot proceed without NFS mount" >&2
    exit 1
  fi

  # Debug: Show PRIVATE_IP value
  echo "PRIVATE_IP value: '$PRIVATE_IP'"

  hostname=$(get_hostname_from_nfs_hosts "$PRIVATE_IP")

  if [ -z "$hostname" ]; then
    echo "Error: Failed to determine hostname for IP: $PRIVATE_IP" >&2
    exit 1
  fi

  echo "$hostname" > /etc/hostname
  hostname "$hostname"

  echo "Hostname set to: $hostname (from IP: $PRIVATE_IP)"
}

setup_hostname
