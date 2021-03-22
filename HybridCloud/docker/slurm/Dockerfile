FROM ubuntu:18.04
ENV VCP_CONTAINER_VERSION vcp/base:ubuntu18.04-slurm
ENV DEBIAN_FRONTEND noninteractive

# https://github.com/docker-library/docker/blob/master/19.03/dind/Dockerfile
ENV DOCKER_VERSION 19.03.1
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

#----------
RUN apt-get update -qq && apt-get install -qqy --no-install-recommends \
      apt-transport-https \
      ca-certificates \
      curl \
      software-properties-common \
      gnupg-agent \
      lxc \
      iptables && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository \
      "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) \
      stable"

# ARG DOCKER_VERSION=5:19.03.1~3-0~ubuntu
RUN apt-get update && \
    apt-get install -y --no-install-recommends docker-ce=5:19.03.1~3-0~ubuntu-bionic && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# dind
# https://github.com/docker/docker/tree/master/hack/dind
ENV DIND_COMMIT 37498f009d8bf25fbb6199e8ccd34bed84f2874b

RUN set -eux; \
  curl -fsSL -o /usr/local/bin/dind "https://raw.githubusercontent.com/docker/docker/${DIND_COMMIT}/hack/dind" \
  && chmod +x /usr/local/bin/dind

ENV DOCKER_LIB_COMMIT 252695b88bf6c0e2914ca20b1f00a2ad0a2bfef3

RUN set -eux; \
  curl -fsSL -o /usr/local/bin/docker-entrypoint.sh https://raw.githubusercontent.com/docker-library/docker/${DOCKER_LIB_COMMIT}/19.03/docker-entrypoint.sh \
  && chmod +x /usr/local/bin/docker-entrypoint.sh

RUN set -eux; \
  curl -fsSL -o /usr/local/bin/modprobe https://raw.githubusercontent.com/docker-library/docker/${DOCKER_LIB_COMMIT}/19.03/modprobe.sh \
  && chmod +x /usr/local/bin/modprobe

RUN curl -fsSL -o /usr/local/bin/dockerd-entrypoint.sh https://raw.githubusercontent.com/docker-library/docker/master/19.03/dind/dockerd-entrypoint.sh \
  && chmod +x /usr/local/bin/dockerd-entrypoint.sh

VOLUME /var/lib/docker

RUN groupadd --system dockremap \
  && useradd --system -g dockremap dockremap \
  && echo 'dockremap:165536:65536' >> /etc/subuid \
  && echo 'dockremap:165536:65536' >> /etc/subgid

# --------------------------------------------------------------------
# ansibleは2.5からpython3対応

RUN apt-get -qq update \
   && apt-get -y install --no-install-recommends \
      git \
      libffi-dev \
      openssh-server \
      supervisor \
      unzip \
      xz-utils \
   && apt-get clean \
   && rm -rf /var/lib/apt/lists/*

RUN apt-get -qq update && \
    apt-get -y install --no-install-recommends \
    python3 \
    python3-dev \
    libc6-dev \
    libssl-dev \
    python3-pip \
    python3-cffi \
    python3-setuptools \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --ignore-installed supervisor ruamel.yaml==0.15.74

ARG DOCKER_COMPOSE_VERSION=1.24.1
RUN curl -fsSL https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-Linux-x86_64 -o /usr/local/bin/docker-compose \
  && chmod +x /usr/local/bin/docker-compose

ARG CADVISOR_VERSION=v0.24.1
RUN curl -fsSL https://github.com/google/cadvisor/releases/download/${CADVISOR_VERSION}/cadvisor -o /usr/local/bin/cadvisor \
  && chmod +x /usr/local/bin/cadvisor

ARG SERF_VERSION=0.8.0
RUN curl -fsSL https://releases.hashicorp.com/serf/${SERF_VERSION}/serf_${SERF_VERSION}_linux_amd64.zip -o serf.zip \
  && unzip serf.zip -d /usr/local/bin/ \
  && rm serf.zip

RUN mkdir -p /var/run/sshd /root/.ssh \
 && ssh-keygen -A \
 && chmod 700 /root/.ssh

ARG LOCALE=en_US.UTF-8
RUN apt-get -qq update \
    && apt-get install -y --no-install-recommends \
        locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "${LOCALE} UTF-8" >> /etc/locale.gen \
    && locale-gen

ENV LC_ALL=${LOCALE}
ENV LANG=${LOCALE}
ENV LANGUAGE=${LOCALE}

COPY tokyo_ca.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

# 非対話シェルでも環境変数を設定する(root向け)
RUN echo "VCP_CONTAINER_VERSION=${VCP_CONTAINER_VERSION}" > /root/.ssh/environment
RUN echo "PermitUserEnvironment yes" >> /etc/ssh/sshd_config

RUN echo "export VCP_CONTAINER_VERSION=${VCP_CONTAINER_VERSION}" > /etc/profile.d/vcp_version.sh

# nfs
RUN apt-get -qq update && \
    apt-get -y install --no-install-recommends \
            nfs-kernel-server \
            rstatd \
            rpcbind \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV NFS_AUTOSTART=false
COPY nfs.sh /usr/local/bin/nfs.sh
RUN chmod +x /usr/local/bin/nfs.sh

# vcp/baseと合わせるためにリンク
RUN ln -s /usr/bin/docker /usr/local/bin/docker

RUN mkdir -p /etc/supervisor.d
COPY supervisord.conf /etc/supervisord.conf
COPY vcpbase.ini /etc/supervisor.d/vcpbase.ini

COPY nfs.sh /usr/local/bin/nfs.sh
RUN chmod +x /usr/local/bin/nfs.sh

# SLURM
RUN apt-get -qq update && \
    apt-get -y install --no-install-recommends \
            slurmd \
            slurm-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY slurm.conf /etc/slurm-llnl/slurm.conf
COPY munge.key /etc/munge/munge.key
RUN chmod 400 /etc/munge/munge.key
RUN mkdir -p /var/log/munge /var/run/munge && chmod 700 /var/log/munge
RUN chown munge:munge /etc/munge/munge.key /var/log/munge /var/run/munge

# TODO 鍵を入れる部分をsupervisorに持っていき、JSONスタイルで書く
# hadolint ignore=DL3025
CMD echo $AUTHORIZED_KEYS | openssl base64 -d -A > /root/.ssh/authorized_keys \
  && /usr/bin/supervisord -n -c /etc/supervisord.conf
