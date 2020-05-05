<?php
/**
 * Add local user.
 *
 * @param string mail-address of user. 
 * @output display mail-address and password of user.
 */
require_once __DIR__ . '/../lib/db.php';
require_once __DIR__ . '/../lib/functions.php';

$mail_addr = "$argv[1]";
$password = generate_password();

try {
    add_local_user($mail_addr, $password);
} catch (Exception $e) {
    echo "$mail_addr: ".$e->getMessage()."\n";
    exit(1);
}

echo "$mail_addr	$password"."\n";
exit;
?>
