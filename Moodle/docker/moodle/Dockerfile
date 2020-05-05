FROM harbor.vcloud.nii.ac.jp/vcp/moodle:common

ARG PHP_VERSION=php72u

ADD https://centos7.iuscommunity.org/ius-release.rpm /tmp/
RUN yum -y install epel-release \
  && yum -y localinstall /tmp/ius-release.rpm \
  && rm /tmp/ius-release.rpm
    
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
  mod_${PHP_VERSION}

COPY etc/php-opcache.ini /tmp
RUN cat /tmp/php-opcache.ini >> /etc/php.ini \
    && rm /tmp/php-opcache.ini
