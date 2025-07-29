#!/bin/bash

: ${MASTER_HOSTNAME:=$(hostname)}

declare -A node_params

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
  /usr/local/bin/jinja2 -o /etc/slurm/slurm.conf /etc/vcp/rc.d/slurm.conf.j2
  chown slurm:slurm /etc/slurm/slurm.conf
  if [ -n "GPUS" ]; then
    /usr/local/bin/jinja2 -o /etc/slurm/gres.conf /etc/vcp/rc.d/gres.conf.j2
  fi
  mkdir -p /var/lib/vcp
  touch /var/lib/vcp/.20-slurm
}

setup() {
  setup_directory
  setup_service
  setup_slurm_conf
}

setup
