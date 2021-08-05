FROM harbor.vcloud.nii.ac.jp/vcp/base:1.8.0-centos7-x86_64

RUN yum -y update \
  && yum clean all \
  && rm -rf /var/cache/yum/*

# ---------------------------------------------------------------------------
# https://github.com/CentOS/CentOS-Dockerfiles/tree/master/systemd/centos7/Dockerfile

ENV container docker

# hadolint ignore=SC2086,DL3003
RUN (cd /lib/systemd/system/sysinit.target.wants/ && for i in *; do [ $i = systemd-tmpfiles-setup.service ] || [ $i = systemd-udevd.service ] || [ $i = systemd-user-sessions.service ] || rm -f $i; done); \
    (cd /lib/systemd/system/multi-user.target.wants/ && for i in *; do [ $i = systemd-user-sessions.service ] || rm -f $i; done); \
    rm -f /etc/systemd/system/*.wants/*;\
    rm -f /lib/systemd/system/local-fs.target.wants/*; \
    rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
    rm -f /lib/systemd/system/basic.target.wants/*;\
    rm -f /lib/systemd/system/anaconda.target.wants/*;

VOLUME [ "/sys/fs/cgroup" ]

CMD ["/usr/sbin/init"]

# ---------------------------------------------------------------------------

RUN yum -y install \
      openssh-server \
      openssh-clients \
      make \
      iproute \
      chrony \
      cronie \
      rsync \
      tree \
      cryptsetup \
      rsyslog \
  && yum clean all \
  && rm -rf /var/cache/yum/*

RUN rm -f /usr/local/bin/nfs.sh \
  && ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

COPY etc /etc/
RUN systemctl enable docker cadvisor serf sshd lvm2-monitor lvm2-lvmetad \
  chronyd rsyslog

COPY entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
