from IPython.display import display, HTML
from pathlib import Path
import subprocess
from ipaddress import IPv4Address, IPv4Network, AddressValueError
from multiprocessing import Pool
import requests
import copy
import re
import requests
from requests.exceptions import RequestException
from logging import getLogger
import time
from inspect import currentframe, getframeinfo
from collections import OrderedDict
import yaml

logger = getLogger(__name__)


anchor_map = {
    'ugroup_name': '#UnitGroup名の指定',
    'vc_provider': '#クラウドプロバイダの指定',
    'manager_flavor': '#managerノードのflavor指定',
    'manager_disk_size': '#managerノードのルートボリュームサイズ',
    'worker_flavor': '#workerノードのflavor指定',
    'worker_disk_size': '#workerノードのルートボリュームサイズ',
    'worker_nodes': '#ノード数の指定',
    'nfs_flavor': '#NFS-serverノードのflavor指定',
    'nfs_root_disk_size': '#NFS-serverノードのルートボリュームサイズ',
    'vc_ipaddress': '#IPアドレスを指定する場合',
    'worker_ipaddresses': '#IPアドレスを指定する場合',
    'nfs_ipaddress': '#IPアドレスを指定する場合',
    'vc_mac_address': '#MACアドレスを指定する場合',
    'worker_mac_addresses': '#MACアドレスを指定する場合',
    'nfs_mac_address': '#MACアドレスを指定する場合',
    'nfs_server': '#NFSサーバの指定',
    'docker_address_pool': '#アドレスプールの指定',
    'ssh_public_key_path': '#SSH公開鍵認証の鍵ファイルの指定',
    'ssh_private_key_path': '#SSH公開鍵認証の鍵ファイルの指定',
    'idp_proxy_flavor': '#flavor指定',
}


def check_parameters(*targets, params={}, nb_vars={}):
    kwargs = dict([(x, nb_vars[x]) for x in targets if x in nb_vars])
    opt_vars = params.get('opt_vars', [])
    for grp in params.get('opt_groups', []):
        opt_vars.extend(grp)
    for target in targets:
        try:
            if target not in nb_vars:
                if target in opt_vars:
                    continue
                raise CwhParameterError(
                        f'{target}が設定されていません。',
                        target=target)
            eval(f'check_parameter_{target}(nb_vars[target], params, kwargs)')
        except CwhParameterError as ex:
            display(HTML(
                f'<p>{" ".join(ex.args)}</p><a href="{ex.link}">' +
                'リンク先</a>に戻って再度設定を行ってください。'))
            raise ex

    for grp in params.get('opt_groups', []):
        try:
            match = len([x for x in grp if x in nb_vars])
            if match == 0:
                raise CwhParameterError(
                    f'{", ".join(grp)}のいずれもが設定されていません。',
                    target=grp[0])
        except CwhParameterError as ex:
            display(HTML(
                f'<p>{" ".join(ex.args)}</p><a href="{ex.link}">' +
                'リンク先</a>に戻って再度設定を行ってください。'))
            raise ex

    for grp in params.get('opt_groups', []):
        try:
            match = len([x for x in grp if x in nb_vars])
            if match > 1:
                raise CwhParameterError(
                    f'{", ".join(grp)}のうち複数の設定が行われています。' +
                    'del()でどちらかの変数を削除してください。')
        except CwhParameterError as ex:
            desc = f'<p>{" ".join(ex.args)}</p>'
            if hasattr(ex, 'link'):
                desc += (f'<a href="{ex.link}">' +
                         'リンク先</a>に戻って再度設定を行ってください。')
            display(HTML(desc))
            raise ex


class CwhParameterError(RuntimeError):
    def __init__(self, message, target=None, frame=None, link=None):
        super().__init__(message)
        if link is not None:
            self.link = link
        elif target is not None and target in anchor_map:
            self.link = anchor_map[target]
        elif frame is not None:
            fname = getframeinfo(frame)[2]
            target = '_'.join(fname.split('_')[2:])
            if target in anchor_map:
                self.link = anchor_map[target]


def check_parameter_ugroup_name(name, params, kwargs):
    ug = params['vcp'].get_ugroup(name)
    if ug is not None:
        raise CwhParameterError(
            f"既に使用しているUnitGroup名です: {name}",
            frame=currentframe())
    if not re.match(r'(?a)[a-zA-Z][a-zA-Z0-9]*$', name):
        raise CwhParameterError(
            f"正しくないUnitGroup名です: {name}",
            frame=currentframe())


def check_parameter_vc_provider(provider, params, kwargs):
    try:
        params['vcp'].df_flavors(provider)
    except Exception:
        raise CwhParameterError(
            f"VCPがサポートしていないプロバイダです: {provider}",
            frame=currentframe())


def check_parameter_manager_flavor(flavor, params, kwargs):
    _check_parameter_vc_flavor(flavor, params, kwargs, currentframe())


def check_parameter_worker_flavor(flavor, params, kwargs):
    _check_parameter_vc_flavor(flavor, params, kwargs, currentframe())


def check_parameter_nfs_flavor(flavor, params, kwargs):
    _check_parameter_vc_flavor(flavor, params, kwargs, currentframe())


def check_parameter_idp_proxy_flavor(flavor, params, kwargs):
    _check_parameter_vc_flavor(flavor, params, kwargs, currentframe())


def _check_parameter_vc_flavor(flavor, params, kwargs, frame):
    try:
        params['vcp'].get_spec(kwargs['vc_provider'], flavor)
    except Exception:
        raise CwhParameterError(
            f"未定義のflavorです: {flavor}", frame=frame)


def check_parameter_manager_disk_size(disk_size, params, kwargs):
    check_parameter_vc_disk_size(disk_size, params, kwargs, currentframe())


def check_parameter_worker_disk_size(disk_size, params, kwargs):
    check_parameter_vc_disk_size(disk_size, params, kwargs, currentframe())


def check_parameter_nfs_root_disk_size(disk_size, params, kwargs):
    check_parameter_vc_disk_size(
            disk_size, params, kwargs, min_sz=-1, frame=currentframe())


def check_parameter_vc_disk_size(value, params, kwargs, frame=None, min_sz=16):
    if type(value) is not int or value <= 0:
        raise CwhParameterError(
            f'ディスクサイズには正の整数を指定してください:{value}',
            frame=frame)
    if min_sz > 0 and value < min_sz:
        raise CwhParameterError(
            f'ディスクサイズに{min_sz}(GB)以上の値を指定してください:{value}',
            frame=frame)


def check_parameter_worker_nodes(value, params, kwargs):
    if type(value) is not int or value <= 0:
        raise CwhParameterError(
            f'正の整数を指定してください:{value}',
            frame=currentframe())


def check_parameter_ssh_public_key_path(path, params, kwargs):
    if not Path(path).expanduser().is_file():
        raise CwhParameterError(
            f"指定されたパスにファイルが存在しません: {path}",
            frame=currentframe())


def check_parameter_ssh_private_key_path(path, params, kwargs):
    private_key_path = Path(path).expanduser()
    if not private_key_path.is_file():
        raise CwhParameterError(
            f"指定されたパスにファイルが存在しません: {path}",
            frame=currentframe())
    ret = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(private_key_path)],
        capture_output=True, check=True)
    generated_public_key = ret.stdout.decode('UTF-8').split()
    public_key_path = Path(kwargs['ssh_public_key_path']).expanduser()
    with public_key_path.open() as f:
        public_key = f.read().split()
    if not (generated_public_key[0] == public_key[0] and
            generated_public_key[1] == public_key[1]):
        raise CwhParameterError(
            f"指定された秘密鍵は公開鍵とペアではありません: {path}",
            frame=currentframe())


def _ipaddress_reachable(ipaddr):
    ret = subprocess.run(["ping", "-c", "3", ipaddr], capture_output=True)
    return (ipaddr, ret.returncode == 0)


def _check_ipv4_format(ipaddr, frame):
    try:
        ip = IPv4Address(ipaddr)
    except AddressValueError:
        raise CwhParameterError(
            f"正しいIPv4アドレスではありません: {ipaddr}", frame=frame)


def _check_vpn_catalog(ipaddr, vcp, provider, frame):
    catalog = vcp.get_vpn_catalog(provider)
    if 'private_network_ipmask' not in catalog:
        return
    subnet = IPv4Network(catalog['private_network_ipmask'])
    ip = IPv4Address(ipaddr)
    if ip not in subnet:
        raise CwhParameterError(
            f"範囲外のIPアドレスが指定されています: {ipaddr}; {subnet}",
            frame=frame)


def check_parameter_vc_ipaddress(value, params, kwargs):
    provider = kwargs['vc_provider']
    _check_ipv4_format(value, currentframe())
    _check_vpn_catalog(value, params['vcp'], provider, currentframe())
    if (provider != 'onpremises' and _ipaddress_reachable(value)[1]):
        raise CwhParameterError(
            f"指定されたIPアドレスは他のノードで利用されています: {value}",
            frame=currentframe())


def check_parameter_worker_ipaddresses(addr_list, params, kwargs):
    if type(addr_list) is not list:
        raise CwhParameterError(
            "アドレスのリストを指定してください", frame=currentframe())

    if len(addr_list) != kwargs['worker_nodes']:
        raise CwhParameterError(
            "workerノード数と指定されたアドレス数が一致しません",
            frame=currentframe())

    provider = kwargs['vc_provider']
    for addr in addr_list:
        _check_ipv4_format(addr, currentframe())
        _check_vpn_catalog(addr, params['vcp'], provider, currentframe())
        if (provider != 'onpremises' and _ipaddress_reachable(addr)[1]):
            raise CwhParameterError(
                f"指定されたIPアドレスは他のノードで利用されています: {addr}",
                frame=currentframe())


def check_parameter_nfs_ipaddress(value, params, kwargs):
    provider = kwargs['vc_provider']
    _check_ipv4_format(value, currentframe())
    _check_vpn_catalog(value, params['vcp'], provider, currentframe())
    if (provider != 'onpremises' and _ipaddress_reachable(value)[1]):
        raise CwhParameterError(
            f"指定されたIPアドレスは他のノードで利用されています: {value}",
            frame=currentframe())


def check_parameter_docker_address_pool(value, params, kwargs):
    try:
        ip = IPv4Network(value)
    except AddressValueError:
        raise CwhParameterError(
            f"正しいIPv4アドレスではありません: {value}", frame=currentframe())


def check_parameter_vc_mac_address(value, params, kwargs):
    if not re.match('[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$', value):
        raise CwhParameterError(
            f"正しいMACアドレスを指定してください{x}",
            frame=currentframe())


def check_parameter_worker_mac_addresses(value, params, kwargs):
    if not ((type(value) is list) and all(type(x) is str for x in value)):
        raise CwhParameterError(
            "MACアドレスのリストを指定してください",
            frame=currentframe())
    for x in value:
        if not re.match('[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$', x):
            raise CwhParameterError(
                f"正しいMACアドレスを指定してください{x}",
                frame=currentframe())

    if len(value) != kwargs['worker_nodes']:
        raise CwhParameterError(
            "VCノード数と指定されたMACアドレス数が一致しません",
            frame=currentframe())


def check_parameter_nfs_server(value, params, kwargs):
    pass
