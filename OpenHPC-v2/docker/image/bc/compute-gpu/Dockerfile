ARG TAG
ARG REGISTRY
FROM $REGISTRY/vcp/openhpc:compute-$TAG

# hadolint ignore=DL3041
RUN dnf config-manager --add-repo \
      https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo \
 && dnf clean all \
 && dnf -y module install nvidia-driver:455-dkms \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*
