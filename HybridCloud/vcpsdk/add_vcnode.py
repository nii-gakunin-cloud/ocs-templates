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

    available_host = get_available_host(ugroup)
    if available_host is None:
        sys.stderr.write("no available host\n")
        return
    hostname, ip_address = available_host

    mdx_token = os.environ.get('MDX_API_TOKEN')
    if mdx_token is not None and mdx_token.strip():
        deploy_mdx_vm(hostname, ip_address, sdk)

    unit_compute = ugroup.get_unit(os.environ['VC_UNIT_NAME'])
    node = unit_compute.add_nodes(num_add_nodes=1, ip_addresses=[ip_address])

    if node and node[0].state == 'RUNNING':
        return hostname


def get_available_host(ugroup):
    etc_hosts_file = f"{os.environ['VCP_CONFIG_DIR']}/hosts.json"
    allocated_nodes = ugroup.find_nodes()
    used_ips = []
    for node in allocated_nodes:
        used_ips.append(node.cloud_instance_address)
    with open(etc_hosts_file) as f:
        reserved = json.load(f)
    available = [x for x in reserved.keys() if x not in used_ips]
    if len(available) > 0:
        ip = available[0]
        return (reserved[ip], ip)
    else:
        return None


def deploy_mdx_vm(vm_name, vm_ip, vcp):
    mdx_ops.use_ipv4_only()
    mdx = MdxResourceExt(os.environ['MDX_API_TOKEN'])

    ssh_public_key_path = os.environ['SSH_PUBLIC_KEY_PATH']
    with open(os.path.expanduser(ssh_public_key_path)) as f:
        shared_key = f.read()

    mdx_project_name = os.environ['MDX_PROJECT_NAME']
    mdx.set_current_project_by_name(mdx_project_name)
    mdx_segment_id = mdx.get_segments()[0]["uuid"]
    c_spec = mdx_ops.mdx_get_vm_spec(
        mdx,
        int(os.environ['MDX_PACK_NUM']),
        False, # os.environ['MDX_USE_GPU']
        int(os.environ['MDX_DISK_SIZE']),
        mdx_segment_id,
        shared_key)

    # fix: mdx REST API (2023-01-31)
    from vcpsdk.plugins.mdx_ext import MDX_VM_SPEC_SCHEMA
    if not 'service_level' in MDX_VM_SPEC_SCHEMA['properties']:
        MDX_VM_SPEC_SCHEMA['properties'].update(
            {'service_level': {'type': 'string'}}
        )
    c_spec.update({'service_level': 'guarantee'})

    ssh_private_key_path = os.environ['SSH_PRIVATE_KEY_PATH']

    mdx_ops.mdx_deploy_vms(mdx, [vm_name], c_spec, project=mdx_project_name, verbose=True)
    mdx_ops.mdx_set_init_passwd(mdx, [vm_name], ssh_private_key_path, os.environ['MDX_INIT_PASSWORD'])
    etc_hosts = {vm_ip: vm_name}
    mdx_ops.mdx_change_ipaddrs(mdx, etc_hosts, ssh_private_key_path, verbose=True)
    vcppubkey = vcp.get_publickey()
    mdx_ops.mdx_init_vcp(list(etc_hosts.keys()), ssh_private_key_path, vcppubkey)


if __name__ == "__main__":
    print(f"AddNodeName:\t{main()}")

