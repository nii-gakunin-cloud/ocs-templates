# syntax=docker/dockerfile:1
FROM cwh-common

RUN dnf -y install dnsmasq \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

COPY etc /etc/
RUN systemctl enable nfs-server nfs-idmapd coursewarehub-dirs dnsmasq
