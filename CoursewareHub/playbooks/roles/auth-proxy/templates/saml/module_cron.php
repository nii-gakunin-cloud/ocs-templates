<?php
/*
 * Configuration for the Cron module.
 */

$config = array (
        'key' => '{{cron_key}}',
        'allowed_tags' => array('daily', 'hourly', 'frequent'),
        'debug_message' => TRUE,
        'sendemail' => FALSE,
);
