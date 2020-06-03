FROM centos:7

# https://docs.docker.com/install/linux/docker-ce/centos/

RUN yum -y install \
      yum-utils \
      device-mapper-persistent-data \
      lvm2 \
  && yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo \
  && yum -y install docker-ce docker-ce-cli containerd.io \
  && yum clean all

# https://github.com/moby/moby/blob/master/project/PACKAGERS.md#runtime-dependencies
RUN yum -y install \
    procps-ng \
    e2fsprogs \
    xfsprogs \
    btrfs-progs \
    xz \
    iptables \
    libseccomp \
    which \
  && yum clean all

RUN groupadd --system dockremap \
  && useradd --system -g dockremap dockremap \
  && echo 'dockremap:165536:65536' >> /etc/subuid \
  && echo 'dockremap:165536:65536' >> /etc/subgid

# https://github.com/docker/docker/tree/master/hack/dind
ENV DIND_COMMIT 37498f009d8bf25fbb6199e8ccd34bed84f2874b
RUN curl -o /usr/local/bin/dind "https://raw.githubusercontent.com/docker/docker/${DIND_COMMIT}/hack/dind" \
  && chmod +x /usr/local/bin/dind

# https://github.com/docker-library/docker/blob/master/dockerd-entrypoint.sh
ENV DOCKER_COMMIT 27471a8b93e980bd4c51464ee933ed90fd36bf97
RUN curl -o /usr/local/bin/dockerd-entrypoint.sh "https://raw.githubusercontent.com/docker-library/docker/${DOCKER_COMMIT}/dockerd-entrypoint.sh" \
  && chmod +x /usr/local/bin/dockerd-entrypoint.sh

VOLUME /var/lib/docker
EXPOSE 2375

# ENTRYPOINT ["dockerd-entrypoint.sh"]

# ---------------------------------------------------------------------------
# https://github.com/CentOS/CentOS-Dockerfiles/tree/master/systemd/centos7/Dockerfile

ENV container docker

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || [ $i == systemd-udevd.service ] || [ $i == systemd-user-sessions.service ] || rm -f $i; done); \
    (cd /lib/systemd/system/multi-user.target.wants/; for i in *; do [ $i == systemd-user-sessions.service ] || rm -f $i; done); \
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
      openssl \
      unzip \
      tcpdump \
      traceroute \
      wget \
      sudo \
  && yum clean all

ARG FLUENTD_VERSION=0.12.43
ARG FLUENT_PLUGIN_CADVISOR_VERSION=0.3.1
RUN yum -y install \
      ruby-devel gcc gcc-c++ make \
  && echo 'gem: --no-document' >> /etc/gemrc \
  && gem install fluentd:${FLUENTD_VERSION} fluent-plugin-cadvisor:${FLUENT_PLUGIN_CADVISOR_VERSION} \
  && yum -y remove make gcc gcc-c++ ruby-devel \
  && yum -y install openssl \
  && yum clean all

ARG CADVISOR_VERSION=v0.35.0
RUN wget https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor -O /usr/local/bin/cadvisor \
  && chmod +x /usr/local/bin/cadvisor

ARG SERF_VERSION=0.8.0
RUN wget https://releases.hashicorp.com/serf/${SERF_VERSION}/serf_${SERF_VERSION}_linux_amd64.zip -O serf.zip \
  && unzip serf.zip -d /usr/local/bin/ \
  && rm serf.zip

COPY tokyo_ca.crt chiba_ca.crt /usr/share/pki/ca-trust-source/anchors/
RUN update-ca-trust extract

# ---------------------------------------------------------------------------
ARG DOCKER_COMPOSE_VERSION=1.25.5
RUN yum -y install \
      make \
      iproute \
      chrony \
      rsync \
      tree \
      cryptsetup \
  && yum clean all \
  && rm -rf /var/cache/yum/* \
  && curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
  && chmod +x /usr/local/bin/docker-compose

COPY etc /etc/
RUN systemctl enable docker cadvisor serf sshd lvm2-monitor lvm2-lvmetad chronyd

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# ---------------------------------------------------------------------------

RUN yum -y install python3-pip \
  && yum clean all \
  && pip3 install awscli azure-cli
