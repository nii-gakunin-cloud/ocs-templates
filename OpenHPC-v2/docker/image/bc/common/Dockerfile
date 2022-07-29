FROM harbor.vcloud.nii.ac.jp/vcp/base:1.8.1-alpine3.13-x86_64 AS vcp-base

FROM rockylinux:8.5

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

# hadolint ignore=DL3041
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

RUN dnf -y module enable ruby:2.7 \
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

ARG CADVISOR_VERSION=v0.39.2
RUN curl -fsSL -o /usr/local/bin/cadvisor https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor \
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
RUN yum -y install http://repos.openhpc.community/OpenHPC/2/EL_8/x86_64/ohpc-release-2-1.el8.x86_64.rpm \
 && yum -y install dnf-plugins-core \
 && yum config-manager --set-enabled powertools \
 && yum clean all \
 && rm -rf /var/cache/dnf/*

# hadolint ignore=DL3041
RUN dnf -y install \
      glibc-locale-source \
      langpacks-en \
      langpacks-ja \
      redhat-lsb-core \
      procps-ng \
      iproute \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

RUN groupadd --system docker
