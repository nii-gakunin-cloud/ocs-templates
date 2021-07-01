FROM harbor.vcloud.nii.ac.jp/vcp/base:1.6.2-centos

RUN yum -y update \
  && yum clean all \
  && rm -rf /var/cache/yum/*

# ---------------------------------------------------------------------------
# https://github.com/CentOS/CentOS-Dockerfiles/tree/master/systemd/centos7/Dockerfile

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

# ---------------------------------------------------------------------------

RUN yum -y update \
  && yum clean all \
  && rm -rf /var/cache/yum/*

RUN yum -y install \
      openssh-server \
      openssh-clients \
      openssl \
      make \
      iproute \
      unzip \
      wget \
      sudo \
      rsync \
      tree \
      chrony \
      nfs-utils \
      git \
      nmap-ncat \
      jq \
  && yum clean all \
  && rm -rf /var/cache/yum/*

ARG CADVISOR_VERSION=v0.37.5
RUN curl -fsSL https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor -o /usr/local/bin/cadvisor \
    && chmod +x /usr/local/bin/cadvisor

COPY etc /etc/
RUN systemctl enable docker cadvisor serf sshd rpcbind chronyd

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /
