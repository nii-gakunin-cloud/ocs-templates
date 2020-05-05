<?php
require_once __DIR__ . '/hub-const.php';
require_once __DIR__ . '/functions.php';

// DSN for Database 
const DSN = 'pgsql:dbname='. DB_NAME. ' host=' . DB_HOST. ' port=' . DB_PORT;

/**
 * Add local user.
 *
 * @param string $mail_addr  mail address of user to be added. 
 * @param string $password  password of user to be added. 
 */
function add_local_user($mail_addr, $password)
{
    if (empty($mail_addr) || empty($password)) {
       // under construct:
    }

    $user_info = array(array('mail_addr' => $mail_addr, 'password' => $password));
    try {
        add_local_users($user_info);
    } catch (Exception $e) {
        throw $e;
    }
}


/**
 * Add local users.
 *
 * @param string $user_info  array of user's mail address and password to be added. 
 */
function add_local_users($user_info)
{
    $insert = "INSERT INTO local_users VALUES(nextval('local_users_id_seq'), :user_name, :password, :mail);";
    try {
        $dbh = new PDO(DSN, DB_USER, DB_PASS, array(PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION));
    } catch (Exception $e) {
        $dbh = null;
        throw $e;
    } 

    try {
        $dbh->beginTransaction(); 
        $st = $dbh->prepare($insert);
        foreach ($user_info as $info) {
            $user_name = get_username_from_mail_address($info['mail_addr']);
            $hashed_password = password_hash($info['password'], CRYPT_BLOWFISH); 
            $rep = $st->execute(array(':user_name'=>$user_name, ':password'=>$hashed_password, ':mail'=>$info['mail_addr']));
        }
        $rep = $dbh->commit(); 
        $st = null;
        $dbh = null;
    } catch (Exception $e) {
        $st = null;
        $dbh = null;
        throw $e;
    } 
}


/**
 * Delete local users.
 *
 * @param string $mail_addrs array of user's mail address to be deleted. 
 */
function delete_local_users($mail_addrs)
{
    $delete = "DELETE FROM local_users where user_name = :user_name;";
    try {
        $dbh = new PDO(DSN, DB_USER, DB_PASS, array(PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION));
    } catch (Exception $e) {
        $dbh = null;
        throw $e;
    } 
    $st = null;
    try {
        $dbh->beginTransaction(); 
        $st = $dbh->prepare($delete);
        foreach ($mail_addrs as $mail) {
            $user_name = get_username_from_mail_address($mail);
            $st->execute(array(':user_name' => $user_name));
        }
        $dbh->commit(); 
        $st = null;
        $dbh = null;
    } catch (Exception $e) {
        $st = null;
        $dbh = null;
        throw $e;
    } 
}


/**
 * Delete local user by ID.
 *
 * @param int $id id of user's record to be deleted. 
 */
function delete_local_user_by_id($id)
{
    $delete = "DELETE FROM local_users where id = :id;";
    try {
        $dbh = new PDO(DSN, DB_USER, DB_PASS, array(PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION));
    } catch (Exception $e) {
        $dbh = null;
        throw $e;
    } 
    $st = null;
    try {
        $dbh->beginTransaction(); 
        $st = $dbh->prepare($delete);
        $st->execute(array(':id' => $id));
        $dbh->commit(); 
        $st = null;
        $dbh = null;
    } catch (Exception $e) {
        $st = null;
        $dbh = null;
        throw $e;
    } 
}


/**
 * Update password of local user.
 *
 * @param string $mail_addr user's email address to reset the password. 
 */
function update_local_user_password($mail_addr, $password)
{
    $update = "UPDATE local_users set password = :password where user_name = :user_name;";
    try {
        $dbh = new PDO(DSN, DB_USER, DB_PASS, array(PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION));
    } catch (Exception $e) {
        $dbh = null;
        throw $e;
    } 
    $st = null;
    try {
        $dbh->beginTransaction(); 
        $st = $dbh->prepare($update);
        $user_name = get_username_from_mail_address($mail_addr);
        $hashed_password = password_hash($password, CRYPT_BLOWFISH);
        $st->execute(array(':password' => $hashed_password, ':user_name' => $user_name));
        $dbh->commit(); 
        $st = null;
        $dbh = null;
    } catch (Exception $e) {
        $st = null;
        $dbh = null;
        throw $e;
    } 
}


/**
 * Authenticated local users.
 *
 * @param string $mail_addr  mail address of user. 
 * @param string $password  password of user. 
 * @return boolean return True if user was authenticated, owtherwise return False.
 */
function authenticate_local_user($mail_addr, $password)
{
    $result = False;

    if (!empty($mail_addr) && !empty($password)) {
        $query = "SELECT * FROM local_users where mail = :mail_addr;";
        try {
            $dbh = new PDO(DSN, DB_USER, DB_PASS, array(PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION));
        } catch (Exception $e) {
            $dbh = null;
            throw $e;
        } 
        $st = $dbh->prepare($query);
        $st->execute(array(':mail_addr' => $mail_addr));
        if ($row = $st->fetch(PDO::FETCH_ASSOC)) {
            if (password_verify($password, $row['password'])) {
                $result = True;
            }
        }
        $st = null;
        $dbh = null;
    }

    return $result;
}

?>
