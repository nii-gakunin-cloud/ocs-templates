FROM centos:7

ENV container docker

# hadolint ignore=DL3003,SC2086
RUN (cd /lib/systemd/system/sysinit.target.wants/ && for i in *; do [ $i = systemd-tmpfiles-setup.service ] || [ $i = systemd-user-sessions.service ] || rm -f $i; done); \
    (cd /lib/systemd/system/multi-user.target.wants/ && for i in *; do [ $i = systemd-user-sessions.service ] || rm -f $i; done); \
    rm -f /etc/systemd/system/*.wants/*;\
    rm -f /lib/systemd/system/local-fs.target.wants/*; \
    rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
    rm -f /lib/systemd/system/basic.target.wants/*; \
    rm -f /lib/systemd/system/anaconda.target.wants/*;

CMD ["/usr/sbin/init"]

RUN yum -y install httpd mod_ssl \
 && yum clean all \
 && systemctl enable httpd

EXPOSE 443

ARG SHIBBOLETH_VERSION
RUN curl 'https://shibboleth.net/cgi-bin/sp_repo.cgi?platform=CentOS_7' -o /etc/yum.repos.d/shibboleth.repo \
 && yum -y install shibboleth${SHIBBOLETH_VERSION} \
 && yum clean all \
 && chmod a+x /etc/shibboleth/shibd-redhat \
 && systemctl enable shibd
RUN /sbin/chkconfig network off

ARG TEMPLATE_URL=https://meatwiki.nii.ac.jp/confluence/download/attachments/12158175/
ARG ATTRIBUTE_MAP_TEMPLATE_PARAMS='version=7&modificationDate=1563426445000'
ARG ATTRIBUTE_POLICY_TEMPLATE_PARAMS='version=4&modificationDate=1563426433000'
RUN curl -L -o /etc/shibboleth/attribute-map.xml \
      "${TEMPLATE_URL}/attribute-map-template.xml?${ATTRIBUTE_MAP_TEMPLATE_PARAMS}&api=v2&download=true" \
 && curl -L -o /etc/shibboleth/attribute-policy.xml \
      "${TEMPLATE_URL}/attribute-policy-template.xml?${ATTRIBUTE_POLICY_TEMPLATE_PARAMS}&api=v2&download=true"
