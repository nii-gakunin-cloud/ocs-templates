#/bin/bash

cd /var/www/simplesamlphp
idp_proxy_metadata_path=metadata/idp-proxy.xml
[ -e "$metadata" ] {
    rm -rf "$idp_proxy_metadata_path"
    sed -i "s|array('type' => 'xml', 'file' => '$idp_proxy_metadata_path')|#IDP_PROXY_XML#|" config/config.php
}
