FROM golang:1.25-bookworm AS builder
RUN go install github.com/mindprince/nvidia_gpu_prometheus_exporter@latest

FROM ohpc-compute

RUN dnf config-manager --add-repo \
      https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo \
 && dnf clean all \
 && dnf -y module install nvidia-driver:525-dkms \
 && dnf clean all \
 && rm -rf /var/cache/dnf/*

COPY etc /etc/
COPY --from=builder /go/bin/nvidia_gpu_prometheus_exporter /usr/local/bin/
RUN systemctl enable nvidia_exporter
