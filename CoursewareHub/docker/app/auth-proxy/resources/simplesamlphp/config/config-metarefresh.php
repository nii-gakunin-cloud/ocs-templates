<?php

$config = array(
    'sets' => array(
        'idp-proxy' => array(
            'cron' => array('daily'),
            'sources' => array(
                array(
                    'src' => 'https://nbhub.ecloud.nii.ac.jp/simplesaml/saml2/idp/metadata.php',
                    'certificates' => array(
                        'idp-proxy.cer'
                    )
                )
            ),
            'outputDir' => 'metadata/idp-proxy/',
            'outputFormat' => 'flatfile',
            'expireAfter' => 60*60*24*4
        )
    )
);

