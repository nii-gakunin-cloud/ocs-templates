FROM niicloudoperation/idp-proxy
# The container image niicloudoperation/idp-proxy is a build of 
# https://github.com/NII-cloud-operation/CoursewareHub-LC_idp-proxy
# with default settings.

ARG CWH_LC_IDPPROXY_RAW_URL=https://raw.githubusercontent.com/NII-cloud-operation/CoursewareHub-LC_idp-proxy/master/resources/simplesamlphp/config
RUN curl -f -o /var/www/simplesamlphp/config/config.php.prod-fed \
        ${CWH_LC_IDPPROXY_RAW_URL}/config.php \
 && curl -f -o /var/www/simplesamlphp/config/config.php.test-fed \
        ${CWH_LC_IDPPROXY_RAW_URL}/config-test.php \
 && curl -f -o /var/www/simplesamlphp/config/config-metarefresh.php.prod-fed \
        ${CWH_LC_IDPPROXY_RAW_URL}/config-metarefresh.php \
 && curl -f -o /var/www/simplesamlphp/config/config-metarefresh.php.test-fed \
        ${CWH_LC_IDPPROXY_RAW_URL}/config-metarefresh-test.php

COPY scripts /usr/local/bin/

CMD ["/usr/local/bin/start-vcp.sh"]
