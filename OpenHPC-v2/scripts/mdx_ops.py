from vcpsdk.plugins.mdx_ext import MdxResourceExt, SLEEP_TIME_SEC, DEPLOY_VM_SLEEP_COUNT
from multiprocessing import Pool
import subprocess
import time
import re

MDX_VM_SERVER_CATALOG = "16a41081-a1cf-428e-90d0-a147b3aa6fc2"
MDX_VM_SERVER_TEMPLATE_NAME = "UT-20220412-2043-ubuntu-2004-server"

def mdx_get_vm_spec(mdx, pack_num, use_gpu, disk_size, segment_id, shared_key,
    vm_catalog=MDX_VM_SERVER_CATALOG,
    vm_template_name=MDX_VM_SERVER_TEMPLATE_NAME,
    storage_net="portgroup"):
    return dict(
        catalog=vm_catalog,
        template_name=vm_template_name,
        pack_num=pack_num,
        pack_type="gpu" if use_gpu else "cpu",
        disk_size=disk_size,
        gpu="1" if use_gpu else "0",
        network_adapters=[
            dict(
                adapter_number=1,
                segment=segment_id
            )
        ],
        shared_key=shared_key,
        storage_network=storage_net
    )

def mdx_deploy_vms(mdx, vms, spec, project='', verbose=False):
    if len(project) > 0:
        mdx.set_current_project_by_name(project)
    for vm in vms:
        mdx.deploy_vm(vm, spec.copy(), wait_for=False)
        if verbose:
            print(f'{vm} deployed.')
    if verbose:
        print('Waiting for VMs being active.')
    vms_rest = vms.copy()
    for i in range(DEPLOY_VM_SLEEP_COUNT):
        for vm in vms_rest:
            info = mdx.get_vm_info(vm)
            if info["status"] != "PowerON":
                continue
            addr = info["service_networks"][0]["ipv4_address"][0]
            if re.match(r"^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$", addr) is None:
                continue
            vms_rest.remove(vm)
            if verbose:
                print(f"{vm} is now up with address {addr}.")
            break
        if len(vms_rest) == 0:
            break
        else:
            time.sleep(SLEEP_TIME_SEC)
    if len(vms_rest) > 0:
        raise RuntimeError(f"Error: VMs not deploed: {vms}")

def _set_init_passwd(mdx, vm, priv_key_path, passwd, user='mdxuser'):
    info = mdx.get_vm_info(vm)
    addr = info["service_networks"][0]["ipv4_address"][0]
    subprocess.run(['./scripts/init_mdx_passwd.exp', user, addr, priv_key_path, passwd],
                    check=True)

def _change_ipaddr(mdx, vm, newaddr, priv_key_path, user='mdxuser'):
    sshopts = ['-i', priv_key_path, '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']
    info = mdx.get_vm_info(vm)
    addr = info["service_networks"][0]["ipv4_address"][0]
    subprocess.run(['scp'] + sshopts + ['scripts/mdx_change_addr.sh', f'{user}@{addr}:'], check=True)
    subprocess.run(['ssh'] + sshopts + [f'{user}@{addr}', './mdx_change_addr.sh', f'{newaddr}'], check=True)

def _wait_for_addr_change(mdx, vm, newaddr, verbose=False):
    for i in range(DEPLOY_VM_SLEEP_COUNT):
        info = mdx.get_vm_info(vm)
        addr = info["service_networks"][0]["ipv4_address"][0]
        if newaddr == addr:
            if verbose:
                print(f"{vm} changed to {addr}")
            return
        time.sleep(SLEEP_TIME_SEC)
    raise RuntimeError(f'Error: {vm}: timeout during changing address.')

def mdx_set_init_passwd(mdx, vms, priv_key_path, passwd, user='mdxuser'):
    for vm in vms:
        _set_init_passwd(mdx, vm, priv_key_path, passwd, user=user)

def mdx_change_ipaddrs(mdx, etc_hosts, priv_key_path, user='mdxuser', verbose=False):
    for newaddr, vm in etc_hosts.items():
        _change_ipaddr(mdx, vm, newaddr, priv_key_path, user=user)
    for newaddr, vm in etc_hosts.items():
        _wait_for_addr_change(mdx, vm, newaddr, verbose=verbose)

class _MdxVcpInitializer(object):
    def __init__(self, priv_key_path, vcppubkey, user='mdxuser'):
        self.privkey = priv_key_path
        self.user = user
        self.vcppubkey = vcppubkey
    def __call__(self, addr):
        sshopts = ['-i', self.privkey, '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']
        subprocess.run(['scp', '-p'] + sshopts + ['scripts/init_mdx_node.sh', f'{self.user}@{addr}:'], check=True)
        subprocess.run(['ssh'] + sshopts + [f'{self.user}@{addr}', './init_mdx_node.sh'], check=True)
        subprocess.run(['ssh', '-p20022'] + sshopts + [f'{self.user}@{addr}', 'cat >> ~/.ssh/authorized_keys'],
                        input=(f'{self.vcppubkey}\n').encode('utf-8'), check=True)

def mdx_init_vcp(addrs, priv_key_path, vcp_public_key, user='mdxuser'):
    with Pool(5) as p:
        p.map(_MdxVcpInitializer(priv_key_path, vcp_public_key, user=user), addrs)
