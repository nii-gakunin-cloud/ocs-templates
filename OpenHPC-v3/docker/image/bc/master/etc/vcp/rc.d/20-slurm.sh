#!/bin/bash

: ${MASTER_HOSTNAME:=$(hostname)}

setup_directory() {
  mkdir -p /var/log/slurm
  chown slurm:slurm /var/log/slurm
}

setup_service() {
  if [ -f /var/lib/vcp/.20-slurm ]; then
    return
  fi
  sed -i -r -e "/PIDFile=/s#/var/run/(slurm[a-z].*\.pid)#/run/slurm/\1#" /usr/lib/systemd/system/slurmctld.service
}

setup_slurm_conf() {
  if [ -f /var/lib/vcp/.20-slurm ]; then
    return
  fi
  export MASTER_HOSTNAME

  # slurm.conf本体の生成（slurm.conf.j2から）
  # パーティション設定はAnsibleでpost-deploymentに追加される
  /usr/local/bin/jinja2 -o /etc/slurm/slurm.conf /etc/vcp/rc.d/templates/slurm.conf.j2
  chown slurm:slurm /etc/slurm/slurm.conf

  # gres.conf はイメージに同梱済み（configless modeで計算ノードに配布される）

  mkdir -p /var/lib/vcp
  touch /var/lib/vcp/.20-slurm
}

setup() {
  setup_directory
  setup_service
  setup_slurm_conf
}

setup
