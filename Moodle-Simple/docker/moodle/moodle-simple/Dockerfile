FROM centos:7

RUN yum -y install \
  aspell \
  graphviz \
  graphviz-gd \
  ghostscript \
  httpd \
  which \
  patch

RUN ln -sf /dev/stdout /var/log/httpd/access_log \
  && ln -sf /dev/stderr /var/log/httpd/error_log

RUN yum -y install epel-release \
 && yum -y install \
      https://repo.ius.io/ius-release-el7.rpm \
      https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

ARG WAIT_FOR_URL=https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN curl -o /usr/local/bin/wait-for-it.sh ${WAIT_FOR_URL} \
 && chmod a+x /usr/local/bin/wait-for-it.sh
    
ARG PHP_VERSION=php73
RUN yum -y install \
  ${PHP_VERSION} \
  ${PHP_VERSION}-cli \
  ${PHP_VERSION}-gd \
  ${PHP_VERSION}-intl \
  ${PHP_VERSION}-mbstring \
  ${PHP_VERSION}-mysqlnd \
  ${PHP_VERSION}-opcache \
  ${PHP_VERSION}-soap \
  ${PHP_VERSION}-xml \
  ${PHP_VERSION}-xmlrpc \
  ${PHP_VERSION}-json \
  ${PHP_VERSION}-ldap \
  mod_${PHP_VERSION}

COPY etc/php-opcache.ini /tmp
RUN cat /tmp/php-opcache.ini >> /etc/php.d/10-opcache.ini \
    && rm /tmp/php-opcache.ini

ARG MOODLE_VERSION=3.9.1
RUN curl -L -o /tmp/moodle.tar.gz https://github.com/moodle/moodle/archive/v${MOODLE_VERSION}.tar.gz \
 && tar xzf /tmp/moodle.tar.gz -C /var/www \
 && rm /tmp/moodle.tar.gz \
 && rmdir /var/www/html \
 && mv /var/www/moodle-${MOODLE_VERSION} /var/www/moodle \
 && chown -R 48:48 /var/www/moodle \
 && ln -s /var/www/moodle /var/www/html

EXPOSE 80
COPY scripts /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/local/bin/init"]
