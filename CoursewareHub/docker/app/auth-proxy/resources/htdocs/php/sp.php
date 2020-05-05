<?php
require_once __DIR__ . '/../../lib/const.php';
require_once __DIR__ . '/../../lib/hub-const.php';
require_once __DIR__ . '/../../lib/functions.php';
require_once __DIR__ . '/../../simplesamlphp/www/_include.php';

@session_start();

$as = new SimpleSAML_Auth_Simple('default-sp');
if (! $as->isAuthenticated()) {
    $as->requireAuth();
}
// get attributes
$attributes = $as->getAttributes();
$mail_address = $attributes[GF_ATTRIBUTES['mail']][0];
$group_list = $attributes[GF_ATTRIBUTES['isMemberOf']];
// check authorization
if (check_authorization($group_list)) {
    // redirect to authenticator of JupyterHub
    session_regenerate_id(true);
    $username = get_username_from_mail_address($mail_address);
    header("X-Accel-Redirect: /entrance/");
    header("X-Reproxy-URL: ".HUB_URL.'/'.COURSE_NAME."/hub/login");
    header("X-REMOTE-USER: $username");
} else {
    // redirect to message page
    header("X-Accel-Redirect: /no_author");
}

exit;
