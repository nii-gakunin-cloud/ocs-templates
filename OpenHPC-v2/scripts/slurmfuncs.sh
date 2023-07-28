#!/bin/bash

declare -A node_params

setup_directory() {
  mkdir -p /var/log/slurm /var/run/slurm
  chown slurm:slurm /var/log/slurm /var/run/slurm
  sed -i -r -e "/LogFile=/s#/var/log/(slurm[a-z].*\.log)#/var/log/slurm/\1#" /etc/slurm/slurm.conf
  sed -i -r -e "/PidFile=/s#/var/run/(slurm[a-z].*\.pid)#/var/run/slurm/\1#" /etc/slurm/slurm.conf
}

setup_service() {
  sed -i -r -e "/PIDFile=/s#/var/run/(slurm[a-z].*\.pid)#/var/run/slurm/\1#" /usr/lib/systemd/system/slurmd.service
  sed -i -e "/ExecStart=/aExecStartPre=/bin/mkdir -p /run/slurm\nExecStartPre=/usr/bin/chown slurm:slurm /run/slurm\nExecStartPre=/usr/bin/chown slurm:slurm /etc/slurm/slurm.conf\n" /usr/lib/systemd/system/slurmd.service
}

setup_control_machine() {
  if [ -n "$MASTER_HOSTNAME" ]; then
    sed -i -r -e "/SlurmctldHost/s/^SlurmctldHost=.+/SlurmctldHost=${MASTER_HOSTNAME}/" /etc/slurm/slurm.conf
  fi
}

setup_slurm_conf() {
  local param params_kv nodes_line node_name partition_line
  if [ -f /var/lib/vcp/.20-slurm ]; then
    return
  fi

  cp /etc/slurm/slurm.conf.ohpc /etc/slurm/slurm.conf
  sed -i -e '1,/TaskPlugin=/s/^TaskPlugin=/#TaskPlugin=/' /etc/slurm/slurm.conf
  sed -i -e '1,/JobCompType=/s/^JobCompType=/#JobCompType=/' /etc/slurm/slurm.conf
  chown slurm:slurm /etc/slurm/slurm.conf
  cp /etc/slurm/cgroup.conf.example /etc/slurm/cgroup.conf

  if [ -n "$SLURM_NODE_PARAMS" ]; then
    for param in ${SLURM_NODE_PARAMS//,/ }; do
      params_kv=(${param//:/ })
      node_params[${params_kv[0]}]=${params_kv[1]}
    done
    if [[ ! -v node_params["State"] ]]; then
      node_params["State"]="UNKNOWN"
    fi

    node_name=${node_params["NodeName"]}
    unset node_params["NodeName"]

    nodes_line="NodeName=$node_name"
    for param in ${!node_params[@]}; do
      nodes_line+=" ${param}=${node_params[$param]}"
    done

    partition_line="PartitionName=normal Nodes=${node_name} Default=YES MaxTime=24:00:00 State=UP"

    sed -i -e '/NodeName=/s/^NodeName/# NodeName/' -e '/PartitionName=/s/^PartitionName/# PartitionName/' /etc/slurm/slurm.conf
    echo $nodes_line >> /etc/slurm/slurm.conf
    echo $partition_line >> /etc/slurm/slurm.conf
    mkdir -p /var/lib/vcp
    touch /var/lib/vcp/.20-slurm
  fi
}

setup() {
  setup_slurm_conf
  setup_directory
  setup_service
  setup_control_machine
}
