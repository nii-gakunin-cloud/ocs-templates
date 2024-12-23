FROM harbor.vcloud.nii.ac.jp/vcp/base:1.8.1-alpine3.13-x86_64-20230226 AS vcp-base

FROM rockylinux:9.3.20231119

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

RUN dnf -y install 'dnf-command(config-manager)' rocky-release-security \
 && dnf config-manager --disable security-common \
 && dnf -y --enablerepo=security-common install \
      openssh-server \
      openssh-clients \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# hadolint ignore=DL3041
RUN dnf -y install \
      iproute \
      rsync \
      sudo \
      unzip \
      tree \
      openssl \
      nfs-utils \
      xfsprogs \
      git \
      hostname \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# hadolint ignore=DL3041,DL3028
RUN dnf -y module enable ruby:3.1 \
 && dnf -y install \
      ruby \
      ruby-devel \
      gcc \
      make \
      redhat-rpm-config \
 && gem install fluentd fluent-plugin-systemd --no-document \
 && dnf -y remove gcc make \
 && dnf clean all \
 && rm -rf /var/cache/dnf/* \
 && mkdir -p /etc/fluentd/config.d/ocs-output \
 && sed -r -i /etc/systemd/journald.conf \
      -e '/RateLimitIntervalSec=/s/^#?RateLimitIntervalSec=.+/RateLimitIntervalSec=1s/' \
      -e '/RateLimitBurst=/s/^#?RateLimitBurst=.+/RateLimitBurst=10000/'

ARG CADVISOR_VERSION=v0.47.2
RUN curl -fsSL -o /usr/local/bin/cadvisor https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor-${CADVISOR_VERSION}-linux-amd64 \
 && chmod +x /usr/local/bin/cadvisor

ARG SERF_VERSION=0.8.0
RUN curl -fsSL -o serf.zip https://releases.hashicorp.com/serf/${SERF_VERSION}/serf_${SERF_VERSION}_linux_amd64.zip \
 && unzip serf.zip -d /usr/local/bin/ \
 && rm serf.zip

COPY --from=vcp-base /usr/local/share/ca-certificates/*.crt /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust extract
COPY --from=vcp-base /usr/local/bin/execute_user_init_command.sh /usr/local/bin/

COPY etc /etc/
RUN systemctl enable cadvisor serf sshd fluentd user_init_command

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
WORKDIR /

# ---------------------------------------------------------------------------
# Enable OpenHPC repository for local use
RUN dnf -y install http://repos.openhpc.community/OpenHPC/3/EL_9/x86_64/ohpc-release-3-1.el9.x86_64.rpm \
 && dnf -y install dnf-plugins-core \
 && dnf config-manager --set-enabled crb \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# hadolint ignore=DL3041
RUN dnf -y install \
      glibc-locale-source \
      langpacks-en \
      langpacks-ja \
      lsb_release \
      procps-ng \
      iproute \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

RUN groupadd --system docker
