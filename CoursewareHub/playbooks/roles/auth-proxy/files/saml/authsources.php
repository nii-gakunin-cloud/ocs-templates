<?php

$config = array(

    // This is a authentication source which handles admin authentication.
    'admin' => array(
        // The default is to use core:AdminPassword, but it can be replaced with
        // any authentication source.

        'core:AdminPassword',
    ),


    // An authentication source which can authenticate against both SAML 2.0
    // and Shibboleth 1.3 IdPs.
    'default-sp' => array(
        'saml:SP',
        'privatekey' => 'auth-proxy.key',
        'certificate' => 'auth-proxy.cer',

        //'entityID' => NULL,

        // The entity ID of the IdP this should SP should contact.
        // Can be NULL/unset, in which case the user will be shown a list of available IdPs.
        'idp' => NULL,

        // The URL to the discovery service.
        // Can be NULL/unset, in which case a builtin discovery service will be used.
        //'discoURL' => NULL,

        'name' => array (
            'en' => 'CoursewareHub SP',
        ),
        'attributes' => array (
            'eduPersonPrincipalName',
            'mail',
        ),
        'attributes.required' => array (
            'eduPersonPrincipalName',
            'mail',
        ),
        'attributes.NameFormat' => 'urn:oasis:names:tc:SAML:2.0:attrname-format:basic',
    ),
);
