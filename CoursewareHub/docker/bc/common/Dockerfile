FROM harbor.vcloud.nii.ac.jp/vcp/base:1.8.1-centos7-x86_64

RUN yum -y update \
  && yum clean all \
  && rm -rf /var/cache/yum/*

# ---------------------------------------------------------------------------
# https://github.com/CentOS/CentOS-Dockerfiles/tree/master/systemd/centos7/Dockerfile

ENV container docker

# hadolint ignore=DL3003,SC2086
RUN (cd /lib/systemd/system/sysinit.target.wants/ && for i in *; do [ $i = systemd-tmpfiles-setup.service ] || [ $i = systemd-udevd.service ] || [ $i = systemd-user-sessions.service ] || rm -f $i; done); \
    (cd /lib/systemd/system/multi-user.target.wants/ && for i in *; do [ $i = systemd-user-sessions.service ] || rm -f $i; done); \
    rm -f /etc/systemd/system/*.wants/*;\
    rm -f /lib/systemd/system/local-fs.target.wants/*; \
    rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
    rm -f /lib/systemd/system/basic.target.wants/*;\
    rm -f /lib/systemd/system/anaconda.target.wants/*;

VOLUME [ "/sys/fs/cgroup" ]

CMD ["/usr/sbin/init"]

# ---------------------------------------------------------------------------
RUN yum -y install \
      openssh-server \
      openssh-clients \
      make \
      iproute \
      chrony \
      rsync \
      sudo \
      unzip \
      tree \
 && yum clean all \
 && rm -rf /var/cache/yum/*

RUN yum -y install docker-compose-plugin \
 && yum clean all \
 && rm -rf /var/cache/yum/*

RUN /usr/local/bin/fluent-gem install fluent-plugin-systemd --no-document \
 && mkdir -p /etc/fluentd/config.d/ocs-output \
 && sed -r -i /etc/systemd/journald.conf \
      -e '/RateLimitInterval=/s/^#?RateLimitInterval=.+/RateLimitInterval=1s/' \
      -e '/RateLimitBurst=/s/^#?RateLimitBurst=.+/RateLimitBurst=10000/'

ARG CADVISOR_VERSION=v0.39.2
RUN curl -fsSL -o /usr/local/bin/cadvisor https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor \
 && chmod +x /usr/local/bin/cadvisor

COPY etc /etc/
RUN systemctl enable docker cadvisor serf sshd fluentd user_init_command \
 && systemctl disable chronyd

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# ---------------------------------------------------------------------------
RUN yum -y install \
      openssl \
      wget \
      nfs-utils \
      git \
      nmap-ncat \
      jq \
 && yum clean all \
 && rm -rf /var/cache/yum/* \
 && systemctl enable rpcbind

WORKDIR /
