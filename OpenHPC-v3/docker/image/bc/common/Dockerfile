# syntax=docker/dockerfile:1
FROM rockylinux/rockylinux:9.6.20250531

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

RUN dnf -y install \
      openssh-server \
      openssh-clients \
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

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -fsSL https://toolbelt.treasuredata.com/sh/install-redhat-fluent-package5-lts.sh | sh
RUN mv /etc/fluent/fluentd.conf /etc/fluent/fluentd.conf.dist \
 && mkdir -p /etc/fluent/config.d/ocs-output \
 && sed -r -i /etc/systemd/journald.conf \
      -e '/RateLimitIntervalSec=/s/^#?RateLimitIntervalSec=.+/RateLimitIntervalSec=1s/' \
      -e '/RateLimitBurst=/s/^#?RateLimitBurst=.+/RateLimitBurst=10000/'

ARG CADVISOR_VERSION=v0.49.2
RUN curl -fsSL -o /usr/local/bin/cadvisor https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor-${CADVISOR_VERSION}-linux-amd64 \
 && chmod +x /usr/local/bin/cadvisor

ARG SERF_VERSION=0.8.0
RUN curl -fsSL -o serf.zip https://releases.hashicorp.com/serf/${SERF_VERSION}/serf_${SERF_VERSION}_linux_amd64.zip \
 && unzip serf.zip -d /usr/local/bin/ \
 && rm serf.zip

COPY --from=harbor.vcloud.nii.ac.jp/vcp/base:2.1.0-alpine3.21-x86_64 \
    /usr/local/share/ca-certificates/*.crt /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust extract
COPY --from=harbor.vcloud.nii.ac.jp/vcp/base:2.1.0-alpine3.21-x86_64 \
    /usr/local/bin/execute_user_init_command.sh /usr/local/bin/

COPY etc /etc/
RUN systemctl enable cadvisor serf sshd fluentd user_init_command \
 && chmod g-w /etc

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
# ---------------------------------------------------------------------------

RUN dnf -y install \
      python3-jinja2 \
      python3-pip \
 && dnf clean all \
 && rm -rf /var/cache/dnf/* \
 && pip install --no-cache-dir jinja2-cli
