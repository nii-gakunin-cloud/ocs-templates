FROM jupyterhub/jupyterhub:1.0.0

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# dind
RUN apt-get update \
  && apt-get install -y --no-install-recommends make curl \
  && apt-get autoclean \
  && apt-get clean \
  && apt-get autoremove \
  && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://get.docker.com/ | sh

# Authenticator
RUN pip --no-cache-dir install git+https://github.com/cwaldbieser/jhub_remote_user_authenticator.git

# Spawner
RUN mkdir /tmp/spawner
COPY ./spawner /tmp/spawner/
# hadolint ignore=DL3003
RUN pip --no-cache-dir install git+https://github.com/jupyterhub/dockerspawner.git \
  && cd /tmp/spawner \
  && pip --no-cache-dir install .

# DB
RUN apt-get update \
    && apt-get install -y --no-install-recommends libc-dev gcc libpq-dev \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* \
    && pip --no-cache-dir install psycopg2

# cull servers
COPY cull_idle_servers.py /usr/local/bin/cull_idle_servers.py

# Resources
RUN mkdir /var/jupyterhub
COPY jupyterhub_config.py /srv/jupyterhub/
COPY get_user_id.sh /
RUN chmod +x /get_user_id.sh
RUN apt-get update \
    && apt-get install -y --no-install-recommends netcat-openbsd \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
EXPOSE 8081
