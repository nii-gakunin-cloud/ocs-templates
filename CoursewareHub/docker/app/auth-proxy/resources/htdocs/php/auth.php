<?php
require_once __DIR__ . '/../../lib/functions.php';

# Redirect to the JupyterHub if local user was authenticated.
redirect_by_local_user_session();
# Redirect to the JupyterHub if Gakunin user was authenticated.
redirect_by_fed_user_session();

# No Authenticated
# Redirect to the Login page
header("X-Accel-Redirect: /entrance/");
header("X-Reproxy-URL: https://".$_SERVER['HTTP_HOST']."/login");
exit;
?>
