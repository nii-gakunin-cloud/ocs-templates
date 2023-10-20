FROM niicloudoperation/auth-proxy:latest
# The container image niicloudoperation/auth-proxy is a build of the auth-proxy/ 
# directory of https://github.com/NII-cloud-operation/CoursewareHub-LC_platform
# with default settings.

ARG WAIT_FOR_SCRIPT_URL=https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN curl -f -o /usr/local/bin/wait-for-it.sh ${WAIT_FOR_SCRIPT_URL} \
 && chmod a+x /usr/local/bin/wait-for-it.sh

COPY scripts /usr/local/bin/

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/local/bin/start-vcp.sh"]
