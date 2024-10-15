FROM harbor.vcloud.nii.ac.jp/vcp/base:1.8.1-rockylinux8.7-x86_64-rc0-rclocal

RUN dnf -y update \
  && dnf clean all \
  && rm -rf /var/cache/dnf/*

# ---------------------------------------------------------------------------

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
      python3.12 \
      python3.12-pip \
 && dnf clean all \
 && rm -rf /var/cache/dnf/* \
 && alternatives --set python3 /usr/bin/python3.12

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
      cronie \
      cryptsetup \
      rsyslog \
 && dnf clean all \
 && rm -rf /var/cache/dnf/* \
 && systemctl enable rsyslog lvm2-monitor

# ---------------------------------------------------------------------------

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" \
 && unzip /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install \
 && rm -rf /tmp/aws /tmp/awscliv2.zip
