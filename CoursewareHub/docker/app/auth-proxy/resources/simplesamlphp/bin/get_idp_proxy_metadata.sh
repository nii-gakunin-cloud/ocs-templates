#/bin/bash

idp_proxy="$1"

idp_proxy_metadata_path=metadata/idp-proxy.xml
idp_entity_id="https://$idp_proxy/simplesaml/saml2/idp/metadata.php"
cd /var/www/simplesamlphp
curl --insecure --fail -o $idp_proxy_metadata_path https://$idp_proxy/simplesaml/saml2/idp/metadata.php
sed -i "s|#IDP_PROXY_XML#|array('type' => 'xml', 'file' => '$idp_proxy_metadata_path')|" config/config.php
sed -i "s|'idp' => .*|'idp' => '$idp_entity_id',|" config/authsources.php
