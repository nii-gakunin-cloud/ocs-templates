#!/bin/bash

: ${VCP_DIR:=/var/lib/vcp}

init_simplesamlphp_config () {(
  cd /var/www/simplesamlphp/config
  if [[ ${GAKUNIN_FEDERATION,,} = "test" ]]; then
    federation=test
  else
    federation=prod
  fi
  cp config.php.${federation}-fed config.php
  cp config-metarefresh.php.${federation}-fed config-metarefresh.php
)}

update_simplesamlphp () {(
  cd /var/www/simplesamlphp
  if [[ -n "$MASTER_FQDN" ]]; then
    sed -i -e "s;'entityID' => .*;'entityID' => 'https://${MASTER_FQDN}/shibboleth-sp',;" \
        config/authsources.php
    sed -i -e "s,var wayf_sp_handlerURL = .*,var wayf_sp_handlerURL = \"https://${MASTER_FQDN}/simplesaml/module.php/saml/sp/discoresp.php\";," \
        templates/selectidp-dropdown.php
  fi
  if [[ ${GAKUNIN_FEDERATION,,} = "test" ]]; then
    : ${CG_FQDN:=sptest.cg.gakunin.jp}
    : ${DS_FQDN:=test-ds.gakunin.nii.ac.jp}
  else
    : ${CG_FQDN:=cg.gakunin.jp}
    : ${DS_FQDN:=ds.gakunin.nii.ac.jp}
  fi

  sed -i -e "s;'entityId' => .*;'entityId' => 'https://${CG_FQDN}/idp/shibboleth',;" \
      config/config.php
  sed -i \
      -e "s,var embedded_wayf_URL = .*,var embedded_wayf_URL = \"https://${DS_FQDN}/WAYF/embedded-wayf.js\";," \
      -e "s,var wayf_URL = .*,var wayf_URL = \"https://${DS_FQDN}/WAYF\";," \
      templates/selectidp-dropdown.php
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
  init_simplesamlphp_config
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
