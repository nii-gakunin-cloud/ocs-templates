#!/bin/bash

setup_directory() {
  mkdir -p /var/log/slurm /var/spool/slurmd
  chown slurm:slurm /var/log/slurm /var/spool/slurmd
}

setup_slurm_conf() {
  if [ -f /var/lib/vcp/.20-slurm ]; then
    return
  fi
  /usr/local/bin/jinja2 -o /etc/sysconfig/slurmd /etc/vcp/rc.d/templates/slurmd.j2
  /usr/local/bin/jinja2 -o /etc/slurm/slurm.conf /etc/vcp/rc.d/templates/slurm.conf.j2
  chown slurm:slurm /etc/slurm/slurm.conf

  mkdir -p /var/lib/vcp
  touch /var/lib/vcp/.20-slurm
}

setup_nsswitch() {
  if [ -n "$ENABLE_NSS_SLURM" ]; then
    if [ -f /var/lib/vcp/.20-slurm-nsswitch ]; then
      return
    fi
    sed -r -i \
      -e '/^passwd:/s/(passwd:[ \t]+)/\1slurm /' -e '/^group:/s/(group:[ \t]+)/\1slurm /' \
      -e '/^hosts:/s/$/ slurm/' /etc/nsswitch.conf
    mkdir -p /var/lib/vcp
    touch /var/lib/vcp/.20-slurm-nsswitch
  fi
}

setup() {
  setup_slurm_conf
  setup_nsswitch
  setup_directory
}

setup
