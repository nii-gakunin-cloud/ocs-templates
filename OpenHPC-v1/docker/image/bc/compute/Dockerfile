ARG TAG
ARG REGISTRY
FROM $REGISTRY/vcp/openhpc:common-$TAG

# ------------------------------------------------------------
# Add OpenHPC base components to compute image (Section 3.8.2)
# ------------------------------------------------------------
RUN yum -y install ohpc-base-compute

# -------------------------------------------------------
# Add OpenHPC components to compute image (Section 3.8.2)
# -------------------------------------------------------
RUN yum -y install ohpc-slurm-client lmod-ohpc

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
RUN yum -y install nhc-ohpc

# VCP customize
COPY etc /etc/
RUN systemctl enable mount-nfs slurmd \
 && yum -y install hostname squashfs-tools
