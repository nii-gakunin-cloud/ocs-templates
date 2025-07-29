# syntax=docker/dockerfile:1
FROM rockylinux/rockylinux:9.6.20250531

RUN dnf -y update \
 && dnf -y install httpd mod_ssl which \ 
 && dnf clean all \
 && mkdir -p /var/www/moodle \
 && rm -rf /var/www/html \
 && ln -s /var/www/moodle /var/www/html \
 && mv /etc/httpd/conf.d/welcome.conf /etc/httpd/conf.d/welcome.conf.dist \
 && touch /etc/httpd/conf.d/welcome.conf \
 && sed -i -e '/<\/VirtualHost>/iIncludeOptional conf.d/moodle.conf' /etc/httpd/conf.d/ssl.conf \
 && sed -i -e '/Indexes/s/Options Indexes/Options/' /etc/httpd/conf/httpd.conf

COPY etc /etc
COPY scripts /usr/local/bin
EXPOSE 443
CMD ["/usr/local/bin/init"]
HEALTHCHECK CMD curl -fskI https://localhost/admin || exit 1
