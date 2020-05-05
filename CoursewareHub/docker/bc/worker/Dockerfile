ARG BASE_IMAGE=harbor.vcloud.nii.ac.jp/vcp/coursewarehub:bc-common
# hadolint ignore=DL3006
FROM $BASE_IMAGE

COPY etc /etc/

RUN mkdir -p /exchange /jupyter \
 && chmod 0777 /exchange /jupyter \
 && systemctl enable rpcbind mount-nfs
