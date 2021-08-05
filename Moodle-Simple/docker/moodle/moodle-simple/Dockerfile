FROM centos:7

RUN yum -y update \
 && yum -y install \
      aspell \
      graphviz \
      graphviz-gd \
      ghostscript \
      httpd \
      which \
      patch \
 && yum clean all

RUN ln -sf /dev/stdout /var/log/httpd/access_log \
  && ln -sf /dev/stderr /var/log/httpd/error_log

ARG REMI_URL=http://ftp.riken.jp/Linux/remi/enterprise/remi-release-7.rpm
RUN yum -y install epel-release \
 && yum -y install ${REMI_URL} \
 && yum clean all

ARG WAIT_FOR_URL=https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN curl -o /usr/local/bin/wait-for-it.sh ${WAIT_FOR_URL} \
 && chmod a+x /usr/local/bin/wait-for-it.sh
    
ARG PHP_VERSION
RUN yum -y install --enablerepo=remi-${PHP_VERSION} \
  php \
  php-cli \
  php-gd \
  php-intl \
  php-mbstring \
  php-mysqlnd \
  php-opcache \
  php-pecl-zip \
  php-soap \
  php-xml \
  php-xmlrpc \
  php-json \
  php-ldap \
 && yum clean all

COPY etc/php-opcache.ini /tmp
RUN cat /tmp/php-opcache.ini >> /etc/php.d/10-opcache.ini \
    && rm /tmp/php-opcache.ini

ARG MOODLE_VERSION
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
