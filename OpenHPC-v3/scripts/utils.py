from __future__ import annotations

import base64
import subprocess
from ipaddress import AddressValueError, IPv4Address, IPv4Network
from multiprocessing import Pool
from pathlib import Path
from typing import Any

import requests
from IPython.display import HTML, display

# 定数
MAX_CONCURRENT_PING_CHECKS = 10


def check_parameters(**kwargs):
    params = kwargs["_params"] if "_params" in kwargs else {}
    for name, value in kwargs.items():
        if name.startswith("_"):
            continue
        try:
            func_name = f"check_parameter_{name}"
            if func_name in globals():
                func = globals()[func_name]
                func(value, params, kwargs)
        except OhpcParameterError as ex:
            display(
                HTML(
                    f'<p>{" ".join(ex.args)}</p><a href="{ex.link}">' + "リンク先</a>に戻って再度設定を行ってください。"
                )
            )
            raise


class OhpcParameterError(RuntimeError):
    def __init__(self, message, link=None):
        super().__init__(message)
        self.link = link


def check_parameter_ugroup_name(name, params, _kwargs):
    ug = params["vcp"].get_ugroup(name)
    if ug is not None:
        msg = f"既に使用しているUnitGroup名です: {name}"
        raise OhpcParameterError(msg, "#UnitGroup名の指定")


def check_parameter_master_provider(provider, params, _kwargs):
    try:
        params["vcp"].df_flavors(provider)
    except Exception as e:
        msg = f"VCPがサポートしていないプロバイダです: {provider}"
        raise OhpcParameterError(msg, "#マスターノードのクラウドプロバイダ") from e


def check_parameter_compute_provider(provider, params, _kwargs):
    try:
        params["vcp"].df_flavors(provider)
    except Exception as e:
        msg = f"VCPがサポートしていないプロバイダです: {provider}"
        raise OhpcParameterError(msg, "#計算ノードのクラウドプロバイダ") from e


def check_parameter_ssh_public_key_path(path, _params, _kwargs):
    if not Path(path).is_file():
        msg = f"指定されたパスにファイルが存在しません: {path}"
        raise OhpcParameterError(msg, "#SSH公開鍵認証の鍵ファイルの指定")


def check_parameter_ssh_private_key_path(path, _params, kwargs):
    if not Path(path).is_file():
        msg = f"指定されたパスにファイルが存在しません: {path}"
        raise OhpcParameterError(msg, "#SSH公開鍵認証の鍵ファイルの指定")
    ret = subprocess.run(["ssh-keygen", "-y", "-f", path], capture_output=True, check=True)  # noqa: S607
    generated_public_key = ret.stdout.decode("UTF-8").split()
    with open(kwargs["ssh_public_key_path"], encoding="utf-8") as f:
        public_key = f.read().split()
    if not (generated_public_key[0] == public_key[0] and generated_public_key[1] == public_key[1]):
        msg = f"指定された秘密鍵は公開鍵とペアではありません: {path}"
        raise OhpcParameterError(msg, "#SSH公開鍵認証の鍵ファイルの指定")


def check_parameter_nfs_disk_size(value, _params, _kwargs):
    if not isinstance(value, int):
        msg = f"ディスクサイズ(GB)には整数を指定してください: {value}"
        raise OhpcParameterError(msg, "#NFS用ディスク")
    if value < 16:
        msg = f"ディスクサイズ(GB)は16GB以上の値を指定してください: {value}"
        raise OhpcParameterError(msg, "#NFS用ディスク")


def check_parameter_nfs_device(_value, _params, _kwargs):
    pass


def check_parameter_compute_nodes(value, _params, _kwargs):
    if not isinstance(value, int):
        msg = f"ノード数には整数を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードのノード数")
    if value < 1:
        msg = f"ノード数には1以上の値を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードのノード数")


def check_parameter_max_compute_nodes(value, _params, kwargs):
    if not isinstance(value, int):
        msg = f"最大ノード数には整数を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードのノード数")
    if value < kwargs["compute_nodes"]:
        msg = f"最大ノード数は計算ノード数以上の値を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードのノード数")


def check_parameter_compute_flavor(flavor, params, _kwargs):
    try:
        params["vcp"].get_spec(params["compute_provider"], flavor)
    except Exception as e:
        msg = f"定義されていないflavorが指定されました: {flavor}"
        raise OhpcParameterError(msg, "#計算ノードのflavor") from e


def check_parameter_compute_use_gpu(value, _params, _kwargs):
    if not isinstance(value, bool):
        msg = f"真偽値以外の値が指定されました: {value}"
        raise OhpcParameterError(msg, "#計算ノードにおけるGPUの利用")


def check_parameter_compute_gpus(value, _params, kwargs):
    if not kwargs["compute_use_gpu"]:
        return
    if not isinstance(value, int):
        msg = f"GPU数には整数を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードにおけるGPUの利用")
    if value < 1:
        msg = f"GPU数には1以上の値を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードにおけるGPUの利用")


def check_parameter_master_flavor(flavor, params, _kwargs):
    try:
        params["vcp"].get_spec(params["master_provider"], flavor)
    except Exception as e:
        msg = f"定義されていないflavorが指定されました: {flavor}"
        raise OhpcParameterError(msg, "#マスターノードのflavor") from e


def check_parameter_master_root_size(value, _params, _kwargs):
    if not isinstance(value, int):
        msg = f"ディスクサイズ(GB)には整数を指定してください: {value}"
        raise OhpcParameterError(msg, "#マスターノードのルートボリュームサイズ")
    if value < 20:
        msg = f"ディスクサイズ(GB)は20GB以上の値を指定してください: {value}"
        raise OhpcParameterError(msg, "#マスターノードのルートボリュームサイズ")


def _ipaddress_reachable(ipaddr):
    ret = subprocess.run(["ping", "-c", "3", ipaddr], capture_output=True, check=False)  # noqa: S607
    return (ipaddr, ret.returncode == 0)


def _check_ipv4_format(ipaddr, link):
    try:
        IPv4Address(ipaddr)
    except AddressValueError as ex:
        msg = f"正しいIPv4アドレスではありません: {ipaddr}"
        raise OhpcParameterError(msg, link) from ex


def _check_vpn_catalog(ipaddr, vcp, provider, link):
    catalog = vcp.get_vpn_catalog(provider)
    if "private_network_ipmask" not in catalog:
        return
    subnet = IPv4Network(catalog["private_network_ipmask"])
    if IPv4Address(ipaddr) not in subnet:
        msg = f"範囲外のIPアドレスが指定されています: {ipaddr}; {subnet}"
        raise OhpcParameterError(msg, link)


def check_parameter_master_ipaddress(value, params, _kwargs):
    link = "#マスターノードのIPアドレスとホスト名"
    provider = params["master_provider"]
    _check_ipv4_format(value, link)
    if provider == "onpremises":
        return
    try:
        _check_vpn_catalog(value, params["vcp"], provider, link)
    except OhpcParameterError:
        raise
    except Exception as e:
        msg = f"VCPのVPNカタログ情報の取得に失敗しました: {e!s}"
        raise OhpcParameterError(msg, link) from e
    if _ipaddress_reachable(value)[1]:
        msg = f"指定されたIPアドレスは既に他のノードで利用されています: {value}"
        raise OhpcParameterError(msg, link)


def check_parameter_master_hostname(_value, _params, _kwargs):
    pass


def check_parameter_compute_etc_hosts(value, params, _kwargs):
    link = "#計算ノードのIPアドレスとホスト名"
    if len(value) != params["max_compute_nodes"]:
        msg = f"指定されたIPアドレスは: {value!s}"
        raise OhpcParameterError(msg, link)

    provider = params["compute_provider"]
    for ipaddr in value:
        _check_ipv4_format(ipaddr, link)
        _check_vpn_catalog(ipaddr, params["vcp"], provider, link)

    if provider == "onpremises":
        return

    with Pool(MAX_CONCURRENT_PING_CHECKS) as p:
        ret = p.map(_ipaddress_reachable, value.keys())
        if any(x[1] for x in ret):
            addrs = [x[0] for x in ret if x[1]]
            msg = f"指定されたIPアドレスは既に他のノードで利用されています: {', '.join(addrs)}"
            raise OhpcParameterError(msg, "#計算ノードのIPアドレスとホスト名")


def _check_mdx_pack_num(packnum, kind, link):
    if packnum < 3:
        msg = f"パック数には3以上の値を設定してください({kind}): {packnum}"
        raise OhpcParameterError(msg, link)


def check_parameter_mdx_master_pack_num(value, _params, _kwargs):
    link = "#mdxでのVMデプロイ準備"
    _check_mdx_pack_num(value, "マスターノード", link)


def check_parameter_mdx_compute_pack_num(value, _params, _kwargs):
    link = "#mdxでのVMデプロイ準備"
    _check_mdx_pack_num(value, "計算ノード", link)


def spec_env_munge_key(gvars, vcp, token, *, verify=True):
    vault_url = f'{vcp.vcc_info()["vault_url"]}/v1/{gvars["vault_path_munge_key"]}'
    r = requests.get(vault_url, headers={"X-Vault-Token": token}, timeout=30, verify=verify)
    return r.json()["data"]["munge.key"]


def spec_add_host_list(gvars):
    add_hosts = [f'{gvars["master_hostname"]}:{gvars["master_ipaddress"]}']
    add_hosts.extend([f"{v}:{k}" for k, v in gvars["compute_etc_hosts"].items()])
    return add_hosts


def spec_env_slurm_conf(gvars):
    return ",".join([f"{k}:{v}" for k, v in gvars["slurm_conf"].items()])


def spec_env_slurm_partitions(gvars):
    return ",".join([f"{k}:{v}" for k, v in gvars["slurm_partitions"].items()])


def extract_vars_dict(keys: list[str | tuple[str, Any]], scope_vars: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for item in keys:
        if isinstance(item, tuple):
            key, default = item
            result[key] = scope_vars.get(key, default)
        else:
            result[item] = scope_vars.get(item)
    return result


def check_parameters_with_keys(
    scope_vars: dict[str, Any],
    keys: list[str | tuple[str, Any]],
    params_keys: list[str | tuple[str, Any]] | None = None,
) -> None:
    kwargs = extract_vars_dict(keys, scope_vars)
    if params_keys is not None:
        kwargs["_params"] = extract_vars_dict(params_keys, scope_vars)
    check_parameters(**kwargs)


def check_nfs_fstab_entries(entries: str) -> list[str]:
    valid_lines = []
    for line_num, line in enumerate(entries.splitlines(), start=1):
        if not line.strip() or line.strip().startswith("#"):
            continue

        if len(fields := line.split()) < 6:
            msg = f"Invalid fstab format (insufficient fields) at line {line_num}: {line}"
            raise OhpcParameterError(msg)
        if (fs_type := fields[2]) not in ("nfs", "nfs4"):
            msg = f"Not an NFS entry (fs_type={fs_type}) at line {line_num}: {line}"
            raise OhpcParameterError(msg)

        valid_lines.append(line)

    return valid_lines


def check_parameter_compute_optional_nfs_entries(entries, _params, _kwargs):
    check_nfs_fstab_entries(entries)


def encode_nfs_fstab_entries(entries: str) -> str:
    valid_lines = check_nfs_fstab_entries(entries)
    if not valid_lines:
        return ""
    combined = "\n".join(valid_lines)
    return base64.b64encode(combined.encode("utf-8")).decode("ascii")
