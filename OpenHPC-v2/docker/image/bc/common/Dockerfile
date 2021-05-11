FROM harbor.vcloud.nii.ac.jp/vcp/base:1.6.2 AS vcp-base

FROM centos:8

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
# hadolint ignore=DL3033
RUN yum -y install \
      openssh-server \
      openssh-clients \
      openssl \
      unzip \
      nfs-utils \
      xfsprogs \
      git \
      hostname \
      sudo \
      rsync \
  && yum clean all \
  && rm -rf /var/cache/dnf/*

ARG CADVISOR_VERSION=v0.37.5
RUN curl -L -o /usr/local/bin/cadvisor https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor \
  && chmod +x /usr/local/bin/cadvisor

ARG SERF_VERSION=0.8.0
RUN curl -L -o serf.zip https://releases.hashicorp.com/serf/${SERF_VERSION}/serf_${SERF_VERSION}_linux_amd64.zip \
  && unzip serf.zip -d /usr/local/bin/ \
  && rm serf.zip

COPY --from=vcp-base /usr/local/share/ca-certificates/*.crt /etc/pki/ca-trust/source/anchors/
RUN update-ca-trust extract

COPY etc /etc/
RUN systemctl enable cadvisor serf sshd

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
WORKDIR /

# Enable OpenHPC repository for local use
RUN yum -y install http://repos.openhpc.community/OpenHPC/2/CentOS_8/x86_64/ohpc-release-2-1.el8.x86_64.rpm \
 && yum -y install dnf-plugins-core \
 && yum config-manager --set-enabled powertools \
 && yum clean all \
 && rm -rf /var/cache/dnf/*

RUN dnf -y reinstall langpacks-en \
 && dnf -y install langpacks-ja \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

RUN groupadd --system docker
