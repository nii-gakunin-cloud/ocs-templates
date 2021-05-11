FROM centos:7.7.1908

RUN yum -y install \
      yum-utils \
      device-mapper-persistent-data \
      lvm2 \
  && yum clean all \
  && rm -rf /var/cache/yum/*

RUN yum -y install \
    procps-ng \
    e2fsprogs \
    xfsprogs \
    xz \
    iptables \
    libseccomp \
    which \
  && yum clean all \
  && rm -rf /var/cache/yum/*

# ---------------------
ENV container docker

# hadolint ignore=DL3003,SC2086,SC2164
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i = systemd-tmpfiles-setup.service ] || [ $i = systemd-udevd.service ] || [ $i = systemd-user-sessions.service ] || rm -f $i; done); \
    (cd /lib/systemd/system/multi-user.target.wants/; for i in *; do [ $i = systemd-user-sessions.service ] || rm -f $i; done); \
    rm -f /etc/systemd/system/*.wants/*;\
    rm -f /lib/systemd/system/local-fs.target.wants/*; \
    rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
    rm -f /lib/systemd/system/basic.target.wants/*;\
    rm -f /lib/systemd/system/anaconda.target.wants/*;

VOLUME [ "/sys/fs/cgroup" ]

CMD ["/usr/sbin/init"]

# ---------------------
RUN yum -y install \
      openssh-server \
      openssh-clients \
      openssl \
      unzip \
      tcpdump \
      traceroute \
      wget \
      sudo \
  && yum clean all \
  && rm -rf /var/cache/yum/*

ARG FLUENTD_VERSION=0.12.33
ARG FLUENT_PLUGIN_CADVISOR_VERSION=0.3.1
RUN yum -y install \
      ruby-devel gcc gcc-c++ make \
  && echo 'gem: --no-document' >> /etc/gemrc \
  && gem install fluentd:${FLUENTD_VERSION} fluent-plugin-cadvisor:${FLUENT_PLUGIN_CADVISOR_VERSION} \
  && yum -y remove make gcc gcc-c++ ruby-devel \
  && yum -y install openssl \
  && yum clean all \
  && rm -rf /var/cache/yum/*

ARG CADVISOR_VERSION=v0.33.0
RUN curl -L -o /usr/local/bin/cadvisor https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor \
  && chmod +x /usr/local/bin/cadvisor

ARG SERF_VERSION=0.8.0
RUN curl -L -o serf.zip https://releases.hashicorp.com/serf/${SERF_VERSION}/serf_${SERF_VERSION}_linux_amd64.zip \
  && unzip serf.zip -d /usr/local/bin/ \
  && rm serf.zip

# vcp 1.5
COPY cert/*.crt /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust extract

RUN yum -y install \
      nvme-cli \
  && yum clean all \
  && rm -rf /var/cache/yum/*

RUN yum -y install \
      make \
      iproute \
      rsync \
      nfs-utils \
      git \
      hostname \
  && yum clean all \
  && yum -y autoremove \
  && rm -rf /var/cache/yum/*

COPY etc /etc/
RUN systemctl enable cadvisor serf sshd rpcbind

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /

RUN sed -i -e '/tsflags/s/^tsflags/#tsflags/' /etc/yum.conf

# Enable OpenHPC repository for local use
RUN yum -y install http://build.openhpc.community/OpenHPC:/1.3/CentOS_7/x86_64/ohpc-release-1.3-1.el7.x86_64.rpm
