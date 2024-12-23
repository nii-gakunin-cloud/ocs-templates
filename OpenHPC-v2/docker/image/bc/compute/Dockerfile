ARG TAG=2.9
ARG REGISTRY=harbor.vcloud.nii.ac.jp
FROM $REGISTRY/vcp/openhpc:common-$TAG

# ------------------------------------------------------------
# Add OpenHPC base components to compute image (Section 3.8.2)
# ------------------------------------------------------------
RUN dnf -y install ohpc-base-compute \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# -------------------------------------------------------
# Add OpenHPC components to compute image (Section 3.8.2)
# -------------------------------------------------------
RUN dnf -y install ohpc-slurm-client lmod-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# -----------------------------------------
# Additional customizations (Section 3.8.4)
# -----------------------------------------

# Update memlock settings
RUN perl -pi -e 's/# End of file/\* soft memlock unlimited\n$&/s' /etc/security/limits.conf \
 && perl -pi -e 's/# End of file/\* hard memlock unlimited\n$&/s' /etc/security/limits.conf

# Enable slurm pam module
#RUN echo "account    required     pam_slurm.so" >> $CHROOT/etc/pam.d/sshd

# -------------------------------------------------------
# Configure rsyslog on SMS and computes (Section 3.8.4.7)
# -------------------------------------------------------
#RUN echo "*.* @${sms_ip}:514" >> /etc/rsyslog.conf \
# && perl -pi -e "s/^\*\.info/\\#\*\.info/" /etc/rsyslog.conf \
# && perl -pi -e "s/^authpriv/\\#authpriv/" /etc/rsyslog.conf \
# && perl -pi -e "s/^mail/\\#mail/" /etc/rsyslog.conf \
# && perl -pi -e "s/^cron/\\#cron/" /etc/rsyslog.conf \
# && perl -pi -e "s/^uucp/\\#uucp/" /etc/rsyslog.conf

# Optionally, enable nhc and configure
RUN dnf -y install nhc-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# VCP customize
COPY etc /etc/

# hadolint ignore=DL3041
RUN systemctl disable NetworkManager-wait-online chronyd \
 && systemctl enable mount-nfs munge slurmd \
 && systemctl mask emergency.service \
 && systemctl mask emergency.target \
 && dnf -y install hostname squashfs-tools \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*
