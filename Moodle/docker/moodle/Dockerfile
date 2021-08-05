ARG BASE_IMAGE=harbor.vcloud.nii.ac.jp/vcp/moodle:common
# hadolint ignore=DL3006
FROM $BASE_IMAGE

ARG REMI_URL=http://ftp.riken.jp/Linux/remi/enterprise/remi-release-7.rpm
RUN yum -y install epel-release \
 && yum -y install  ${REMI_URL} \
 && yum clean all
    
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
RUN cat /tmp/php-opcache.ini >> /etc/php.ini \
    && rm /tmp/php-opcache.ini
