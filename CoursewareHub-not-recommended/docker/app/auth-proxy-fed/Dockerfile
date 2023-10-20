FROM niicloudoperation/auth-proxy-fed:latest
# The container image niicloudoperation/auth-proxy-fed is a build of the auth-proxy-fed/ 
# directory of https://github.com/NII-cloud-operation/CoursewareHub-LC_platform
# with default settings.

ARG CWH_LC_PLATFORM_RAW_URL=https://raw.githubusercontent.com/NII-cloud-operation/CoursewareHub-LC_platform/master/auth-proxy-fed/resources/simplesamlphp/config
RUN curl -f -o /var/www/simplesamlphp/config/config.php.prod-fed \
        ${CWH_LC_PLATFORM_RAW_URL}/config.php \
 && curl -f -o /var/www/simplesamlphp/config/config.php.test-fed \
        ${CWH_LC_PLATFORM_RAW_URL}/config-test.php \
 && curl -f -o /var/www/simplesamlphp/config/config-metarefresh.php.prod-fed \
        ${CWH_LC_PLATFORM_RAW_URL}/config-metarefresh.php \
 && curl -f -o /var/www/simplesamlphp/config/config-metarefresh.php.test-fed \
        ${CWH_LC_PLATFORM_RAW_URL}/config-metarefresh-test.php

ARG WAIT_FOR_SCRIPT_URL=https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN curl -f -o /usr/local/bin/wait-for-it.sh ${WAIT_FOR_SCRIPT_URL} \
 && chmod a+x /usr/local/bin/wait-for-it.sh

COPY scripts /usr/local/bin/

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/local/bin/start-vcp.sh"]
