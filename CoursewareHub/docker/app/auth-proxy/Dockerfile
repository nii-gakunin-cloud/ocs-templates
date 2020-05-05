FROM ubuntu:18.04

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Update cache and install base packages
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install -y --no-install-recommends gnupg2 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
RUN set -x \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 00A6F0A3C300EE8C \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 4F4EA0AAE5267A6C \
    #&& apt-key adv --recv-keys --keyserver keyserver.ubuntu.com \
    && apt-get update \
    && apt-get -y --force-yes install --no-install-recommends \
        software-properties-common \
        pwgen \
        curl \
        git \
        unzip \
        supervisor \
        cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# hadolint ignore=SC2010,DL3003
RUN set -x \
    && add-apt-repository ppa:nginx/stable \
    && add-apt-repository ppa:ondrej/php \
    && apt-get update \
    && apt-get -y --force-yes --no-install-recommends --no-install-suggests install \
        nginx \
        php5.6-cli \
        php5.6-fpm \
        php5.6-common \
        php5.6-xml \
        php5.6-pgsql \
    && ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log \
    && mkdir -p /run/php \
    # Install simplesamlphp
    && cd /var/www \
    && curl -Lo /var/www/downloaded-simplesamlphp.tar.gz https://github.com/simplesamlphp/simplesamlphp/releases/download/v1.14.12/simplesamlphp-1.14.12.tar.gz \
    && tar xvfz downloaded-simplesamlphp.tar.gz \
    && mv "$( ls | grep simplesaml | grep -v tar.gz )" simplesamlphp \
    && rm /var/www/downloaded-simplesamlphp.tar.gz \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure PHP settings
RUN perl -pi -e 's/;cgi.fix_pathinfo=1/cgi.fix_pathinfo=0/g' /etc/php/5.6/fpm/php.ini
RUN perl -pi -e 's/allow_url_fopen = Off/allow_url_fopen = On/g' /etc/php/5.6/fpm/php.ini
RUN perl -pi -e 's/expose_php = On/expose_php = Off/g' /etc/php/5.6/fpm/php.ini

# Prepare nginx configuration
RUN mkdir /etc/nginx/certs

# Setup simplesamlphp
COPY resources/simplesamlphp/config/config.php /var/www/simplesamlphp/config
COPY resources/simplesamlphp/config/authsources.php /var/www/simplesamlphp/config
COPY resources/simplesamlphp/config/config-metarefresh.php /var/www/simplesamlphp/config
COPY resources/simplesamlphp/bin/get_idp_proxy_metadata.sh /var/www/simplesamlphp/bin
COPY resources/simplesamlphp/bin/remove_idp_proxy_metadata.sh /var/www/simplesamlphp/bin
# simplesamlphp keys
# hadolint ignore=DL3003
RUN set -x \
    && cd /var/www/simplesamlphp/cert \
    && openssl req -newkey rsa:2048 -new -x509 -nodes \
         -out auth-proxy.cer \
         -keyout auth-proxy.key \
         -subj "/C=JP/ST=Tokyo/L=Chiyoda-ku/O=NII/CN=auth-proxy"

# simplesamlphp metarefresh module
RUN set -x \
    && touch /var/www/simplesamlphp/modules/cron/enable \
    && touch /var/www/simplesamlphp/modules/metarefresh/enable \
    && mkdir -p /var/www/simplesamlphp/metadata/idp-proxy

# Change owner
RUN set -x \
    && chown -R www-data:www-data /var/www/simplesamlphp \
    && chmod a+x /var/www/simplesamlphp/bin/get_idp_proxy_metadata.sh

# supervisord
COPY resources/supervisord.conf /etc/

# Set the current working directory
WORKDIR /var/www/html

# Expose port 80
EXPOSE 80
EXPOSE 443

COPY resources/scripts/config.py /
COPY resources/scripts/start.sh /
RUN chmod +x /config.py /start.sh


RUN mkdir -p /var/www/htdocs/php /var/www/htdocs/html /var/www/bin /var/www/lib
COPY resources/htdocs/php /var/www/htdocs/php
COPY resources/html /var/www/htdocs/html
COPY resources/bin /var/www/bin
COPY resources/lib /var/www/lib
RUN chown -R www-data:www-data /var/www/htdocs /var/www/bin /var/www/lib

CMD ["/start.sh"]
