<?php
/**
 * Reset the password of the local user.
 *
 * @param string mail-address of user to reset the password. 
 * @output display the mail-address and the password of user.
 */
require_once __DIR__ . '/../lib/db.php';
require_once __DIR__ . '/../lib/functions.php';

$mail_addr = "$argv[1]";
$password = generate_password();
try {
    update_local_user_password($mail_addr, $password);
} catch (Exception $e) {
    echo "$mail_addr: ".$e->getMessage()."\n";
    exit(1);
}

echo "$mail_addr	$password\n";
exit;
?>
