FROM {{moodle_image_name}}

RUN yum -y install mod_ssl
RUN ln -sf /dev/stdout /var/log/httpd/ssl_access_log \
  && ln -sf /dev/stderr /var/log/httpd/ssl_error_log
