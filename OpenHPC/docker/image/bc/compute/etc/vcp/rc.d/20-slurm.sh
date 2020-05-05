#!/bin/bash

declare -A node_params

setup_control_machine() {
  if [ -n "$MASTER_HOSTNAME" ]; then
    sed -i -r -e "/ControlMachine/s/^ControlMachine=.+/ControlMachine=${MASTER_HOSTNAME}/" /etc/slurm/slurm.conf
  fi
}

setup_slurm_conf() {
  local param params_kv nodes_line node_name partition_line
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
      echo "${ipaddr} ${hosts[$ipaddr]}" >> /etc/hosts
      nodes_line+=" ${param}=${node_params[$param]}"
    done

    partition_line="PartitionName=normal Nodes=${node_name} Default=YES MaxTime=24:00:00 State=UP"

    sed -i -e '/NodeName=/s/^NodeName/# NodeName/' -e '/PartitionName=/s/^PartitionName/# PartitionName/' /etc/slurm/slurm.conf
    echo $nodes_line >> /etc/slurm/slurm.conf
    echo $partition_line >> /etc/slurm/slurm.conf
  fi
}


setup() {
  setup_control_machine
  setup_slurm_conf
}

setup
