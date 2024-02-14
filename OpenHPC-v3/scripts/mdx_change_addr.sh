#!/bin/bash

set -euo pipefail

netif=ens160
newaddr=$1

dns1=`resolvectl dns ${netif} | awk '{print $4}'`
dns2=`resolvectl dns ${netif} | awk '{print $5}'`
defroute=`ip route list default | awk '{print $3}'`

echo "DNS=${dns1}" | sudo tee -a /etc/systemd/resolved.conf
if [ -n "${dns2}" ]; then
    echo "FallbackDNS=${dns2}" | sudo tee -a /etc/systemd/resolved.conf
fi
sudo systemctl restart systemd-resolved

masklen=`ip addr show dev $netif | \
    awk '/inet / {i = index($2, "/"); print(substr($2, i+1));}'`
sudo netplan set ethernets.${netif}.addresses=[${newaddr}/${masklen}]
sudo netplan set ethernets.${netif}.routes="[{to: default, via: ${defroute} }]"
sudo netplan set ethernets.ens192.dhcp-identifier=mac
sudo netplan set ethernets.ens192.dhcp4=true
sudo rm -f /etc/netplan/mdx.yaml
echo 'netplan apply' | sudo at now+1min
