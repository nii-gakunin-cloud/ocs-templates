<?php

require_once __DIR__ . '/../../lib/functions.php';
@session_start();

// remove cookies
setcookie(session_name(), '', time() - 1800, '/');
setcookie('jupyter-hub-token', '', time() - 1800, '/');
setcookie('_xsrf', '', time() - 1800, '/');
// logout federation authentication
logout_fed();
// destroy session
session_destroy();
// redirect to login
header('Location: /login');
