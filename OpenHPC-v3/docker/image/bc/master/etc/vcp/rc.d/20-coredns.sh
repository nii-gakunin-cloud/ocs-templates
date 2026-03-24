#!/bin/bash

: ${DNS_DOMAIN:="ohpc.internal"}
: ${DNS_FORWARDERS:="8.8.8.8,8.8.4.4"}
: ${MASTER_HOSTNAME:=$(hostname)}

setup_coredns_config() {
  if [ -f /var/lib/vcp/.20-coredns ]; then
    return
  fi

  # マスターノードのIPアドレスを環境変数から取得してエクスポート
  export MASTER_IP=${PRIVATE_IP}
  export DNS_DOMAIN DNS_FORWARDERS

  # Corefile の生成
  /usr/local/bin/jinja2 -o /etc/coredns/Corefile /etc/vcp/rc.d/templates/Corefile.j2
  chown root:root /etc/coredns/Corefile
  chmod 644 /etc/coredns/Corefile

  # 初期hostsファイルの生成
  generate_initial_hosts_file

  mkdir -p /var/lib/vcp
  touch /var/lib/vcp/.20-coredns
}

generate_initial_hosts_file() {
  local hosts_file="/opt/ohpc/pub/etc/hosts.ohpc"

  # hostsファイルの生成（NFS共有領域に直接生成）
  # 計算ノードのエントリはAnsibleで管理
  mkdir -p /opt/ohpc/pub/etc
  cat > "$hosts_file" <<EOF
# OpenHPC cluster hosts
# Managed by Ansible - DO NOT EDIT MANUALLY

# Master node
${MASTER_IP}    ${MASTER_HOSTNAME} ${MASTER_HOSTNAME}.${DNS_DOMAIN}

EOF

  chown root:root "$hosts_file"
  chmod 644 "$hosts_file"
}

setup() {
  setup_coredns_config
}

setup
