FROM cwh-common

COPY etc /etc/

RUN mkdir -p /mnt/nfs /exchange /jupyter /share \
 && chmod 0777 /exchange /jupyter /share \
 && systemctl enable rpcbind
