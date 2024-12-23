ARG TAG=3.2
ARG REGISTRY=harbor.vcloud.nii.ac.jp
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
RUN dnf -y install gnu14-compilers-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# --------------------------------
# Install MPI Stacks (Section 4.3)
# --------------------------------
RUN dnf -y install openmpi5-gnu14-ohpc mpich-ofi-gnu14-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------
# Install Performance Tools (Section 4.4)
# ---------------------------------------
RUN dnf -y install ohpc-gnu14-perf-tools \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------
# Setup default development environment (Section 4.5)
# ---------------------------------------
RUN dnf -y install lmod-defaults-gnu14-openmpi5-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------------------
# Install 3rd Party Libraries and Tools (Section 4.6)
# ---------------------------------------------------
RUN dnf -y install \
      ohpc-gnu14-serial-libs \
      ohpc-gnu14-io-libs \
      ohpc-gnu14-python-libs \
      ohpc-gnu14-runtimes \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*
RUN dnf -y install \
      ohpc-gnu14-mpich-parallel-libs \
      ohpc-gnu14-openmpi5-parallel-libs \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ------------------------------------
# Resource Manager Startup (Section 5)
# ------------------------------------
RUN systemctl enable munge \
 && systemctl enable slurmctld

# ----------------------------
RUN systemctl disable NetworkManager-wait-online chronyd \
 && systemctl enable nfs-server \
 && systemctl mask emergency.service \
 && systemctl mask emergency.target

COPY etc /etc/

RUN sed -i -e '1,/TaskPlugin=/s/^TaskPlugin=/#TaskPlugin=/' /etc/slurm/slurm.conf \
 && sed -i -e '1,/JobCompType=/s/^JobCompType=/#JobCompType=/' /etc/slurm/slurm.conf

# ------------------------------------------------------------
# Apptainer
# ------------------------------------------------------------
RUN dnf -y remove singularity-ce \
 && dnf -y install apptainer \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

