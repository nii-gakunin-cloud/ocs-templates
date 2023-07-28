FROM python:3.10-slim

ENV VCPSDK_RELEASE=22.10.0

RUN apt-get -qq update ; \
    apt-get install -y curl expect patch openssh-client ; \
    apt-get clean ; \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN python3 -m pip install ruamel.yaml jsonschema requests pandas

WORKDIR /app

RUN curl https://s3-ap-northeast-1.amazonaws.com/vcp-jupyternotebook/$VCPSDK_RELEASE/jupyternotebook_vcpsdk-$VCPSDK_RELEASE.tgz \
  | tar zxf - vcpsdk/cci_schema vcpsdk/common vcpsdk/vcplib vcpsdk/vcpcli vcpsdk/vcpsdk

COPY vcp_ca.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY mdx mdx/
COPY *.py .
RUN chmod +x *.py

COPY mdx-deploy-wait_for-False.patch /tmp/
RUN cd vcpsdk ; cat /tmp/mdx-deploy-wait_for-False.patch | patch -p1

ENV PYTHONPATH=/app/vcpsdk

