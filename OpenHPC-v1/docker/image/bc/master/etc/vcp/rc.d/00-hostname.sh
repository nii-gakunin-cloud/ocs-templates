#!/bin/bash

declare -A hosts

setup_etc_hosts() {
  local host_kv host ipaddr
  if [[ -n "$ETC_HOSTS" ]]; then
    for host in ${ETC_HOSTS//,/ }; do
      host_kv=(${host//:/ })
      hosts[${host_kv[0]}]=${host_kv[1]}
    done

    for ipaddr in ${!hosts[@]}; do
      echo "${ipaddr} ${hosts[$ipaddr]}" >> /etc/hosts
    done
  fi
}

setup_hostname() {
  if [[ -n "$MY_HOSTNAME" ]]; then
    echo $MY_HOSTNAME > /etc/hostname
  elif [[ -n "$SMS_HOSTNAME" ]]; then
    echo $SMS_HOSTNAME > /etc/hostname
  elif [[ -n "${hosts[$PRIVATE_IP]}" ]]; then
    echo ${hosts[$PRIVATE_IP]} > /etc/hostname
  fi
}

setup() {
  setup_etc_hosts
  setup_hostname
}

setup
