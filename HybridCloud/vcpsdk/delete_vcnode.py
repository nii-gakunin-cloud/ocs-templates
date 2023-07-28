#!/usr/bin/env python3
  
import json
import os
import sys

from vcpsdk import vcpsdk
from common import logsetting

from mdx import mdx_ops
from vcpsdk.plugins.mdx_ext import MdxResourceExt

def main():
    sdk = vcpsdk.VcpSDK(os.environ['VCP_ACCESSKEY'],
                        config_dir=os.environ['VCP_CONFIG_DIR'])

    unit_group_name = os.environ['VC_GROUP_NAME']
    ugroup = sdk.get_ugroup(ugroup_name=unit_group_name)

    actives = get_activated_hosts(ugroup)
    if actives is None:
        sys.stderr.write("no deletable host\n")
        return ""
    hostname, ip_address = actives

    unit_compute = ugroup.get_unit(os.environ['VC_UNIT_NAME'])
    unit_compute.delete_nodes(ip_addresses=[ip_address])

    mdx_token = os.environ.get('MDX_API_TOKEN')
    if mdx_token is not None and mdx_token.strip():
        destroy_mdx_vm(hostname)

    return hostname


def get_activated_hosts(ugroup):
    allocated_nodes = ugroup.find_nodes()
    used_ips = []
    for node in allocated_nodes:
        used_ips.append(node.cloud_instance_address)

    etc_hosts_file = f"{os.environ['VCP_CONFIG_DIR']}/hosts.json"
    with open(etc_hosts_file) as f:
        reserved = json.load(f)
    actives = [x for x in reserved.keys() if x in used_ips]
    if len(actives) > 1: # 1ノード保持
        ip = actives[-1] # 末尾を取得
        return (reserved[ip], ip)
    else:
        return None

def destroy_mdx_vm(vm_name):
    mdx_ops.use_ipv4_only()
    mdx = MdxResourceExt(os.environ['MDX_API_TOKEN'])

    mdx.set_current_project_by_name(os.environ['MDX_PROJECT_NAME'])
    mdx.power_off_vm(vm_name, wait_for=True)
    mdx.destroy_vm(vm_name, wait_for=True)


if __name__ == "__main__":
    print(f"DeleteNodeName:\t{main()}")

