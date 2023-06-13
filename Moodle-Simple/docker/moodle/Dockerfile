FROM rockylinux:8.8.20230518

RUN dnf -y update \
 && dnf -y install \
      aspell \
      graphviz \
      ghostscript \
      httpd \
      which \
      patch \
 && dnf clean all

RUN ln -sf /dev/stdout /var/log/httpd/access_log \
  && ln -sf /dev/stderr /var/log/httpd/error_log

ARG REMI_URL=http://ftp.riken.jp/Linux/remi/enterprise/remi-release-8.rpm
RUN dnf -y install epel-release \
 && dnf -y install ${REMI_URL} \
 && dnf clean all

ARG WAIT_FOR_URL=https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN curl -o /usr/local/bin/wait-for-it.sh ${WAIT_FOR_URL} \
 && chmod a+x /usr/local/bin/wait-for-it.sh
    
ARG PHP_VERSION=8.0
RUN dnf -y module reset php \
 && dnf -y module install php:remi-${PHP_VERSION} \
 && dnf -y install \
  php-gd \
  php-intl \
  php-mysqlnd \
  php-opcache \
  php-pecl-zip \
  php-soap \
  php-xmlrpc \
  php-ldap \
  php-sodium \
 && dnf clean all

COPY php/php-opcache.ini /tmp
RUN cat /tmp/php-opcache.ini >> /etc/php.d/10-opcache.ini \
    && rm /tmp/php-opcache.ini \
    && sed -ri -e '/max_input_vars/s/\;?\s*max_input_vars\s*=.+$/max_input_vars = 5000/' /etc/php.ini

RUN dnf -y install supervisor \
 && dnf clean all

ARG MOODLE_VERSION
RUN curl -L -o /tmp/moodle.tar.gz https://github.com/moodle/moodle/archive/v${MOODLE_VERSION}.tar.gz \
 && tar xzf /tmp/moodle.tar.gz -C /var/www \
 && rm /tmp/moodle.tar.gz \
 && rmdir /var/www/html \
 && mv /var/www/moodle-${MOODLE_VERSION} /var/www/moodle \
 && chown -R 48:48 /var/www/moodle \
 && ln -s /var/www/moodle /var/www/html \
 && sed -i -e '/Indexes/s/Options Indexes/Options/' /etc/httpd/conf/httpd.conf

COPY etc /etc/
COPY scripts /usr/local/bin/
EXPOSE 80
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["/usr/local/bin/init"]
