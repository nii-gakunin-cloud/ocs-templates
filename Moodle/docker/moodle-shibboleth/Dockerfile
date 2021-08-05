ARG SHIBBOLETH_SP_VERSION=3.0.4
ARG BASE_IMAGE=harbor.vcloud.nii.ac.jp/vcp/shibboleth:sp-${SHIBBOLETH_SP_VERSION}
# hadolint ignore=DL3006
FROM $BASE_IMAGE

COPY conf.d/*.conf /etc/httpd/conf.d/
COPY conf.d/shib.conf.append /tmp/
RUN sed -i -e 's/^/#/' /etc/httpd/conf.d/welcome.conf \
 && sed -i -e '/<Location \/secure>/,/<\/Location>/s/^/#/' /etc/httpd/conf.d/shib.conf \
 && cat /tmp/shib.conf.append >> /etc/httpd/conf.d/shib.conf \
 && rm /tmp/shib.conf.append \
 && sed -i -e '/<\/VirtualHost>/s%^%Include conf.d/proxy.conf\n%' /etc/httpd/conf.d/ssl.conf
