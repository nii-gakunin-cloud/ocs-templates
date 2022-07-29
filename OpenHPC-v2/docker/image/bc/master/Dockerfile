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
 && cp /etc/slurm/slurm.conf.ohpc /etc/slurm/slurm.conf
#RUN perl -pi -e "s/ControlMachine=\S+/ControlMachine=${sms_name}/" /etc/slurm/slurm.conf

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
RUN dnf -y install gnu9-compilers-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# --------------------------------
# Install MPI Stacks (Section 4.3)
# --------------------------------
RUN dnf -y install openmpi4-gnu9-ohpc mpich-ofi-gnu9-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------
# Install Performance Tools (Section 4.4)
# ---------------------------------------
RUN dnf -y install ohpc-gnu9-perf-tools \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------
# Setup default development environment (Section 4.5)
# ---------------------------------------
RUN dnf -y install lmod-defaults-gnu9-openmpi4-ohpc \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ---------------------------------------------------
# Install 3rd Party Libraries and Tools (Section 4.6)
# ---------------------------------------------------
RUN dnf -y install \
      ohpc-gnu9-serial-libs \
      ohpc-gnu9-io-libs \
      ohpc-gnu9-python-libs \
      ohpc-gnu9-runtimes \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*
RUN dnf -y install \
      ohpc-gnu9-mpich-parallel-libs \
      ohpc-gnu9-openmpi4-parallel-libs \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# -----------------------------------------------------------------------------------
# Install Optional Development Tools for use with Intel Parallel Studio (Section 4.7)
# -----------------------------------------------------------------------------------
#RUN yum -y install intel-compilers-devel-ohpc intel-mpi-devel-ohpc
#RUN yum -y install mvapich2-psm2-intel-ohpc
#RUN yum -y install ohpc-intel-serial-libs ohpc-intel-geopm ohpc-intel-io-libs ohpc-intel-perf-tools ohpc-intel-python-libs ohpc-intel-runtimes ohpc-intel-mpich-parallel-libs ohpc-intel-mvapich2-parallel-libs ohpc-intel-openmpi3-parallel-libs ohpc-intel-impi-parallel-libs

# ------------------------------------
# Resource Manager Startup (Section 5)
# ------------------------------------
RUN systemctl enable munge \
 && systemctl enable slurmctld

# ----------------------------
RUN dnf -y install \
      libjpeg-turbo-devel \
      python36-devel \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

# ----------------------------
RUN systemctl disable NetworkManager-wait-online chronyd \
 && systemctl enable nfs-server \
 && systemctl mask emergency.service \
 && systemctl mask emergency.target

COPY etc /etc/
