<?php
require_once __DIR__ . '/hub-const.php';
require_once __DIR__ . '/const.php';
require_once __DIR__ . '/../simplesamlphp/www/_include.php';

$SESSION_NAME = session_name();


function redirect_to_hub()
{
    $reproxy_url = HUB_URL.implode('/', array_map('rawurlencode', explode('/', $_SERVER['HTTP_X_REPROXY_URI'])));
    if (array_key_exists('HTTP_X_REPROXY_QUERY', $_SERVER)) {
        $reproxy_url = $reproxy_url.$_SERVER['HTTP_X_REPROXY_QUERY'];
    }
    header("X-Accel-Redirect: /entrance/");
    header("X-Reproxy-URL: ".$reproxy_url);
}

/**
 * Redirect to the JupyterHub if local user was authenticated.
 */
function redirect_by_local_user_session()
{
    @session_start();

    if (isset($_SESSION['username'])) {
        // check user entry

        // redirect to hub
        redirect_to_hub();
        exit;
    }
}

/**
 * Redirect to the JupyterHub if Gakunin user was authenticated.
 */
function redirect_by_fed_user_session()
{
    @session_start();

    // if idp metadata file does not exist, cancel the session check.
    if (!file_exists(IDP_METADATA_FILE_PATH)) {
        return;
    }

    $as = new SimpleSAML_Auth_Simple('default-sp');
    if ($as->isAuthenticated()) {
        // maybe access to other course
        // redirect to authenticator of JupyterHub
        $attributes = $as->getAttributes();
        $mail_address = $attributes[GF_ATTRIBUTES['mail']][0];
        $group_list = $attributes[GF_ATTRIBUTES['isMemberOf']];

        // check authorization
        if (check_authorization($group_list)) {
            $username = get_username_from_mail_address($mail_address);
            header("X-REMOTE-USER: $username");
            redirect_to_hub();
        } else {
            // redirect to message page
            header("X-Accel-Redirect: /no_author");
        }
        exit;
    }
}

/**
 * Logout from the federation
 */
function logout_fed()
{
    $as = new SimpleSAML_Auth_Simple('default-sp');
    if ($as->isAuthenticated()) {
        $as->logout();
    }
}

/**
 * Check the user autorization of this Coursen
 *
 * @param string $group_list list of groups where a user belongs to
 * @return bool True if user authorized, otherwise False
 */
function check_authorization($group_list)
{
    $result = False;
    if (empty(AUTHOR_GROUP_LIST)) {
        $result = True;
    } else {
       foreach ($group_list as $group) {
           if (in_array($group, AUTHOR_GROUP_LIST)) {
               $result = True;
               break;
           }
       }
    }

    return $result;
}

/**
 * Generate CSRF token based on th session id.
 *
 * @return string  generated token
 */
function generate_token()
{
    return hash('sha256', session_id());
}

/**
 * Validate CSRF token
 *
 * @param string $token  CSRF token
 * @return bool  result of validation
 */
function validate_token($token)
{
    return $token === generate_token();
}

/**
 * Wraper function of the 'htmlspecialchars'
 *
 * @param string $str  source string
 * @return string  entity string
 */
function h($str)
{
    return htmlspecialchars($str, ENT_QUOTES, 'UTF-8');
}

/**
 * Get local username form user's mail address
 *
 * @param string $str  mail_address
 * @return string  local username
 */
function get_username_from_mail_address($mail_address)
{
    $result = "";

    // Convert to lower and remove characters except for alphabets and digits
    $wk = explode("@", $mail_address);
    $local_part = strtolower($wk[0]);
    $result = preg_replace('/[^a-zA-Z0-9]/', '', $local_part);
    // Add top 6bytes of hash string
    $hash = substr(md5($mail_address), 0, 6);
    $result .= 'x';
    $result .= $hash;

    return $result;
}


function generate_password($length = 10)
{
    $exclude = "/[1I0O\"\'\(\)\^~\\\`\{\}_\?<>]/";

    while(true) {
        $password = exec("pwgen -1ys $length");
        if (preg_match($exclude, $password)) {
            continue;
        }
        break;
    }
    return $password;
}
