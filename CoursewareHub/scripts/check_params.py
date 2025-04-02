import re
import subprocess
from inspect import currentframe, getframeinfo
from ipaddress import AddressValueError, IPv4Address, IPv4Network
from logging import getLogger
from pathlib import Path

from IPython.display import HTML, display

logger = getLogger(__name__)


anchor_map = {
    "ugroup_name": "#UnitGroup名の指定",
    "vc_provider": "#クラウドプロバイダの指定",
    "manager_flavor": "#managerノードのflavor指定",
    "manager_disk_size": "#managerノードのルートボリュームサイズ",
    "worker_flavor": "#workerノードのflavor指定",
    "worker_disk_size": "#workerノードのルートボリュームサイズ",
    "worker_nodes": "#ノード数の指定",
    "nfs_flavor": "#NFS-serverノードのflavor指定",
    "nfs_root_disk_size": "#NFS-serverノードのルートボリュームサイズ",
    "manager_ipaddress": "#IPアドレスを指定する場合",
    "worker_ipaddresses": "#IPアドレスを指定する場合",
    "vc_ipaddress": "#IPアドレスを指定する場合",
    "nfs_ipaddress": "#IPアドレスを指定する場合",
    "vc_mac_address": "#MACアドレスを指定する場合",
    "worker_mac_addresses": "#MACアドレスを指定する場合",
    "nfs_mac_address": "#MACアドレスを指定する場合",
    "nfs_server": "#NFSサーバの指定",
    "docker_address_pool": "#アドレスプールの指定",
    "ssh_public_key_path": "#SSH公開鍵認証の鍵ファイルの指定",
    "ssh_private_key_path": "#SSH公開鍵認証の鍵ファイルの指定",
    "idp_proxy_flavor": "#flavor指定",
    "ssh_user_name": "#mdx-VM-ログインユーザ名の指定",
    "schedule_down_type": "#ノードの停止方法",
    "vcnode_all_ipaddress": "#IPアドレス",
}


def _display_html_error(ex) -> None:
    msg = f"<p>{' '.join(ex.args)}</p>"
    if hasattr(ex, "link"):
        msg += f'<a href="{ex.link}">リンク先</a>に戻って再度設定を行ってください。'
    display(HTML(msg))


def check_parameters(*targets, params=None, nb_vars=None):
    if params is None:
        params = {}
    if nb_vars is None:
        nb_vars = {}
    kwargs = dict((x, nb_vars[x]) for x in targets if x in nb_vars)
    opt_vars = params.get("opt_vars", [])
    for grp in params.get("opt_groups", []):
        opt_vars.extend(grp)
    for target in targets:
        try:
            v = nb_vars.get(target)
            func = globals().get(f"check_parameter_{target}")
            if v is None:
                if target not in opt_vars:
                    msg = f"{target}が設定されていません。"
                    raise CwhParameterError(msg, target=target)
                func = globals().get(f"opt_check_parameter_{target}")
            if func:
                func(v, params, kwargs)
        except CwhParameterError as ex:
            _display_html_error(ex)
            raise ex

    for grp in params.get("opt_groups", []):
        try:
            match = len([x for x in grp if x in nb_vars])
            if match == 0:
                raise CwhParameterError(f"{', '.join(grp)}のいずれもが設定されていません。", target=grp[0])
        except CwhParameterError as ex:
            _display_html_error(ex)
            raise ex

    for grp in params.get("opt_groups", []):
        try:
            match = len([x for x in grp if x in nb_vars])
            if match > 1:
                raise CwhParameterError(
                    f"{', '.join(grp)}のうち複数の設定が行われています。"
                    + "del()でどちらかの変数を削除してください。"
                )
        except CwhParameterError as ex:
            _display_html_error(ex)
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
            target = "_".join(fname.split("_")[2:])
            if target in anchor_map:
                self.link = anchor_map[target]


def check_parameter_ugroup_name(name, params, _kwargs):
    ug = params["vcp"].get_ugroup(name)
    if ug is not None:
        raise CwhParameterError(f"既に使用しているUnitGroup名です: {name}", frame=currentframe())
    if not re.match(r"(?a)[a-zA-Z][a-zA-Z0-9]*$", name):
        raise CwhParameterError(f"正しくないUnitGroup名です: {name}", frame=currentframe())


def check_parameter_vc_provider(provider, params, _kwargs):
    try:
        params["vcp"].df_flavors(provider)
    except Exception as exc:
        raise CwhParameterError(
            f"VCPがサポートしていないプロバイダです: {provider}", frame=currentframe()
        ) from exc


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
        params["vcp"].get_spec(kwargs["vc_provider"], flavor)
    except Exception as exc:
        raise CwhParameterError(f"未定義のflavorです: {flavor}", frame=frame) from exc


def check_parameter_manager_disk_size(disk_size, params, kwargs):
    check_parameter_vc_disk_size(disk_size, params, kwargs, currentframe())


def check_parameter_worker_disk_size(disk_size, params, kwargs):
    check_parameter_vc_disk_size(disk_size, params, kwargs, currentframe())


def check_parameter_nfs_root_disk_size(disk_size, params, kwargs):
    check_parameter_vc_disk_size(
        disk_size, params, kwargs, min_sz=-1, frame=currentframe()
    )


def check_parameter_vc_disk_size(value, _params, _kwargs, frame=None, min_sz=16):
    if not isinstance(value, int) or value <= 0:
        raise CwhParameterError(f"ディスクサイズには正の整数を指定してください:{value}", frame=frame)
    if min_sz > 0 and value < min_sz:
        raise CwhParameterError(
            f"ディスクサイズに{min_sz}(GB)以上の値を指定してください:{value}", frame=frame
        )


def check_parameter_worker_nodes(value, _params, _kwargs):
    if not isinstance(value, int) or value <= 0:
        raise CwhParameterError(f"正の整数を指定してください:{value}", frame=currentframe())


def check_parameter_ssh_public_key_path(path, _params, _kwargs):
    if not Path(path).expanduser().is_file():
        raise CwhParameterError(f"指定されたパスにファイルが存在しません: {path}", frame=currentframe())


def check_parameter_ssh_private_key_path(path, _params, kwargs):
    private_key_path = Path(path).expanduser()
    if not private_key_path.is_file():
        raise CwhParameterError(f"指定されたパスにファイルが存在しません: {path}", frame=currentframe())
    ret = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(private_key_path)],
        capture_output=True,
        check=True,
    )
    generated_public_key = ret.stdout.decode("UTF-8").split()
    public_key_path = Path(kwargs["ssh_public_key_path"]).expanduser()
    with public_key_path.open(encoding="utf-8") as f:
        public_key = f.read().split()
    if not (
        generated_public_key[0] == public_key[0]
        and generated_public_key[1] == public_key[1]
    ):
        raise CwhParameterError(f"指定された秘密鍵は公開鍵とペアではありません: {path}", frame=currentframe())


def _ipaddress_reachable(ipaddr):
    ret = subprocess.run(["ping", "-c", "3", ipaddr], capture_output=True, check=False)
    return (ipaddr, ret.returncode == 0)


def _check_ipv4_format(ipaddr, frame):
    try:
        IPv4Address(ipaddr)
    except AddressValueError as exc:
        raise CwhParameterError(f"正しいIPv4アドレスではありません: {ipaddr}", frame=frame) from exc


def _check_vpn_catalog(ipaddr, vcp, provider, frame):
    catalog = vcp.get_vpn_catalog(provider)
    if "private_network_ipmask" not in catalog:
        return
    subnet = IPv4Network(catalog["private_network_ipmask"])
    ip = IPv4Address(ipaddr)
    if ip not in subnet:
        raise CwhParameterError(f"範囲外のIPアドレスが指定されています: {ipaddr}; {subnet}", frame=frame)


def check_parameter_manager_ipaddress(value, params, kwargs):
    provider = kwargs["vc_provider"]
    _check_ipv4_format(value, currentframe())
    _check_vpn_catalog(value, params["vcp"], provider, currentframe())
    if provider != "onpremises" and _ipaddress_reachable(value)[1]:
        raise CwhParameterError(
            f"指定されたIPアドレスは他のノードで利用されています: {value}", frame=currentframe()
        )


def opt_check_parameter_manager_ipaddress(value, params, kwargs):
    provider = kwargs["vc_provider"]
    if value is None:
        if provider != "onpremises":
            return
        target = "manager_ipaddress"
        raise CwhParameterError(f"{target}が設定されていません。", target=target)
    check_parameter_manager_ipaddress(value, params, kwargs)


check_parameter_vc_ipaddress = check_parameter_manager_ipaddress


def check_parameter_worker_ipaddresses(addr_list, params, kwargs):
    if not isinstance(addr_list, list):
        raise CwhParameterError("アドレスのリストを指定してください", frame=currentframe())

    if len(addr_list) != kwargs["worker_nodes"]:
        raise CwhParameterError("workerノード数と指定されたアドレス数が一致しません", frame=currentframe())

    provider = kwargs["vc_provider"]
    for addr in addr_list:
        _check_ipv4_format(addr, currentframe())
        _check_vpn_catalog(addr, params["vcp"], provider, currentframe())
        if provider != "onpremises" and _ipaddress_reachable(addr)[1]:
            raise CwhParameterError(
                f"指定されたIPアドレスは他のノードで利用されています: {addr}", frame=currentframe()
            )


def opt_check_parameter_worker_ipaddresses(addr_list, params, kwargs):
    provider = kwargs["vc_provider"]
    if addr_list is None:
        if provider != "onpremises":
            return
        target = "worker_ipaddresses"
        raise CwhParameterError(f"{target}が設定されていません。", target=target)
    check_parameter_worker_ipaddresses(addr_list, params, kwargs)


def check_parameter_nfs_ipaddress(value, params, kwargs):
    provider = kwargs["vc_provider"]
    _check_ipv4_format(value, currentframe())
    _check_vpn_catalog(value, params["vcp"], provider, currentframe())
    if provider != "onpremises" and _ipaddress_reachable(value)[1]:
        raise CwhParameterError(
            f"指定されたIPアドレスは他のノードで利用されています: {value}", frame=currentframe()
        )


def check_parameter_docker_address_pool(value, _params, _kwargs):
    try:
        IPv4Network(value)
    except AddressValueError as exc:
        raise CwhParameterError(
            f"正しいIPv4アドレスではありません: {value}", frame=currentframe()
        ) from exc


def check_parameter_vc_mac_address(value, _params, _kwargs):
    if not re.match("[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$", value):
        raise CwhParameterError(f"正しいMACアドレスを指定してください: {value}", frame=currentframe())


def check_parameter_worker_mac_addresses(value, _params, kwargs):
    if not (isinstance(value, list) and all(isinstance(x, str) for x in value)):
        raise CwhParameterError("MACアドレスのリストを指定してください", frame=currentframe())
    for x in value:
        if not re.match("[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$", x):
            raise CwhParameterError(f"正しいMACアドレスを指定してください{x}", frame=currentframe())

    if len(value) != kwargs["worker_nodes"]:
        raise CwhParameterError("VCノード数と指定されたMACアドレス数が一致しません", frame=currentframe())


def opt_check_parameter_ssh_user_name(value, _params, kwargs):
    provider = kwargs["vc_provider"]
    if value is None and provider == "onpremises":
        target = "ssh_user_name"
        raise CwhParameterError(f"{target}が設定されていません。", target=target)


def check_parameter_schedule_down_type(value, _params, _kwargs):
    if value not in ["deleted", "power_down"]:
        msg = f"deleted または power_down を指定してください: {value}"
        raise CwhParameterError(msg, frame=currentframe())


def check_parameter_vcnode_all_ipaddress(value, params, _kwargs):
    if not isinstance(value, list):
        raise CwhParameterError("IPアドレスのリストを指定してください", frame=currentframe())
    if len(value) == 0:
        raise CwhParameterError("IPアドレスのリストが空です", frame=currentframe())

    vcp = params["vcp"]
    provider = params["vc_provider"]
    current_nodes = params.get("current_nodes", [])
    for addr in value:
        _check_ipv4_format(addr, currentframe())
        _check_vpn_catalog(addr, vcp, provider, currentframe())
        if provider == "onpremises" or addr in current_nodes:
            continue
        if _ipaddress_reachable(addr)[1]:
            msg = f"指定されたIPアドレスは他のノードで利用されています: {addr}"
            raise CwhParameterError(msg, frame=currentframe())
