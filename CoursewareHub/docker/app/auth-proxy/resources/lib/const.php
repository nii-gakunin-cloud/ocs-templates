<?php
// Attribute dictionary for Gakunnin federation 
const GF_ATTRIBUTES = array(
  "mail" => "urn:oid:0.9.2342.19200300.100.1.3",
  "eduPersonPrincipalName" => "urn:oid:1.3.6.1.4.1.5923.1.1.1.6",
  "jaDisplayName" => "urn:oid:1.3.6.1.4.1.32264.1.1.3",
  "displayName" => "urn:oid:2.16.840.1.113730.3.1.241",
  "isMemberOf" => "urn:oid:1.3.6.1.4.1.5923.1.5.1.1",
);

// Path of IdP metadata file
const IDP_METADATA_FILE_PATH = "/var/www/simplesamlphp/metadata/idp-proxy/saml20-idp-remote.php";
?>
