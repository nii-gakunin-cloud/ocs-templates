from IPython.display import display, HTML
from pathlib import Path
import subprocess
from ipaddress import IPv4Address, IPv4Network, AddressValueError
from multiprocessing import Pool
import requests
import copy


def check_parameters(**kwargs):
    params = kwargs['_params'] if '_params' in kwargs else {}
    for k, v in kwargs.items():
        if (k.startswith('_')):
            continue
        try:
            eval(f'check_parameter_{k}(v, params, kwargs)')
        except OhpcParameterError as ex:
            display(HTML(
                f'<p>{" ".join(ex.args)}</p><a href="{ex.link}">' +
                'リンク先</a>に戻って再度設定を行ってください。'))
            raise ex


class OhpcParameterError(RuntimeError):
    def __init__(self, message, link=None):
        super().__init__(message)
        self.link = link


def check_parameter_ugroup_name(name, params, kwargs):
    ug = params['vcp'].get_ugroup(name)
    if ug is not None:
        raise OhpcParameterError(
            f"既に使用しているUnitGroup名です: {name}",
            '#UnitGroup名の指定')


def check_parameter_vc_provider(provider, params, kwargs):
    try:
        params['vcp'].df_flavors(provider)
    except Exception:
        raise OhpcParameterError(
            f"VCPがサポートしていないプロバイダです: {provider}",
            '#クラウドプロバイダの指定')


def check_parameter_ssh_public_key_path(path, params, kwargs):
    if not Path(path).is_file():
        raise OhpcParameterError(
            f"指定されたパスにファイルが存在しません: {path}",
            '#SSH公開鍵認証の鍵ファイルの指定')


def check_parameter_ssh_private_key_path(path, params, kwargs):
    if not Path(path).is_file():
        raise OhpcParameterError(
            f"指定されたパスにファイルが存在しません: {path}",
            '#SSH公開鍵認証の鍵ファイルの指定')
    ret = subprocess.run(
        ["ssh-keygen", "-y", "-f", path], capture_output=True, check=True)
    generated_public_key = ret.stdout.decode('UTF-8').split()
    with open(kwargs['ssh_public_key_path']) as f:
        public_key = f.read().split()
    if not (generated_public_key[0] == public_key[0] and
            generated_public_key[1] == public_key[1]):
        raise OhpcParameterError(
            f"指定された秘密鍵は公開鍵とペアではありません: {path}",
            '#SSH公開鍵認証の鍵ファイルの指定')


def check_parameter_ohpc_user_pubkey(path, params, kwargs):
    if not Path(path).is_file():
        raise OhpcParameterError(
            f"指定されたパスにファイルが存在しません: {path}",
            '#SSH公開鍵認証の鍵ファイルの指定')


def check_parameter_ohpc_user_prvkey(path, params, kwargs):
    if not Path(path).is_file():
        raise OhpcParameterError(
            f"指定されたパスにファイルが存在しません: {path}",
            '#SSH公開鍵認証の鍵ファイルの指定')
    ret = subprocess.run(
        ["ssh-keygen", "-y", "-f", path], capture_output=True, check=True)
    generated_public_key = ret.stdout.decode('UTF-8').split()
    with open(kwargs['ssh_public_key_path']) as f:
        public_key = f.read().split()
    if not (generated_public_key[0] == public_key[0] and
            generated_public_key[1] == public_key[1]):
        raise OhpcParameterError(
            f"指定された秘密鍵は公開鍵とペアではありません: {path}",
            '#SSH公開鍵認証の鍵ファイルの指定')


def check_parameter_nfs_disk_size(value, params, kwargs):
    if not isinstance(value, int):
        raise OhpcParameterError(
            f"ディスクサイズ(GB)には整数を指定してください: {value}",
            '#NFS用ディスク')
    if value < 16:
        raise OhpcParameterError(
            f"ディスクサイズ(GB)は16GB以上の値を指定してください: {value}",
            '#NFS用ディスク')


def check_parameter_nfs_device(value, params, kwargs):
    pass


def check_parameter_compute_nodes(value, params, kwargs):
    if not isinstance(value, int):
        raise OhpcParameterError(
            f"ノード数には整数を指定してください: {value}",
            '#計算ノードのノード数')
    if value < 1:
        raise OhpcParameterError(
            f"ノード数には1以上の値を指定してください: {value}",
            '#計算ノードのノード数')


def check_parameter_compute_flavor(flavor, params, kwargs):
    try:
        spec = params['vcp'].get_spec(params['vc_provider'], flavor)
    except Exception as ex:
        raise OhpcParameterError(
            f"定義されていないflavorが指定されました: {flavor}",
            '#計算ノードのflavor')


def check_parameter_master_flavor(flavor, params, kwargs):
    try:
        spec = params['vcp'].get_spec(params['vc_provider'], flavor)
    except Exception as ex:
        raise OhpcParameterError(
            f"定義されていないflavorが指定されました: {flavor}",
            '#マスターノードのflavor')


def check_parameter_master_root_size(value, params, kwargs):
    if not isinstance(value, int):
        raise OhpcParameterError(
            f"ディスクサイズ(GB)には整数を指定してください: {value}",
            '#マスターノードのルートボリュームサイズ')
    if value < 20:
        raise OhpcParameterError(
            f"ディスクサイズ(GB)は20GB以上の値を指定してください: {value}",
            '#マスターノードのルートボリュームサイズ')


def _ipaddress_reachable(ipaddr):
    ret = subprocess.run(["ping", "-c", "3", ipaddr], capture_output=True)
    return (ipaddr, ret.returncode == 0)


def _check_ipv4_format(ipaddr, link):
    try:
        ip = IPv4Address(ipaddr)
    except AddressValueError:
        raise OhpcParameterError(
            f"正しいIPv4アドレスではありません: {ipaddr}", link)


def _check_vpn_catalog(ipaddr, vcp, provider, link):
    catalog = vcp.get_vpn_catalog(provider)
    if 'private_network_ipmask' not in catalog:
        return
    subnet = IPv4Network(catalog['private_network_ipmask'])
    ip = IPv4Address(ipaddr)
    if ip not in subnet:
        raise OhpcParameterError(
            f"範囲外のIPアドレスが指定されています: {ipaddr}; {subnet}",
            link)


def check_parameter_master_ipaddress(value, params, kwargs):
    link = '#マスターノードのIPアドレスとホスト名'
    provider = params['vc_provider']
    _check_ipv4_format(value, link)
    _check_vpn_catalog(value, params['vcp'], provider, link)
    if (provider != 'onpremises' and _ipaddress_reachable(value)[1]):
        raise OhpcParameterError(
            f"指定されたIPアドレスは既に他のノードで利用されています: {value}",
            '#マスターノードのIPアドレスとホスト名')


def check_parameter_master_hostname(value, params, kwargs):
    pass


def check_parameter_c_ip_address(value, params, kwargs):
    link = '#計算ノードのIPアドレス'
    provider = params['vc_provider']
    _check_ipv4_format(value, link)
    _check_vpn_catalog(value, params['vcp'], provider, link)
    if (provider != 'onpremises' and _ipaddress_reachable(value)[1]):
        raise OhpcParameterError(
            f"指定されたIPアドレスは既に他のノードで利用されています: {value}",
            '#マスターノードのIPアドレスとホスト名')


def check_parameter_compute_etc_hosts(value, params, kwargs):
    link = '#計算ノードのIPアドレスとホスト名'
    if len(value) != params['compute_nodes']:
        raise OhpcParameterError(f"指定されたIPアドレスは: {str(value)}", link)

    provider = params['vc_provider']
    for ipaddr in value.keys():
        _check_ipv4_format(ipaddr, link)
        _check_vpn_catalog(ipaddr, params['vcp'], provider, link)

    if provider == 'onpremises':
        return

    p = Pool(10)
    ret = p.map(_ipaddress_reachable, value.keys())
    if any([x[1] for x in ret]):
        addrs = [x[0] for x in ret if x[1]]
        raise OhpcParameterError(
            '指定されたIPアドレスは既に他のノードで利用されています: ' +
            ', '.join(addrs),
            '#計算ノードのIPアドレスとホスト名')


def spec_env_munge_key(gvars, vcp, token):
    vault_url = \
        f'{vcp.vcc_info()["vault_url"]}/v1/{gvars["vault_path_munge_key"]}'
    r = requests.get(vault_url, headers={'X-Vault-Token': token})
    return r.json()['data']['munge.key']


def spec_add_host_list(gvars):
    add_hosts = [f'{gvars["master_hostname"]}:{gvars["master_ipaddress"]}']
    add_hosts.extend(
        [f'{v}:{k}' for k, v in gvars['compute_etc_hosts'].items()])
    return add_hosts


def spec_env_slurm_conf(gvars):
    return ','.join([f'{k}:{v}' for k, v in gvars["slurm_conf"].items()])
