# syntax=docker/dockerfile:1
FROM rockylinux/rockylinux:9.7.20251123 AS base

RUN dnf -y update \
 && dnf -y install httpd mod_ssl which \
 && dnf clean all \
 && mv /etc/httpd/conf.d/welcome.conf /etc/httpd/conf.d/welcome.conf.dist \
 && touch /etc/httpd/conf.d/welcome.conf \
 && sed -i -e '/<\/VirtualHost>/iIncludeOptional conf.d/moodle.conf' /etc/httpd/conf.d/ssl.conf \
 && sed -i -e '/Indexes/s/Options Indexes/Options/' /etc/httpd/conf/httpd.conf

RUN curl 'https://shibboleth.net/cgi-bin/sp_repo.cgi?platform=rockylinux9' \
  -o /etc/yum.repos.d/shibboleth.repo \
 && dnf -y install shibboleth \
 && dnf clean all \
 && chmod a+x /etc/shibboleth/shibd-redhat \
 && mv /etc/httpd/conf.d/shib.conf /etc/httpd/conf.d/shib.conf.dist

RUN curl 'https://meatwiki.nii.ac.jp/confluence/download/attachments/12158175/attribute-map-template.xml?version=7&modificationDate=1563426445000&api=v2&download=true' \
      -L -o /etc/shibboleth/attribute-map.xml \
 && curl 'https://meatwiki.nii.ac.jp/confluence/download/attachments/12158175/attribute-policy-template.xml?version=4&modificationDate=1563426433000&api=v2&download=true' \
      -L -o /etc/shibboleth/policy-map.xml

RUN dnf -y install epel-release 'dnf-command(config-manager)' \
 && dnf -y install supervisor \
 && dnf clean all

COPY scripts /usr/local/bin
COPY etc /etc

FROM base AS v4

RUN mkdir -p /var/www/moodle \
 && rm -rf /var/www/html \
 && ln -s /var/www/moodle /var/www/html
COPY etc.v4/httpd/conf.d/moodle.conf /etc/httpd/conf.d/moodle.conf

EXPOSE 443
CMD ["/usr/local/bin/init"]
HEALTHCHECK CMD curl -fskI https://localhost/admin || exit 1

FROM base

RUN mkdir -p /var/www/moodle/public \
 && rm -rf /var/www/html \
 && ln -s /var/www/moodle/public /var/www/html

EXPOSE 443
CMD ["/usr/local/bin/init"]
HEALTHCHECK CMD curl -fskI https://localhost/admin || exit 1
