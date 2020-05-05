ARG TAG
ARG REGISTRY
FROM $REGISTRY/vcp/openhpc:common-$TAG

# ------------------------------------------------------------
# Add baseline OpenHPC and provisioning services (Section 3.3)
# ------------------------------------------------------------
RUN yum -y install ohpc-base

# -------------------------------------------------------------
# Add resource management services on master node (Section 3.4)
# -------------------------------------------------------------
RUN yum -y install ohpc-slurm-server
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
RUN yum -y install nhc-ohpc

# ---------------------------------------
# Install Development Tools (Section 4.1)
# ---------------------------------------
RUN yum -y install ohpc-autotools EasyBuild-ohpc hwloc-ohpc spack-ohpc valgrind-ohpc

# -------------------------------
# Install Compilers (Section 4.2)
# -------------------------------
RUN yum -y install gnu8-compilers-ohpc

# ----------------------
# Install llvm Compilers
# ----------------------
RUN yum -y install llvm5-compilers-ohpc

# --------------------------------
# Install MPI Stacks (Section 4.3)
# --------------------------------
RUN yum -y install openmpi3-pmix-slurm-gnu8-ohpc mpich-gnu8-ohpc

# ---------------------------------------
# Install Performance Tools (Section 4.4)
# ---------------------------------------
RUN yum -y install ohpc-gnu8-perf-tools \
 && yum -y install lmod-defaults-gnu8-openmpi3-ohpc

# ---------------------------------------------------
# Install 3rd Party Libraries and Tools (Section 4.6)
# ---------------------------------------------------
RUN yum -y install ohpc-gnu8-serial-libs ohpc-gnu8-io-libs ohpc-gnu8-python-libs ohpc-gnu8-runtimes
RUN yum -y install ohpc-gnu8-mpich-parallel-libs ohpc-gnu8-openmpi3-parallel-libs

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
RUN systemctl disable ipmievd network \
 && systemctl enable nfs-server

COPY etc /etc/
