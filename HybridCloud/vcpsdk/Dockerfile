FROM python:3.8-slim-buster

ENV VCPSDK_RELEASE=20.10.0

RUN python3 -m pip install ruamel.yaml==0.15.95 jsonschema==3.2.0 requests pandas

RUN curl https://s3-ap-northeast-1.amazonaws.com/vcp-jupyternotebook/$VCPSDK_RELEASE/jupyternotebook_vcpsdk-$VCPSDK_RELEASE.tgz \
  | (cd /opt && tar zxf - ./vcpsdk/cci_schema ./vcpsdk/common ./vcpsdk/vcplib ./vcpsdk/vcpcli ./vcpsdk/vcpsdk)

COPY tokyo_ca.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY add_vcnode.py /usr/local/bin/
COPY cleanup_vc.py /usr/local/bin/
COPY get_vcnode.py /usr/local/bin/
RUN chmod +x /usr/local/bin/add_vcnode.py /usr/local/bin/cleanup_vc.py /usr/local/bin/get_vcnode.py

ENV PYTHONPATH=/opt/vcpsdk
