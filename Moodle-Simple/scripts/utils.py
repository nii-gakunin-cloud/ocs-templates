from __future__ import annotations

import contextlib
import re
import subprocess
import time
from collections import OrderedDict
from inspect import currentframe, getframeinfo
from ipaddress import AddressValueError, IPv4Address, IPv4Network
from logging import getLogger
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import requests
import yaml
from IPython.display import HTML, display
from requests.exceptions import RequestException

logger = getLogger(__name__)


anchor_map = {
    "ugroup_name": "#UnitGroup名の指定",
    "vc_provider": "#クラウドプロバイダの指定",
    "vc_flavor": "#VCノードに割り当てるリソース量の指定",
    "vc_moodle_ipaddress": "#IPアドレスの指定",
    "ssh_public_key_path": "#SSH公開鍵認証の鍵ファイルの指定",
    "ssh_private_key_path": "#SSH公開鍵認証の鍵ファイルの指定",
    "moodle_version": "#Moodleのバージョン",
    "moodle_admin_name": "#管理者ユーザ",
    "moodle_image_name": "#Moodleのコンテナイメージ",
    "moodle_disk_size": "#Moodleのディスクサイズ",
    "moodle_volume_data_size": "#Moodleのボリュームサイズ",
    "moodle_volume_php_size": "#Moodleのボリュームサイズ",
    "moodle_url": "#MoodleのURL",
    "moodle_vault_path": "#MoodleパラメータのVaultサーバへの保存",
    "db_image_name": "#データベースのコンテナイメージ",
    "db_moodle_db": "#データベース名",
    "db_moodle_db_user": "#データベースの接続ユーザ",
    "db_disk_size": "#データベースのディスクサイズ",
    "db_volume_size": "#データベースのボリュームサイズ",
    "db_vault_path": "#データベースパラメータのVaultサーバへの保存",
    "rproxy_image_name": "#リバースプロキシのコンテナイメージ",
    "rproxy_tls_cert_path": "#サーバ証明書",
    "rproxy_tls_key_path": "#サーバ証明書",
}


def _check_parameters(*targets: str, params: dict[str, Any], nb_vars: dict[str, Any]) -> None:
    kwargs = {x: nb_vars[x] for x in targets if x in nb_vars}
    for target in targets:
        if target not in nb_vars:
            msg = f"{target}が設定されていません。"
            raise MoodleParameterError(msg, target=target)
        # 動的に検証関数を取得して呼び出す
        func_name = f"check_parameter_{target}"
        check_func = globals().get(func_name)
        if check_func is None:
            msg = f"検証関数が定義されていません: {func_name}"
            raise MoodleParameterError(msg, target=target)
        check_func(nb_vars[target], params, kwargs)


def check_parameters(
    *targets: str, params: dict[str, Any] | None = None, nb_vars: dict[str, Any] | None = None
) -> None:
    if params is None:
        params = {}
    if nb_vars is None:
        nb_vars = {}
    try:
        _check_parameters(*targets, params=params, nb_vars=nb_vars)
    except MoodleParameterError as ex:
        display(HTML(f'<p>{" ".join(ex.args)}</p><a href="{ex.link}">リンク先</a>に戻って再度設定を行ってください。'))
        raise


class MoodleParameterError(RuntimeError):
    def __init__(
        self,
        message: str,
        target: str | None = None,
        frame: Any | None = None,
        link: str | None = None,
    ) -> None:
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


def check_parameter_ugroup_name(name: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    ug = params["vcp"].get_ugroup(name)
    if ug is not None:
        msg = f"既に使用しているUnitGroup名です: {name}"
        raise MoodleParameterError(msg, frame=currentframe())
    if not re.match(r"(?a)[a-zA-Z]\w*$", name):
        msg = f"正しくないUnitGroup名です: {name}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_vc_provider(provider: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    try:
        params["vcp"].df_flavors(provider)
    except Exception as e:
        msg = f"VCPがサポートしていないプロバイダです: {provider}"
        raise MoodleParameterError(msg, frame=currentframe()) from e


def check_parameter_ssh_public_key_path(path: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    if not Path(path).expanduser().is_file():
        msg = f"指定されたパスにファイルが存在しません: {path}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_ssh_private_key_path(path: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    private_key_path = Path(path).expanduser()
    if not private_key_path.is_file():
        msg = f"指定されたパスにファイルが存在しません: {path}"
        raise MoodleParameterError(msg, frame=currentframe())
    ret = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(private_key_path)],
        capture_output=True,
        check=True,
    )
    generated_public_key = ret.stdout.decode("UTF-8").split()
    public_key_path = Path(kwargs["ssh_public_key_path"]).expanduser()
    with public_key_path.open() as f:
        public_key = f.read().split()
    if not (generated_public_key[0] == public_key[0] and generated_public_key[1] == public_key[1]):
        msg = f"指定された秘密鍵は公開鍵とペアではありません: {path}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_vc_flavor(flavor: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    try:
        params["vcp"].get_spec(kwargs["vc_provider"], flavor)
    except Exception as e:
        msg = f"定義されていないflavorが指定されました: {flavor}"
        raise MoodleParameterError(msg, frame=currentframe()) from e


def _ipaddress_reachable(ipaddr: str) -> tuple[str, bool]:
    ret = subprocess.run(["ping", "-c", "3", ipaddr], check=False, capture_output=True)
    return (ipaddr, ret.returncode == 0)


def _check_ipv4_format(ipaddr: str, frame: Any) -> None:
    try:
        IPv4Address(ipaddr)
    except AddressValueError as e:
        msg = f"正しいIPv4アドレスではありません: {ipaddr}"
        raise MoodleParameterError(msg, frame=frame) from e


def _check_vpn_catalog(ipaddr: str, vcp: Any, provider: str, frame: Any) -> None:
    catalog = vcp.get_vpn_catalog(provider)
    if "private_network_ipmask" not in catalog:
        return
    subnet = IPv4Network(catalog["private_network_ipmask"])
    ip = IPv4Address(ipaddr)
    if ip not in subnet:
        msg = f"範囲外のIPアドレスが指定されています: {ipaddr}; {subnet}"
        raise MoodleParameterError(msg, frame=frame)


def check_parameter_vc_moodle_ipaddress(value: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    provider = kwargs["vc_provider"]
    _check_ipv4_format(value, currentframe())
    _check_vpn_catalog(value, params["vcp"], provider, currentframe())
    if provider != "onpremises" and _ipaddress_reachable(value)[1]:
        msg = f"指定されたIPアドレスは既に他のノードで利用されています: {value}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_moodle_admin_name(name: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    if not re.match(r"[-\.@_a-z0-9]+$", name):
        msg = f"正しくないユーザ名です: {name}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_moodle_version(
    version: str, params: dict[str, Any] | None = None, kwargs: dict[str, Any] | None = None
) -> None:
    try:
        r = requests.get("https://api.github.com/repos/moodle/moodle/git/refs/tags", timeout=10)
    except RequestException:
        logger.warning("GitHubからMoodleの情報取得に失敗しました。moodle_versionのチェックをスキップします。")
        return
    if not r.ok:
        logger.warning(
            "GitHubからMoodleの情報取得に失敗しました(%s)。moodle_versionのチェックをスキップします。", r.reason
        )
        return
    if version not in [x["ref"].split("/")[-1] for x in r.json()]:
        eparams: dict[str, Any] = {}
        with contextlib.suppress(Exception):
            eparams["frame"] = currentframe()
        msg = f"Moodleに存在しないバージョンです:{version}"
        raise MoodleParameterError(msg, **eparams)


def check_parameter_moodle_image_name(image: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    pass


def check_parameter_moodle_disk_size(value: Any, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        msg = f"moodle_disk_sizeには正の整数を指定してください:{value}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_moodle_volume_data_size(value: Any, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        msg = f"moodle_volume_data_sizeには正の整数を指定してください:{value}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_moodle_volume_php_size(value: Any, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        msg = f"moodle_volume_php_sizeには正の整数を指定してください:{value}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_moodle_url(value: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    res = urlparse(value)
    if res.scheme not in ["http", "https"]:
        msg = f'スキーム名には"http"または"https"を指定してください:{value}'
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_moodle_vault_path(name: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    pass


def check_parameter_db_image_name(value: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    pass


def check_parameter_db_moodle_db(value: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    pass


def check_parameter_db_moodle_db_user(value: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    pass


def check_parameter_db_disk_size(value: Any, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        msg = f"db_disk_sizeには正の整数を指定してください:{value}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_db_volume_size(value: Any, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        msg = f"db_volume_sizeには正の整数を指定してください:{value}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_db_vault_path(value: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    pass


def check_parameter_rproxy_image_name(value: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    pass


def check_parameter_rproxy_tls_cert_path(path: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    cert_path = Path(path).resolve()
    if not cert_path.is_file():
        msg = f"指定されたパスにファイルが存在しません: {path}"
        raise MoodleParameterError(msg, frame=currentframe())


def check_parameter_rproxy_tls_key_path(path: str, params: dict[str, Any], kwargs: dict[str, Any]) -> None:
    cert_path = Path(path).resolve()
    if not cert_path.is_file():
        msg = f"指定されたパスにファイルが存在しません: {path}"
        raise MoodleParameterError(msg, frame=currentframe())


def retry_exec(
    func: Callable[[], None],
    interval: int = 10,
    retry_max: int = 60,
    err: type[Exception] = RuntimeError,
    redo: Callable[[], None] | None = None,
) -> None:
    for _retry in range(retry_max):
        try:
            func()
            break
        except err:
            time.sleep(interval)
            if redo:
                redo()
    else:
        msg = "ERROR: timeout"
        raise RuntimeError(msg)


def setup_yaml_od() -> None:
    tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
    yaml.add_constructor(tag, lambda loader, node: OrderedDict(loader.construct_pairs(node)))
    yaml.add_representer(
        OrderedDict,
        lambda dumper, instance: dumper.represent_mapping(tag, instance.items()),
    )


def check_version(version: str) -> bool:
    vers = [int(x) for x in version.split(".")]
    if len(vers) < 2 or len(vers) > 3:
        return False
    return (vers[0] == 4 and vers[1] >= 5) or vers[0] == 5
