#!/bin/bash

: ${VCP_DIR:=/var/lib/vcp}

update_simplesamlphp () {(
  cd /var/www/simplesamlphp/config
  if [[ -n "$MASTER_FQDN" ]]; then
    sed -i -e "s;'entityID' => .*;'entityID' => 'https://${MASTER_FQDN}/simplesaml/module.php',;" \
        authsources.php
  fi
  if [[ -n "$AUTH_FQDN" ]]; then
    sed -i -e "s;'idp' => .*;'idp' => 'https://${AUTH_FQDN}/simplesaml/saml2/idp/metadata.php',;" \
        authsources.php
    sed -i -e "s;'src' => .*;'src' => 'https://${AUTH_FQDN}/simplesaml/saml2/idp/metadata.php',;" \
        config-metarefresh.php
  else
    rm /var/www/simplesamlphp/modules/metarefresh/enable
  fi
)}

update_hub_const_php () {(
  cd /var/www/lib
  echo "${MD5_HUB_CONST:-ce979c9c0050457416e8faef3f5d58c0} hub-const.php" | md5sum -c - > /dev/null 2>&1
  if [[ $? -ne 0 ]]; then
    return
  fi
  cat > hub-const.php <<EOF
<?php
const COURSE_NAME = "";
const HUB_URL = "http://jupyterhub:8000";
const AUTHOR_GROUP_LIST = array (${CG_GROUPS});
const DB_USER = "${POSTGRES_USER:-jhauth}";
const DB_PASS = "${POSTGRES_PASSWORD}";
const DB_PORT = "5432";
const DB_NAME = "${POSTGRES_DB:-jupyterhub}";
const DB_HOST = "postgres";
?>
EOF
)}

update_supervisord_conf() {(
  cd /etc
  echo "${MD5_SUPERVISORD_CONF:-4afccd92ae5e16fbe87acbca57d8805d} supervisord.conf" | md5sum -c - > /dev/null 2>&1
  if [[ $? -ne 0 ]]; then
    return
  fi
  sed -i -e '/^pidfile=/s/)//' supervisord.conf
  cat >> supervisord.conf <<EOF

[unix_http_server]
file=/var/run/supervisord.sock

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisord.sock
EOF
)}

setup_cron_secret () {
  if [[ -n "${CRON_SECRET}" ]]; then
    return
  fi
  if [[ -f /run/secrets/cron_secret ]]; then
    export CRON_SECRET=$(cat /run/secrets/cron_secret)
  fi
}

setup_config () {
  update_simplesamlphp
  update_hub_const_php
  update_supervisord_conf
}

setup () {
  mkdir -p $VCP_DIR
  if [[ ! -e ${VCP_DIR}/.done_config ]]; then
    setup_config
    touch ${VCP_DIR}/.done_config
  fi
  setup_cron_secret
  export HUB_NAME=${HUB_NAME:-jupyterhub}
}

setup

exec /start.sh
