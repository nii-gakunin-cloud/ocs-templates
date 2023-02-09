ARG TAG
ARG REGISTRY
FROM $REGISTRY/vcp/openhpc:common-$TAG

# ------------------------------------------------------------
# Add baseline OpenHPC and provisioning services (Section 3.3)
# ------------------------------------------------------------
RUN dnf -y install ohpc-base \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# -------------------------------------------------------------
# Add resource management services on master node (Section 3.4)
# -------------------------------------------------------------
RUN dnf -y install ohpc-slurm-server \
 && dnf clean all \
 && rm -rf /var/cache/dnf/* \
 && cp /etc/slurm/slurm.conf.ohpc /etc/slurm/slurm.conf \
 && cp /etc/slurm/cgroup.conf.example /etc/slurm/cgroup.conf
#RUN perl -pi -e "s/SlurmctldHost=\S+/SlurmctldHost=${sms_name}/" /etc/slurm/slurm.conf

# -----------------------------------------
# Additional customizations (Section 3.8.4)
# -----------------------------------------

# Update memlock settings
RUN perl -pi -e 's/# End of file/\* soft memlock unlimited\n$&/s' /etc/security/limits.conf \
 && perl -pi -e 's/# End of file/\* hard memlock unlimited\n$&/s' /etc/security/limits.conf

# -------------------------------------------------------
# Configure rsyslog on SMS and computes (Section 3.8.4.7)
# -------------------------------------------------------
#RUN perl -pi -e "s/\\#\\\$ModLoad imudp/\\\$ModLoad imudp/" /etc/rsyslog.conf \
# && perl -pi -e "s/\\#\\\$UDPServerRun 514/\\\$UDPServerRun 514/" /etc/rsyslog.conf \
# && systemctl restart rsyslog

# Optionally, enable nhc and configure
RUN dnf -y install nhc-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------
# Install Development Tools (Section 4.1)
# ---------------------------------------
RUN dnf -y install \
      ohpc-autotools \
      EasyBuild-ohpc \
      hwloc-ohpc \
      spack-ohpc \
      valgrind-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# -------------------------------
# Install Compilers (Section 4.2)
# -------------------------------
RUN dnf -y install gnu12-compilers-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# --------------------------------
# Install MPI Stacks (Section 4.3)
# --------------------------------
RUN dnf -y install openmpi4-gnu12-ohpc mpich-ofi-gnu12-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------
# Install Performance Tools (Section 4.4)
# ---------------------------------------
RUN dnf -y install ohpc-gnu12-perf-tools \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------
# Setup default development environment (Section 4.5)
# ---------------------------------------
RUN dnf -y install lmod-defaults-gnu12-openmpi4-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------------------
# Install 3rd Party Libraries and Tools (Section 4.6)
# ---------------------------------------------------
RUN dnf -y install \
      ohpc-gnu12-serial-libs \
      ohpc-gnu12-io-libs \
      ohpc-gnu12-python-libs \
      ohpc-gnu12-runtimes \
      singularity-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*
RUN dnf -y install \
      ohpc-gnu12-mpich-parallel-libs \
      ohpc-gnu12-openmpi4-parallel-libs \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ------------------------------------
# Resource Manager Startup (Section 5)
# ------------------------------------
RUN systemctl enable munge \
 && systemctl enable slurmctld

# ----------------------------
#RUN dnf -y install \
#      libjpeg-turbo-devel \
#      python36-devel \
# && dnf clean all \
# && rm -rf /var/cache/dnf/*

# ----------------------------
RUN systemctl disable NetworkManager-wait-online chronyd \
 && systemctl enable nfs-server \
 && systemctl mask emergency.service \
 && systemctl mask emergency.target

COPY etc /etc/

RUN sed -i -e '1,/TaskPlugin=/s/^TaskPlugin=/#TaskPlugin=/' /etc/slurm/slurm.conf \
 && sed -i -e '1,/JobCompType=/s/^JobCompType=/#JobCompType=/' /etc/slurm/slurm.conf
