FROM harbor.vcloud.nii.ac.jp/vcp/base:1.8.1-rockylinux8.7-x86_64-rc0-rclocal

RUN dnf -y update \
  && dnf clean all \
  && rm -rf /var/cache/dnf/*

# ---------------------------------------------------------------------------
# https://hub.docker.com/r/rockylinux/rockylinux

ENV container=docker

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

RUN sed -r -i \
    -e '/multipath_component_detection/s/^(\s*multipath_component_detection)\s*=\s*[0-9]+\s*$/\1 = 0/' \
    -e '/md_component_detection/s/^(\s*md_component_detection)\s*=\s*[0-9]+\s*$/\1 = 0/' \
    -e '/udev_sync/s/^(\s*udev_sync)\s*=\s*[0-9]+\s*$/\1 = 0/' \
    -e '/udev_rules/s/^(\s*udev_rules)\s*=\s*[0-9]+\s*$/\1 = 0/' \
    /etc/lvm/lvm.conf

# ---------------------------------------------------------------------------
RUN dnf -y install \
      openssh-server \
      openssh-clients \
      iproute \
      rsync \
      unzip \
      tree \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

RUN dnf -y install \
      python3.11 \
      python3.11-pip \
 && dnf clean all \
 && rm -rf /var/cache/dnf/* \
 && alternatives --set python3 /usr/bin/python3.11

RUN /usr/local/bin/fluent-gem install fluent-plugin-systemd --no-document \
 && mkdir -p /etc/fluentd/config.d/ocs-output \
 && sed -r -i /etc/systemd/journald.conf \
      -e '/RateLimitInterval=/s/^#?RateLimitInterval=.+/RateLimitInterval=1s/' \
      -e '/RateLimitBurst=/s/^#?RateLimitBurst=.+/RateLimitBurst=10000/'

COPY etc /etc/
RUN systemctl enable docker cadvisor serf sshd fluentd user_init_command

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# ---------------------------------------------------------------------------
RUN dnf -y install \
      openssl \
      wget \
      nfs-utils \
      git \
      nmap-ncat \
      jq \
 && dnf clean all \
 && rm -rf /var/cache/dnf/* \
 && systemctl enable rpcbind

WORKDIR /
