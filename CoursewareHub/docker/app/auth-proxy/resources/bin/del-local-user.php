<?php
/**
 * Delete local users.
 *
 * @param string mail-address of user to delete. 
 * @output display deleted mail-address of user.
 */
require_once __DIR__ . '/../lib/db.php';
require_once __DIR__ . '/../lib/functions.php';

$mail_addr = "$argv[1]";
try {
    delete_local_users(array($mail_addr));
} catch (Exception $e) {
    echo "$mail_addr: ".$e->getMessage()."\n";
    exit(1);
}

echo "$mail_addr\n";
exit;
?>
