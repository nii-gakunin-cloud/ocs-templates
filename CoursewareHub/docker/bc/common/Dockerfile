FROM centos:7
# https://docs.docker.com/install/linux/docker-ce/centos/

RUN yum -y install \
      yum-utils \
      device-mapper-persistent-data \
      lvm2 \
  && yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo \
  && yum -y install docker-ce docker-ce-cli containerd.io \
  && yum clean all \
  && rm -rf /var/cache/yum/*

# https://github.com/moby/moby/blob/master/project/PACKAGERS.md#runtime-dependencies
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

RUN groupadd --system dockremap \
  && useradd --system -g dockremap dockremap \
  && echo 'dockremap:165536:65536' >> /etc/subuid \
  && echo 'dockremap:165536:65536' >> /etc/subgid

# https://github.com/docker/docker/tree/master/hack/dind
ENV DIND_COMMIT 52379fa76dee07ca038624d639d9e14f4fb719ff
RUN curl -o /usr/local/bin/dind "https://raw.githubusercontent.com/docker/docker/${DIND_COMMIT}/hack/dind" \
  && chmod +x /usr/local/bin/dind

# https://github.com/docker-library/docker/blob/master/dockerd-entrypoint.sh
ENV DOCKER_COMMIT 92d278e671f32a9ee4a3c0668e46a41f4a3b74b0
RUN curl -o /usr/local/bin/docker-entrypoint.sh https://raw.githubusercontent.com/docker-library/docker/${DOCKER_COMMIT}/19.03/docker-entrypoint.sh \
  && chmod +x /usr/local/bin/docker-entrypoint.sh

VOLUME /var/lib/docker
EXPOSE 2375

# ENTRYPOINT ["/usr/local/bin/dockerd-entrypoint.sh"]

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

# 1.5
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
  && yum clean all \
  && rm -rf /var/cache/yum/*

ARG DOCKER_COMPOSE_VERSION=1.24.1
RUN curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/bin/docker-compose \
  && chmod +x /usr/bin/docker-compose

COPY etc /etc/
RUN systemctl enable docker cadvisor serf sshd rpcbind

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /
