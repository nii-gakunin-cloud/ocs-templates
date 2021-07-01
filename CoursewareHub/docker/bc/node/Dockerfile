ARG BASE_IMAGE=harbor.vcloud.nii.ac.jp/vcp/coursewarehub:bc-common
# hadolint ignore=DL3006
FROM $BASE_IMAGE

COPY etc /etc/

RUN mkdir -p /mnt/nfs /exchange /jupyter /share \
 && chmod 0777 /exchange /jupyter /share \
 && systemctl enable rpcbind
