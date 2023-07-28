#!/usr/bin/env python3

import json
import os

from vcpsdk import vcpsdk

def main():
    sdk = vcpsdk.VcpSDK(os.environ['VCP_ACCESSKEY'],
                        config_dir=os.environ['VCP_CONFIG_DIR'])

    ugroup = sdk.get_ugroup(ugroup_name=os.environ['VC_GROUP_NAME'])
    if ugroup is None:
        return

    unit_compute = ugroup.get_unit(os.environ['VC_UNIT_NAME'])
    if unit_compute is None:
        return

    allocated_nodes = unit_compute.find_nodes()
    used_ips = []
    for node in allocated_nodes:
        used_ips.append(node.cloud_instance_address)

    etc_hosts_file = f"{os.environ['VCP_CONFIG_DIR']}/hosts.json"
    with open(etc_hosts_file) as f:
        reserved = json.load(f)
    for ip in used_ips:
        print(reserved[ip])


if __name__ == "__main__":
    main()

