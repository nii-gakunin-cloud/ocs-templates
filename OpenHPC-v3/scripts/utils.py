# ruff: noqa: RUF001, RUF002, RUF003, ARG001, PLR2004

from __future__ import annotations

import base64
import re
import subprocess
from ipaddress import AddressValueError, IPv4Address, IPv4Network
from pathlib import Path
from typing import Any

import requests
from IPython.display import HTML, display

# 定数
MAX_CONCURRENT_PING_CHECKS = 10
ABSOLUTE_MAX_PARTITION_IPS = 256  # パーティションごとのIPアドレス上限


# ============================================================================
# Core Parameter Checking Infrastructure
# ============================================================================


class OhpcParameterError(RuntimeError):
    def __init__(self, message, link=None):
        super().__init__(message)
        self.link = link


def _check_parameters(params: dict[str, Any], **kwargs) -> None:
    for name, value in kwargs.items():
        if name.startswith("_"):
            continue
        func_name_optional = f"check_parameter_{name}_optional"
        func_name_required = f"check_parameter_{name}"

        # 統合パラメータ辞書を構築: params + 現在の項目を除く全kwargs
        unified_params = dict(params)
        unified_params.update({k: v for k, v in kwargs.items() if k != name})

        if func_name_optional in globals():
            if value is None:
                continue
            func = globals()[func_name_optional]
            func(value, unified_params)
        elif func_name_required in globals():
            if value is None:
                msg = f"{name}が設定されていません。"
                raise OhpcParameterError(msg)
            func = globals()[func_name_required]
            func(value, unified_params)


def check_parameters(**kwargs):
    """パラメータを検証し、エラー時にHTML付きメッセージを表示して例外を送出する。"""
    params = kwargs["_params"] if "_params" in kwargs else {}
    try:
        _check_parameters(params, **kwargs)
    except OhpcParameterError as ex:
        href = ex.link
        link_txt = (
            f"<a href='{href}'>リンク先</a>に戻って再度設定を行ってください。"
            if "_link" not in kwargs or (href := kwargs.get("_link")) is not None
            else ""
        )
        display(HTML(f"<p>{' '.join(ex.args)}</p>{link_txt}"))
        raise


def extract_vars_dict(keys: list[str | tuple[str, Any]], scope_vars: dict[str, Any]) -> dict[str, Any]:
    """keys で指定した変数名（またはデフォルト値付きタプル）を scope_vars から抽出して辞書で返す。"""
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
    *,
    link: str | bool = True,
) -> None:
    """scope_vars から keys を抽出し check_parameters で検証する。"""
    kwargs = extract_vars_dict(keys, scope_vars)
    if params_keys is not None:
        kwargs["_params"] = extract_vars_dict(params_keys, scope_vars)
    if isinstance(link, str):
        kwargs["_link"] = link
    elif link is False:
        kwargs["_link"] = None
    check_parameters(**kwargs)


# ============================================================================
# Helper Functions
# ============================================================================


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


def _ipaddress_reachable(ipaddr):
    ret = subprocess.run(["ping", "-c", "3", ipaddr], capture_output=True, check=False)  # noqa: S607
    return (ipaddr, ret.returncode == 0)


def _validate_label(label: str) -> bool:
    return re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$", label) is not None


def _validate_domain_name(domain: str) -> bool:
    if len(domain) > 253:
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    return all(_validate_label(label) for label in labels)


def _validate_hostname(hostname: str, *, fqdn: bool = True) -> bool:
    if len(hostname) > 255:
        return False
    hostname = hostname.removesuffix(".")
    labels = hostname.split(".")
    if not fqdn and len(labels) == 1:
        return _validate_label(hostname)
    return all(_validate_label(label) for label in labels)


# ============================================================================
# UnitGroup Validation
# ============================================================================


def check_parameter_ugroup_name(name: str, params: dict[str, Any]) -> None:
    ug = params["vcp"].get_ugroup(name)
    if ug is not None:
        msg = f"既に使用しているUnitGroup名です: {name}"
        raise OhpcParameterError(msg, "#UnitGroup名の指定")


# ============================================================================
# SSH Key Validation
# ============================================================================


def check_parameter_ssh_public_key_path(path: str, params: dict[str, Any]) -> None:
    if not Path(path).is_file():
        msg = f"指定されたパスにファイルが存在しません: {path}"
        raise OhpcParameterError(msg, "#SSH公開鍵認証の鍵ファイルの指定")


def check_parameter_ssh_private_key_path(path: str, params: dict[str, Any]) -> None:
    if not Path(path).is_file():
        msg = f"指定されたパスにファイルが存在しません: {path}"
        raise OhpcParameterError(msg, "#SSH公開鍵認証の鍵ファイルの指定")
    ret = subprocess.run(["ssh-keygen", "-y", "-f", path], capture_output=True, check=True)  # noqa: S607
    generated_public_key = ret.stdout.decode("UTF-8").split()
    with open(params["ssh_public_key_path"], encoding="utf-8") as f:
        public_key = f.read().split()
    if not (generated_public_key[0] == public_key[0] and generated_public_key[1] == public_key[1]):
        msg = f"指定された秘密鍵は公開鍵とペアではありません: {path}"
        raise OhpcParameterError(msg, "#SSH公開鍵認証の鍵ファイルの指定")


# ============================================================================
# Provider Validation
# ============================================================================


def check_parameter_master_provider(provider: str, params: dict[str, Any]) -> None:
    try:
        params["vcp"].df_flavors(provider)
    except Exception as e:
        msg = f"VCPがサポートしていないプロバイダです: {provider}"
        raise OhpcParameterError(msg, "#マスターノードのクラウドプロバイダ") from e


def check_parameter_compute_provider(provider: str, params: dict[str, Any]) -> None:
    try:
        params["vcp"].df_flavors(provider)
    except Exception as e:
        msg = f"VCPがサポートしていないプロバイダです: {provider}"
        raise OhpcParameterError(msg, "#計算ノードのクラウドプロバイダ") from e


# ============================================================================
# Master Node Validation
# ============================================================================


def check_parameter_master_flavor(flavor: str, params: dict[str, Any]) -> None:
    try:
        params["vcp"].get_spec(params["master_provider"], flavor)
    except Exception as e:
        msg = f"定義されていないflavorが指定されました: {flavor}"
        raise OhpcParameterError(msg, "#マスターノードのflavor") from e


def check_parameter_master_root_size(value: Any, params: dict[str, Any]) -> None:
    if not isinstance(value, int):
        msg = f"ディスクサイズ(GB)には整数を指定してください: {value}"
        raise OhpcParameterError(msg, "#マスターノードのルートボリュームサイズ")
    if value < 20:
        msg = f"ディスクサイズ(GB)は20GB以上の値を指定してください: {value}"
        raise OhpcParameterError(msg, "#マスターノードのルートボリュームサイズ")


def check_parameter_master_ipaddress(value: str, params: dict[str, Any]) -> None:
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


def check_parameter_master_hostname(value: str, params: dict[str, Any]) -> None:
    if not _validate_hostname(value, fqdn=False):
        msg = f"ホスト名の形式が不正です: {value}"
        raise OhpcParameterError(msg, "#マスターノードのIPアドレスとホスト名")


# ============================================================================
# Compute Node Validation
# ============================================================================


def check_parameter_compute_nodes(value: Any, _params: dict[str, Any]) -> None:
    if not isinstance(value, int):
        msg = f"ノード数には整数を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードのノード数")
    if value < 1:
        msg = f"ノード数には1以上の値を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードのノード数")


def check_parameter_compute_flavor(flavor: str, params: dict[str, Any]) -> None:
    try:
        params["vcp"].get_spec(params["compute_provider"], flavor)
    except Exception as e:
        msg = f"定義されていないflavorが指定されました: {flavor}"
        raise OhpcParameterError(msg, "#計算ノードのflavor") from e


def check_parameter_compute_use_gpu(value: Any, _params: dict[str, Any]) -> None:
    if not isinstance(value, bool):
        msg = f"真偽値以外の値が指定されました: {value}"
        raise OhpcParameterError(msg, "#計算ノードにおけるGPUの利用")


def check_parameter_compute_gpus_optional(value: Any, _params: dict[str, Any]) -> None:
    if not isinstance(value, int):
        msg = f"GPU数には整数を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードにおけるGPUの利用")
    if value < 1:
        msg = f"GPU数には1以上の値を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードにおけるGPUの利用")


def _check_compute_ipaddress(ip_addr: IPv4Address, subnet: IPv4Network | None, master_ip: IPv4Address) -> None:
    if subnet is not None and ip_addr not in subnet:
        msg = f"範囲外のIPアドレスが指定されています: {ip_addr}; {subnet}"
        raise OhpcParameterError(msg, "#計算ノードのIPアドレス")
    if ip_addr == master_ip:
        msg = f"マスターノードのIPアドレスと重複しています: {ip_addr}"
        raise OhpcParameterError(msg, "#計算ノードのIPアドレス")


def _check_compute_ip_ranges(value: list[str], params: dict[str, Any], vcp: Any, compute_provider: str) -> list[str]:
    ip_addrs = list({IPv4Address(ip_addr) for ip_range in value for ip_addr in parse_ip_range(ip_range)})
    if len(ip_addrs) < params["compute_nodes"]:
        msg = f"指定されたIPアドレスの数が計算ノード数に足りません: {len(ip_addrs)} < {params['compute_nodes']}"
        raise OhpcParameterError(msg, "#計算ノードのIPアドレス")

    if len(ip_addrs) > ABSOLUTE_MAX_PARTITION_IPS:
        msg = (
            f"指定されたIPアドレスの数が多すぎます"
            f"（パーティションごとの上限: {ABSOLUTE_MAX_PARTITION_IPS}）: {len(ip_addrs)}"
        )
        raise OhpcParameterError(msg, "#計算ノードのIPアドレス")

    master_ip = IPv4Address(params["master_ipaddress"])
    catalog = vcp.get_vpn_catalog(compute_provider)
    subnet = IPv4Network(catalog["private_network_ipmask"]) if compute_provider != "onpremises" else None
    for ip_addr in ip_addrs:
        _check_compute_ipaddress(ip_addr, subnet, master_ip)

    return [str(ip_addr) for ip_addr in ip_addrs]


def check_parameter_compute_ip_ranges(value: list[str], params: dict[str, Any]) -> None:
    try:
        compute_provider = params["compute_provider"]
        vcp = params["vcp"]
        ip_addrs = _check_compute_ip_ranges(value, params, vcp, compute_provider)
    except KeyError as e:
        msg = f"パラメータの取得に失敗しました: {e!s}"
        raise OhpcParameterError(msg, "#計算ノードのIPアドレス") from e
    except AddressValueError as e:
        msg = f"IPアドレスの形式が不正です: {e!s}"
        raise OhpcParameterError(msg, "#計算ノードのIPアドレス") from e

    # 重複チェック
    if "gvars" in params and "slurm_features" in (gvars := params["gvars"]):
        existing_ips = {
            addr
            for feature in gvars["slurm_features"].values()
            for addr in feature["ip_addresses"]
            if "ip_addresses" in feature
        }
        if set(ip_addrs) & existing_ips:
            msg = f"指定されたIPアドレスの一部は既に他のFeatureで使用されています: {set(ip_addrs) & existing_ips}"
            raise OhpcParameterError(msg, "#計算ノードのIPアドレス")


def check_parameter_compute_hostname_template(value: Any, params: dict[str, Any]) -> None:
    if not isinstance(value, str):
        msg = f"ホスト名テンプレートには文字列を指定してください: {value}"
        raise OhpcParameterError(msg, "#計算ノードのホスト名テンプレート")

    # プレースホルダーが1つのみであることを確認
    try:
        # テスト実行
        for i in range(1, 10):
            hostname = value.format(i)
            if not _validate_hostname(hostname, fqdn=False):
                msg = f"ホスト名テンプレートの形式が不正です: {hostname}"
                raise OhpcParameterError(msg, "#計算ノードのホスト名テンプレート")
    except (KeyError, IndexError, ValueError) as e:
        msg = f"ホスト名テンプレートのフォーマット書式が不正です: {e!s}"
        raise OhpcParameterError(msg, "#計算ノードのホスト名テンプレート") from e

    # 重複チェック
    if "gvars" in params and "slurm_features" in (gvars := params["gvars"]):
        hostnames = {value.format(i) for i in [1, 10, 100]}
        templates = [
            feature["hostname_template"]
            for feature in gvars["slurm_features"].values()
            if "hostname_template" in feature
        ]
        for template in templates:
            if hostnames & {template.format(i) for i in [1, 10, 100]}:
                msg = f"既に使用されているホスト名テンプレートです: {template}"
                raise OhpcParameterError(msg, "#計算ノードのホスト名テンプレート")


# ============================================================================
# NFS Validation
# ============================================================================


def check_parameter_nfs_disk_size(value: Any, _params: dict[str, Any]) -> None:
    if not isinstance(value, int):
        msg = f"ディスクサイズ(GB)には整数を指定してください: {value}"
        raise OhpcParameterError(msg, "#NFS用ディスク")
    if value < 16:
        msg = f"ディスクサイズ(GB)は16GB以上の値を指定してください: {value}"
        raise OhpcParameterError(msg, "#NFS用ディスク")


def check_parameter_nfs_device(_value: Any, _params: dict[str, Any]) -> None:
    pass


def check_nfs_fstab_entries(entries: str) -> list[str]:
    """fstab形式のNFSエントリを検証し、有効な行のリストを返す。"""
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


def check_parameter_compute_optional_nfs_entries_optional(entries: str, _params: dict[str, Any]) -> None:
    check_nfs_fstab_entries(entries)


def encode_nfs_fstab_entries(entries: str) -> str:
    """fstab形式のNFSエントリを検証し、Base64エンコードした文字列を返す。"""
    valid_lines = check_nfs_fstab_entries(entries)
    if not valid_lines:
        return ""
    combined = "\n".join(valid_lines)
    return base64.b64encode(combined.encode("utf-8")).decode("ascii")


# ============================================================================
# MDX Validation
# ============================================================================


def _check_mdx_pack_num(packnum, kind, link):
    if packnum < 3:
        msg = f"パック数には3以上の値を設定してください({kind}): {packnum}"
        raise OhpcParameterError(msg, link)


def check_parameter_mdx_master_pack_num(value: int, _params: dict[str, Any]) -> None:
    link = "#mdxでのVMデプロイ準備"
    _check_mdx_pack_num(value, "マスターノード", link)


def check_parameter_mdx_compute_pack_num(value: int, _params: dict[str, Any]) -> None:
    link = "#mdxでのVMデプロイ準備"
    _check_mdx_pack_num(value, "計算ノード", link)


# ============================================================================
# Feature/Partition Validation
# ============================================================================


def check_parameter_feature_name(value: str, params: dict[str, Any]) -> None:
    link = "#Feature名の指定"
    if not isinstance(value, str):
        msg = f"feature_nameには文字列を指定してください: {type(value).__name__}"
        raise OhpcParameterError(msg, link)

    if not value:
        msg = "feature_nameには空文字列以外を指定してください"
        raise OhpcParameterError(msg, link)

    # 命名規則チェック（英数字とハイフン、1-64文字）
    if not re.match(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$", value):
        msg = f"feature_nameの命名規則が不正です（英小文字・数字・ハイフン、1-64文字）: {value}"
        raise OhpcParameterError(msg, link)

    if value == "master":
        msg = "feature_nameに「master」は使用できません"
        raise OhpcParameterError(msg, link)

    # 重複チェック
    if "gvars" in params and "slurm_features" in (gvars := params["gvars"]) and value in gvars["slurm_features"]:
        msg = f"既に使用されているFeature名です: {value}"
        raise OhpcParameterError(msg, link)


def check_parameter_partition_name(value: str, params: dict[str, Any]) -> None:
    if not isinstance(value, str):
        msg = f"partition_nameには文字列を指定してください: {type(value).__name__}"
        raise OhpcParameterError(msg, "#Partition名の指定")

    if not value:
        msg = "partition_nameには空文字列以外を指定してください"
        raise OhpcParameterError(msg, "#Partition名の指定")

    # 命名規則チェック（英数字とハイフン、アンダースコア、1-64文字）
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}[a-zA-Z0-9]$", value):
        msg = f"partition_nameの命名規則が不正です（英数字・ハイフン・アンダースコア、1-64文字）: {value}"
        raise OhpcParameterError(msg, "#Partition名の指定")

    # 重複チェック
    if (
        "gvars" in params
        and "slurm_partitions" in (gvars := params["gvars"])
        and value in gvars["slurm_partitions"]
        and not (params.get("add_to_existing"))
    ):
        msg = f"既に使用されているPartition名です: {value}"
        raise OhpcParameterError(msg, "#Partition名の指定")


def check_parameter_partition_allow_groups_optional(value: list, _params: dict[str, Any]) -> None:
    if not isinstance(value, list):
        msg = f"partition_allow_groupsにはリストを指定してください: {type(value).__name__}"
        raise OhpcParameterError(msg, "#アクセス制御設定（オプション）")

    if _params.get("add_to_existing"):
        # 既存の設定にFeatureを追加する場合は、アクセス制御グループの指定を許容しない
        msg = "既存のPartitionにFeatureを追加する場合、partition_allow_groupsは指定できません"
        raise OhpcParameterError(msg, "#アクセス制御設定（オプション）")

    for group in value:
        if not isinstance(group, str):
            msg = f"partition_allow_groupsの各要素には文字列を指定してください: {type(group).__name__}"
            raise OhpcParameterError(msg, "#アクセス制御設定（オプション）")

        if not group:
            msg = "partition_allow_groupsに空文字列は指定できません"
            raise OhpcParameterError(msg, "#アクセス制御設定（オプション）")

        # UNIXグループ名の命名規則（英数字、ハイフン、アンダースコア、1-32文字）
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,30}[a-zA-Z0-9]$", group):
            msg = f"partition_allow_groupsのグループ名が無効です（英数字・ハイフン・アンダースコア、2-32文字）: {group}"
            raise OhpcParameterError(msg, "#アクセス制御設定（オプション）")


# ============================================================================
# DNS Validation
# ============================================================================


def check_parameter_dns_forwarders(value: list[str], _params: dict[str, Any]) -> None:
    if not isinstance(value, list):
        msg = f"dns_forwardersにはリストを指定してください: {type(value).__name__}"
        raise OhpcParameterError(msg, "#DNSフォワーダー¶")

    if len(value) == 0:
        msg = "dns_forwardersには少なくとも1つのDNSサーバを指定してください"
        raise OhpcParameterError(msg, "#DNSフォワーダー¶")

    for forwarder in value:
        _check_ipv4_format(forwarder, "#DNSフォワーダー¶")


def check_parameter_dns_domain_optional(value: str, _params: dict[str, Any]) -> None:
    if not _validate_domain_name(value):
        msg = f"正しいドメイン名の形式ではありません: {value}"
        raise OhpcParameterError(msg, "#クラスタ内部ドメイン名")


# ============================================================================
# Slurm Spec Utility Functions
# ============================================================================


def spec_env_munge_key(gvars, vcp, token, *, verify=True):
    """VaultからMunge鍵を取得して返す。"""
    vault_url = f"{vcp.vcc_info()['vault_url']}/v1/{gvars['vault_path_munge_key']}"
    r = requests.get(vault_url, headers={"X-Vault-Token": token}, timeout=30, verify=verify)
    return r.json()["data"]["munge.key"]


# ============================================================================
# Slurm Features/Partitions Management
# ============================================================================


def generate_slurm_features_params(variables: dict[str, Any], prefix: str = "compute_") -> tuple[str, dict[str, Any]]:
    """variables からSlurm Feature設定パラメータを生成し (feature_name, feature_config) を返す。"""
    # Feature識別情報
    feature_config: dict[str, Any] = {
        # VCP設定（必須）
        "vc_unit": variables["feature_name"],
        "provider": variables[f"{prefix}provider"],
        "flavor": variables[f"{prefix}flavor"],
        "use_gpu": variables[f"{prefix}use_gpu"],
        "gpus": variables.get(f"{prefix}gpus", 0),
        # ノード設定
        "nodes": variables[f"{prefix}nodes"],
        "ip_addresses": parse_ip_ranges(variables[f"{prefix}ip_ranges"]),
        "hostname_template": variables[f"{prefix}hostname_template"],
    }

    # オプション設定の追加
    if f"{prefix}instance_type" in variables:
        feature_config["instance_type"] = variables[f"{prefix}instance_type"]
    if f"{prefix}root_size" in variables:
        feature_config["root_size"] = variables[f"{prefix}root_size"]
    if f"{prefix}optional_nfs_entries" in variables:
        nfs_entries = variables[f"{prefix}optional_nfs_entries"].strip()
        if nfs_entries:  # 空文字列でない場合のみエンコード
            feature_config["nfs_entries"] = encode_nfs_fstab_entries(nfs_entries)

    # mdx固有パラメータの追加
    if "mdx_compute_pack_num" in variables:
        feature_config["mdx_pack_num"] = variables["mdx_compute_pack_num"]

    return variables["feature_name"], feature_config


# ============================================================================
# IP Address Parsing
# ============================================================================


def parse_ip_range(ip_range_str: str) -> list[str]:
    """
    IPレンジ文字列を解析してIPアドレスのリストを返す

    Args:
        ip_range_str: "172.30.2.121-130" 形式、または "172.30.2.121-172.30.2.130" 形式

    Returns:
        list[str]: IPアドレス文字列のリスト

    Example:
        >>> parse_ip_range("172.30.2.121-123")
        ['172.30.2.121', '172.30.2.122', '172.30.2.123']
        >>> parse_ip_range("172.30.2.121-172.30.2.123")
        ['172.30.2.121', '172.30.2.122', '172.30.2.123']
        >>> parse_ip_range("172.30.2.121")
        ['172.30.2.121']
    """
    if "-" not in ip_range_str:
        # 単一IPアドレス
        return [ip_range_str]

    start_ip_str, end_str = ip_range_str.split("-")
    start_ip = IPv4Address(start_ip_str.strip())

    # 末尾が最終オクテットのみの場合（例: "172.30.2.121-125"）
    if "." not in end_str:
        end_octet = int(end_str.strip())
        ip_parts = start_ip_str.split(".")
        end_ip_str = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{end_octet}"
    else:
        end_ip_str = end_str.strip()

    end_ip = IPv4Address(end_ip_str)

    ip_list = []
    current_ip = start_ip
    while current_ip <= end_ip:
        ip_list.append(str(current_ip))
        current_ip += 1

    return ip_list


def parse_ip_ranges(ip_ranges: list[str]) -> list[str]:
    """複数のIPレンジ文字列を解析し、重複を除いたソート済みIPアドレスのリストを返す。"""
    return sorted({ip for ip_range in ip_ranges for ip in parse_ip_range(ip_range)})
