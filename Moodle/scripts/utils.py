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
    'vc_flavor': '#VCノードに割り当てるリソース量の指定',
    'vc_moodle_ipaddress': '#IPアドレスの指定',
    'ssh_public_key_path': '#SSH公開鍵認証の鍵ファイルの指定',
    'ssh_private_key_path': '#SSH公開鍵認証の鍵ファイルの指定',
    'moodle_version': '#Moodleのバージョン',
    'moodle_admin_name': '#Moodleの管理者ユーザ',
    'moodle_admin_password': '#Moodleの管理者パスワード',
    'moodle_image_name': '#Moodleのコンテナイメージ',
    'moodle_disk_size': '#Moodleのディスクサイズ',
    'moodle_volume_data_size': '#Moodleのボリュームサイズ',
    'moodle_volume_php_size': '#Moodleのボリュームサイズ',
    'moodle_volume_encrypt': '#Moodleボリュームの暗号化',
    'moodle_url': '#MoodleのURL',
    'moodle_vault_path': '#MoodleパラメータのVaultサーバへの保存',
    'db_image_name': '#データベースのコンテナイメージ',
    'db_moodle_db': '#データベース名',
    'db_moodle_db_user': '#データベースの接続ユーザ',
    'db_disk_size': '#データベースのディスクサイズ',
    'db_volume_size': '#データベースのボリュームサイズ',
    'db_volume_encrypt': '#データベースボリュームの暗号化',
    'db_vault_path': '#データベースパラメータのVaultサーバへの保存',
    'rproxy_image_name': '#リバースプロキシのコンテナイメージ',
    'rproxy_tls_cert_path': '#サーバ証明書',
    'rproxy_tls_key_path': '#サーバ証明書',
}


def check_parameters(*targets, params={}, nb_vars={}):
    kwargs = dict([(x, nb_vars[x]) for x in targets if x in nb_vars])
    for target in targets:
        try:
            if target not in nb_vars:
                raise MoodleParameterError(
                        f'{target}が設定されていません。',
                        target=target)
            eval(f'check_parameter_{target}(nb_vars[target], params, kwargs)')
        except MoodleParameterError as ex:
            display(HTML(
                f'<p>{" ".join(ex.args)}</p><a href="{ex.link}">' +
                'リンク先</a>に戻って再度設定を行ってください。'))
            raise ex


class MoodleParameterError(RuntimeError):
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
        raise MoodleParameterError(
            f"既に使用しているUnitGroup名です: {name}",
            frame=currentframe())
    if not re.match(r'(?a)[a-zA-Z]\w*$', name):
        raise MoodleParameterError(
            f"正しくないUnitGroup名です: {name}",
            frame=currentframe())


def check_parameter_vc_provider(provider, params, kwargs):
    try:
        params['vcp'].df_flavors(provider)
    except Exception:
        raise MoodleParameterError(
            f"VCPがサポートしていないプロバイダです: {provider}",
            frame=currentframe())


def check_parameter_ssh_public_key_path(path, params, kwargs):
    if not Path(path).expanduser().is_file():
        raise MoodleParameterError(
            f"指定されたパスにファイルが存在しません: {path}",
            frame=currentframe())


def check_parameter_ssh_private_key_path(path, params, kwargs):
    private_key_path = Path(path).expanduser()
    if not private_key_path.is_file():
        raise MoodleParameterError(
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
        raise MoodleParameterError(
            f"指定された秘密鍵は公開鍵とペアではありません: {path}",
            frame=currentframe())


def check_parameter_vc_flavor(flavor, params, kwargs):
    try:
        spec = params['vcp'].get_spec(kwargs['vc_provider'], flavor)
    except Exception as ex:
        raise MoodleParameterError(
            f"定義されていないflavorが指定されました: {flavor}",
            frame=currentframe())


def _ipaddress_reachable(ipaddr):
    ret = subprocess.run(["ping", "-c", "3", ipaddr], capture_output=True)
    return (ipaddr, ret.returncode == 0)


def _check_ipv4_format(ipaddr, frame):
    try:
        ip = IPv4Address(ipaddr)
    except AddressValueError:
        raise MoodleParameterError(
            f"正しいIPv4アドレスではありません: {ipaddr}", frame=frame)


def _check_vpn_catalog(ipaddr, vcp, provider, frame):
    catalog = vcp.get_vpn_catalog(provider)
    if 'private_network_ipmask' not in catalog:
        return
    subnet = IPv4Network(catalog['private_network_ipmask'])
    ip = IPv4Address(ipaddr)
    if ip not in subnet:
        raise MoodleParameterError(
                f'範囲外のIPアドレスが指定されています: {ipaddr}; {subnet}',
                frame=frame)


def check_parameter_vc_moodle_ipaddress(value, params, kwargs):
    provider = kwargs['vc_provider']
    _check_ipv4_format(value, currentframe())
    _check_vpn_catalog(value, params['vcp'], provider, currentframe())
    if (provider != 'onpremises' and _ipaddress_reachable(value)[1]):
        raise MoodleParameterError(
            f"指定されたIPアドレスは既に他のノードで利用されています: {value}",
            frame=currentframe())


def check_parameter_moodle_admin_name(name, params, kwargs):
    if not re.match(r'[-\.@_a-z0-9]+$', name):
        raise MoodleParameterError(
            f"正しくないユーザ名です: {name}", frame=currentframe())


def check_parameter_moodle_admin_password(password, params, kwargs):
    if len(password) == 0 or password == 'admin':
        raise MoodleParameterError(
            "正しくないパスワードです", frame=currentframe())


def check_parameter_moodle_version(version, params=None, kwargs=None):
    try:
        r = requests.get(
                'https://api.github.com/repos/moodle/moodle/git/refs/tags')
    except RequestException:
        logger.warning(
            'GitHubからMoodleの情報取得に失敗しました。' +
            'moodle_versionのチェックをスキップします。')
        return
    if not r.ok:
        logger.warning(
            f'GitHubからMoodleの情報取得に失敗しました({r.reason})。' +
            'moodle_versionのチェックをスキップします。')
        return
    if version not in [x['ref'].split('/')[-1] for x in r.json()]:
        eparams = {}
        try:
            eparams['frame'] = currentframe()
        except Exception:
            pass
        raise MoodleParameterError(
                f'Moodleに存在しないバージョンです:{version}', **eparams)


def check_parameter_moodle_image_name(image, params, kwargs):
    pass


def check_parameter_moodle_disk_size(value, params, kwargs):
    if type(value) is not int or value <= 0:
        raise MoodleParameterError(
            f'moodle_disk_sizeには正の整数を指定してください:{value}',
            frame=currentframe())


def check_parameter_moodle_volume_data_size(value, params, kwargs):
    if type(value) is not int or value <= 0:
        raise MoodleParameterError(
            f'moodle_volume_data_sizeには正の整数を指定してください:{value}',
            frame=currentframe())


def check_parameter_moodle_volume_php_size(value, params, kwargs):
    if type(value) is not int or value <= 0:
        raise MoodleParameterError(
            f'moodle_volume_php_sizeには正の整数を指定してください:{value}',
            frame=currentframe())


def check_parameter_moodle_volume_encrypt(value, params, kwargs):
    if type(value) is not bool:
        raise MoodleParameterError(
            f'moodle_volume_encryptには真偽値を指定してください:{value}',
            frame=currentframe())


def check_parameter_moodle_url(name, params, kwargs):
    pass


def check_parameter_moodle_vault_path(name, params, kwargs):
    pass


def check_parameter_db_image_name(value, params, kwargs):
    pass


def check_parameter_db_moodle_db(value, params, kwargs):
    pass


def check_parameter_db_moodle_db_user(value, params, kwargs):
    pass


def check_parameter_db_disk_size(value, params, kwargs):
    if type(value) is not int or value <= 0:
        raise MoodleParameterError(
            f'db_disk_sizeには正の整数を指定してください:{value}',
            frame=currentframe())


def check_parameter_db_volume_size(value, params, kwargs):
    if type(value) is not int or value <= 0:
        raise MoodleParameterError(
            f'db_volume_sizeには正の整数を指定してください:{value}',
            frame=currentframe())


def check_parameter_db_volume_encrypt(value, params, kwargs):
    if type(value) is not bool:
        raise MoodleParameterError(
            f'db_volume_encryptには真偽値を指定してください:{value}',
            frame=currentframe())


def check_parameter_db_vault_path(value, params, kwargs):
    pass


def check_parameter_rproxy_image_name(value, params, kwargs):
    pass


def check_parameter_rproxy_tls_cert_path(path, params, kwargs):
    cert_path = Path(path).resolve()
    if not cert_path.is_file():
        raise MoodleParameterError(
            f"指定されたパスにファイルが存在しません: {path}",
            frame=currentframe())


def check_parameter_rproxy_tls_key_path(path, params, kwargs):
    cert_path = Path(path).resolve()
    if not cert_path.is_file():
        raise MoodleParameterError(
            f"指定されたパスにファイルが存在しません: {path}",
            frame=currentframe())


def retry_exec(func, interval=10, retry_max=60, err=RuntimeError, redo=None):
    for retry in range(retry_max):
        try:
            func()
            break
        except err:
            time.sleep(interval)
            if redo:
                redo()
    else:
        raise Exception("ERROR: timeout")


def setup_yaml_od():
    tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
    yaml.add_constructor(
        tag, lambda loader, node: OrderedDict(loader.construct_pairs(node)))
    yaml.add_representer(
        OrderedDict, lambda dumper, instance: dumper.represent_mapping(
            tag, instance.items()))
