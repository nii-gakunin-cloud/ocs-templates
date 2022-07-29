#!/bin/bash

: ${VCP_USER:=vcp}
: ${VCP_SHELL:=/bin/bash}
: ${AUTHORIZED_KEYS:?"AUTHORIZED_KEYS must be set!"}

setup_ssh_public_key() {
  eval KEYS_PATH="~${VCP_USER}/.ssh/authorized_keys"

  mkdir -p -m 700 $(dirname ${KEYS_PATH})
  touch ${KEYS_PATH}
  chmod go-rwx ${KEYS_PATH}
  chown -R ${VCP_USER}:${VCP_USER} $(dirname ${KEYS_PATH})

  echo ${AUTHORIZED_KEYS} | base64 -d >> ${KEYS_PATH}
}

setup_user() {
  if [ -f /var/lib/vcp/.10-user ]; then
    return
  fi
  groupadd -f -r docker
  useradd -m -s /bin/bash -U -G docker ${VCP_USER}

  if [ -z "${SUDO_NOT_PERMITTED}" ]; then
    echo "${VCP_USER} ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/vcp
  fi

  setup_ssh_public_key
  mkdir -p /var/lib/vcp
  touch /var/lib/vcp/.10-user
}

setup_user

