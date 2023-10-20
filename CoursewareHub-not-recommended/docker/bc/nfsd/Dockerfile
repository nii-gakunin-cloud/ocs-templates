ARG BASE_IMAGE=harbor.vcloud.nii.ac.jp/vcp/coursewarehub:bc-common
# hadolint ignore=DL3006
FROM $BASE_IMAGE

COPY etc /etc/
RUN systemctl enable nfs-server nfs-idmapd coursewarehub-dirs
