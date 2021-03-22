#!/usr/bin/env python3

import json
import os

from vcpsdk import vcpsdk

RESERVED_HOST_FILE = '/opt/vcpsdk/vcpsdk/config/hosts.json'

vcp_accesskey = os.environ['VCP_ACCESSKEY']
unit_group_name = os.environ['VC_NAME']


def main():
    sdk = vcpsdk.VcpSDK(vcc_access_token=vcp_accesskey, verbose=10)

    ugroup = sdk.get_ugroup(ugroup_name=unit_group_name)
    if ugroup is None:
        return

    allocated_nodes = ugroup.find_nodes()
    used_ips = []
    for node in allocated_nodes:
        used_ips.append(node.cloud_instance_address)
    with open(RESERVED_HOST_FILE) as f:
        reserved = json.load(f)
    for ip in used_ips:
        print(reserved[ip])


if __name__ == "__main__":
    main()
