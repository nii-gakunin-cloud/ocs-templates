#!/usr/bin/env python3

import json
import os
import sys
import uuid

from vcpsdk import vcpsdk

RESERVED_HOST_FILE = '/opt/vcpsdk/vcpsdk/config/hosts.json'
PUBLIC_KEY_FILE = '/tmp/key.pub'

vcp_accesskey = os.environ['VCP_ACCESSKEY']
unit_group_name = os.environ['VC_NAME']
provider_name = os.environ['PROVIDER_NAME']  # e.g. aws, aws_disk, azure, ...
flavor_name = os.environ['FLAVOR_NAME']      # e.g. small, medium, large, ...
image_name = os.environ['IMAGE_NAME']


def main():
    sdk = vcpsdk.VcpSDK(vcc_access_token=vcp_accesskey, verbose=10)

    ugroup = sdk.get_ugroup(ugroup_name=unit_group_name)
    if ugroup is None:
        ugroup = sdk.create_ugroup(unit_group_name)

    available_host = get_available_host(ugroup)
    if available_host is None:
        sys.stderr.write("no available host\n")
        return
    hostname, ip_address = available_host

    spec = sdk.get_spec(provider_name, flavor_name)
    spec.image = image_name
    spec.params_v = ['/var/lib/docker']
    spec.hostname = hostname
    spec.ip_addresses = [ip_address]
    if os.path.isfile(PUBLIC_KEY_FILE):
        spec.set_ssh_pubkey(PUBLIC_KEY_FILE)

    unit_name = str(uuid.uuid4())
    unit = ugroup.create_unit(unit_name, spec, wait_for=True)

    node = unit.find_nodes()[0]
    ip_address = node.cloud_instance_address if node.state == 'RUNNING' else ''
    print(ip_address)


def get_available_host(ugroup):
    allocated_nodes = ugroup.find_nodes()
    used_ips = []
    for node in allocated_nodes:
        used_ips.append(node.cloud_instance_address)
    with open(RESERVED_HOST_FILE) as f:
        reserved = json.load(f)
    available = reserved.keys() - used_ips
    if len(available) > 0:
        ip = available.pop()
        return (reserved[ip], ip)
    else:
        return None


if __name__ == "__main__":
    main()
