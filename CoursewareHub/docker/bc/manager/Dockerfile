ARG BASE_IMAGE=harbor.vcloud.nii.ac.jp/vcp/coursewarehub:bc-common
# hadolint ignore=DL3006
FROM $BASE_IMAGE

# hadolint ignore=SC2039
RUN mkdir -p /mnt/nfs/home /exported/home \
 && mkdir -p /exported/exchange /exported/jupyter \
      /mnt/nfs/exchange /mnt/nfs/jupyter /exchange /jupyter \
 && chmod 0777 /exported/exchange /exported/jupyter \
      /mnt/nfs/exchange /mnt/nfs/jupyter /exchange /jupyter \
 && echo $'/mnt/nfs/home /exported/home none bind 0 0\n\
/mnt/nfs/exchange /exported/exchange none bind 0 0\n\
/mnt/nfs/jupyter /exported/jupyter none bind 0 0\n\
/mnt/nfs/home /home none bind 0 0\n\
/mnt/nfs/exchange /exchange none bind 0 0\n\
/mnt/nfs/jupyter /jupyter none bind 0 0\n\
' >> /etc/fstab \
 && systemctl enable nfs-server nfs-idmapd

COPY etc /etc/
