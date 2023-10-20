#!/bin/bash

set -euo pipefail

# for 2023.08 handson
sudo sed -i '/DNS=/d' /etc/systemd/resolved.conf
echo DNS=8.8.8.8 | sudo tee -a /etc/systemd/resolved.conf
sudo systemctl restart systemd-resolved

sudo systemctl stop apt-daily.timer
sudo systemctl stop apt-daily.service
sudo systemctl stop apt-daily-upgrade.timer
sudo systemctl disable apt-daily.service
sudo systemctl disable apt-daily.timer
sudo systemctl disable apt-daily-upgrade.timer

sudo apt-get -qq update
sudo apt-get -qq install -y ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get -qq update
sudo apt-get -qq install -y docker-ce docker-ce-cli containerd.io
sudo docker version

echo 'Port 20022' | sudo tee -a /etc/ssh/sshd_config
sudo systemctl restart sshd

