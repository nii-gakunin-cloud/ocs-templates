<?php
  require_once __DIR__ . '/../lib/functions.php';
  $mail_addr = "$argv[1]";

  echo get_username_from_mail_address($mail_addr);
