ARG BASE_IMAGE=harbor.vcloud.nii.ac.jp/vcp/coursewarehub:bc-common
# hadolint ignore=DL3006
FROM $BASE_IMAGE

RUN dnf -y install dnsmasq \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

COPY etc /etc/
RUN systemctl enable nfs-server nfs-idmapd coursewarehub-dirs dnsmasq
