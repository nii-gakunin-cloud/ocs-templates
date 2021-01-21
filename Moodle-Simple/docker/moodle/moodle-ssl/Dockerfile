ARG MOODLE_VERSION
FROM harbor.vcloud.nii.ac.jp/vcp/moodle-simple:$MOODLE_VERSION

RUN yum -y install mod_ssl \
 && yum clean all
RUN ln -sf /dev/stdout /var/log/httpd/ssl_access_log \
  && ln -sf /dev/stderr /var/log/httpd/ssl_error_log
