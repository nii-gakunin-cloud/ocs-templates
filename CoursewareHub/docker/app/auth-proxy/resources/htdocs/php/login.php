<?php
require_once __DIR__ . '/../../lib/const.php';
require_once __DIR__ . '/../../lib/hub-const.php';
require_once __DIR__ . '/../../lib/functions.php';
require_once __DIR__ . '/../../lib/db.php';

@session_start();

// Recieved user name and password
$email = filter_input(INPUT_POST, 'email');
$password = filter_input(INPUT_POST, 'password');

// In case of POST method
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (validate_token(filter_input(INPUT_POST, 'token')) &&
        authenticate_local_user($email, $password)) 
    {
        session_regenerate_id(true);
        // Set Session info
        $username = get_username_from_mail_address($email);
        $_SESSION['username'] = $username;

        header("X-Accel-Redirect: /entrance/");
        header("X-Reproxy-URL: ".HUB_URL.'/'.COURSE_NAME."/hub/login");
        header("X-REMOTE-USER: $username");

        exit;
    }
    // 「403 Forbidden」
    http_response_code(403);
}

header('Content-Type: text/html; charset=UTF-8');
?>

<?xml version="1.0" encoding="euc-jp"?>
<!DOCTYPE html PUBLIC "-//W3C/DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">
<head>
<title>Sign In</title>
<style type="text/css">
/* Simple Reset */
* { margin: 0; padding: 0; box-sizing: border-box; }

/* body */
body {
  background: #e9e9e9;
  color: #5e5e5e;
  font: 400 87.5%/1.5em 'Open Sans', sans-serif;
}

/* Form Layout */
.form-wrapper {
  background: #fafafa;
  margin: 3em auto;
  padding: 0 1em;
  max-width: 370px;
}

h1 {
  text-align: center;
  padding: 1em 0;
}

form {
  padding: 0 1.5em;
}

.form-item {
  margin-bottom: 0.75em;
  width: 100%;
}

.form-item input {
  background: #fafafa;
  border: none;
  border-bottom: 2px solid #e9e9e9;
  color: #666;
  font-family: 'Open Sans', sans-serif;
  font-size: 1em;
  height: 50px;
  transition: border-color 0.3s;
  width: 100%;
}

.form-item input:focus {
  border-bottom: 2px solid #c0c0c0;
  outline: none;
}

.button-panel {
  margin: 2em 0 0;
  width: 100%;
}

.button-panel .button {
  background: #f16272;
  border: none;
  color: #fff;
  cursor: pointer;
  height: 50px;
  font-family: 'Open Sans', sans-serif;
  font-size: 1.2em;
  letter-spacing: 0.05em;
  text-align: center;
  text-transform: uppercase;
  transition: background 0.3s ease-in-out;
  width: 100%;
}

.button:hover {
  background: #ee3e52;
}

.form-footer {
  font-size: 1em;
  padding: 2em 0;
  text-align: center;
}

.form-footer a {
  color: #8c8c8c;
  text-decoration: none;
  transition: border-color 0.3s;
}

.form-footer a:hover {
  border-bottom: 1px dotted #8c8c8c;
}

.error-panel {
  font-size: 1em;
  text-align: center;
  color: #ee3e52;
}
</style>
</head>

<body>
<div class="form-wrapper">
  <h1>Sign In</h1>
  <?php if (http_response_code() === 403): ?> 
  <div class="error-panel">
  <p>ユーザ名またはパスワードが違います</p>
  </div>
  <?php endif; ?>

  <form method="POST" action="/php/login.php">
    <div class="form-item">
      <label for="email"></label>
      <input type="email" name="email" required="required" placeholder="Email Address"></input>
    </div>
    <div class="form-item">
      <label for="password"></label>
      <input type="password" name="password" required="required" placeholder="Password"></input>
    </div>
    <div class="button-panel">
      <input type="hidden" name="token" value="<?=h(generate_token())?>">
      <input type="submit" class="button" title="Sign In" value="Sign In"></input>
    </div>
  </form>
  <div class="form-footer">
  <?php if (file_exists(IDP_METADATA_FILE_PATH)) {?> 
    <p><a href="/php/sp.php">学認フェデレーションへ</a></p>
  <?php }?>
  </div>
</div>
</body>
</html>
