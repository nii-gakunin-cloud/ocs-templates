# syntax=docker/dockerfile:1
FROM rockylinux/rockylinux:9.7.20251123 AS base

RUN dnf -y update \
 && dnf -y install 'dnf-command(config-manager)' \
 && dnf config-manager --set-enabled crb \
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

ARG REMI_URL=http://ftp.riken.jp/Linux/remi/enterprise/remi-release-9.rpm
RUN dnf -y install ${REMI_URL} \
 && dnf clean all

ARG PHP_VERSION=8.4
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
  php-tidy \
 && dnf clean all

COPY php/php-opcache.ini /tmp
RUN cat /tmp/php-opcache.ini >> /etc/php.d/10-opcache.ini \
    && rm /tmp/php-opcache.ini \
    && sed -ri -e '/max_input_vars/s/\;?\s*max_input_vars\s*=.+$/max_input_vars = 5000/' /etc/php.ini

RUN dnf -y install supervisor fcgi \
 && dnf clean all

ARG MOODLE_VERSION
RUN curl -L -o /tmp/moodle.tar.gz https://github.com/moodle/moodle/archive/v${MOODLE_VERSION}.tar.gz \
 && tar xzf /tmp/moodle.tar.gz -C /var/www \
 && rm /tmp/moodle.tar.gz \
 && rmdir /var/www/html \
 && mv /var/www/moodle-${MOODLE_VERSION} /var/www/moodle \
 && chown -R 48:48 /var/www/moodle \
 && sed -i -e '/Indexes/s/Options Indexes/Options/' /etc/httpd/conf/httpd.conf

WORKDIR /var/www/moodle
COPY scripts /usr/local/bin/
COPY etc /etc/

FROM base AS v4

RUN ln -s /var/www/moodle /var/www/html
COPY etc.v4/httpd/conf.d/moodle.conf /etc/httpd/conf.d/moodle.conf

EXPOSE 80
CMD ["/usr/local/bin/init"]
HEALTHCHECK --interval=10s --start-period=150s --retries=6 CMD /usr/local/bin/healthcheck

FROM base

# Install Composer (required for Moodle 5.1 vendor dependencies)
RUN curl -sS https://getcomposer.org/installer -o /tmp/composer-installer.php \
 && php /tmp/composer-installer.php --filename=composer --install-dir=/usr/local/bin \
 && rm /tmp/composer-installer.php \
 && composer --version

# Reset ownership after composer creates vendor directory
RUN composer install --no-dev --classmap-authoritative \
 && chown -R 48:48 /var/www/moodle \
 && ln -s /var/www/moodle/public /var/www/html

EXPOSE 80
CMD ["/usr/local/bin/init"]
HEALTHCHECK --interval=10s --start-period=150s --retries=6 CMD /usr/local/bin/healthcheck
