# ruff: noqa: RUF002
from __future__ import annotations

from pathlib import Path
from re import match
from typing import Any, TypeAlias

import yaml

GROUP_VARS_DIR = "group_vars"

PathStrType: TypeAlias = Path | str | None
PathOptType: TypeAlias = Path | None


class _LiteralBlockDumper(yaml.SafeDumper):
    """複数行文字列をリテラルブロックスカラー（|）で出力する Dumper"""


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_LiteralBlockDumper.add_representer(str, _str_representer)


def _load_group_vars_yml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_group_vars(target_group: str, work_dir: PathOptType = None) -> dict[str, Any]:
    if work_dir is None:
        work_dir = Path.cwd()
    target_path = work_dir / GROUP_VARS_DIR / target_group
    if target_path.is_dir():
        data: dict[str, Any] = {}
        for gv_path in target_path.glob("*.yml"):
            data.update(_load_group_vars_yml(gv_path))
        return data

    if not target_path.exists():
        return _load_group_vars_yml(target_path.with_suffix(".yml"))

    return _load_group_vars_yml(target_path)


def load_group_vars(target_group: str, work_dir: PathStrType = None) -> dict[str, Any]:
    if isinstance(work_dir, str):
        work_dir = Path(work_dir)
    data = _load_group_vars("all", work_dir)
    data.update(_load_group_vars(target_group, work_dir))
    return data


def load_group_var(target_group: str, name: str, work_dir: PathStrType = None) -> Any:
    gvars = load_group_vars(target_group, work_dir)
    return gvars.get(name)


def store_group_vars(target_group: str, gvars: dict[str, Any], work_dir: PathStrType = None) -> None:
    if work_dir is None:
        work_dir = Path.cwd()
    if isinstance(work_dir, str):
        work_dir = Path(work_dir)
    gv_path = (work_dir / GROUP_VARS_DIR / target_group).with_suffix(".yml")
    gv_path.parent.mkdir(parents=True, exist_ok=True)
    with gv_path.open(mode="w", encoding="utf-8") as f:
        yaml.dump(gvars, f, Dumper=_LiteralBlockDumper, default_flow_style=False, allow_unicode=True)


def update_group_vars(_target_group: str, work_dir: PathStrType = None, **kwargs) -> None:
    if isinstance(work_dir, str):
        work_dir = Path(work_dir)
    gvars = _load_group_vars(_target_group, work_dir=work_dir)
    gvars.update(kwargs)
    store_group_vars(_target_group, gvars, work_dir=work_dir)


def remove_group_vars(
    _target_group: str,
    *args: str,
    work_dir: PathStrType = None,
    if_exists: bool = False,
):
    if isinstance(work_dir, str):
        work_dir = Path(work_dir)
    gvars = _load_group_vars(_target_group, work_dir=work_dir)
    for arg in args:
        if if_exists and arg not in gvars:
            continue
        gvars.pop(arg)
    store_group_vars(_target_group, gvars, work_dir=work_dir)


def _merge_dict(target: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    for key, value in other.items():
        if isinstance(value, dict):
            _merge_dict(target.setdefault(key, {}), value)
        elif key not in target:
            target[key] = value
    return target


def update_inventory_yml(
    new_value: dict[str, Any],
    inventory_path: PathOptType = None,
    backup: str | None = ".bak",
) -> Path:
    if inventory_path is None:
        inventory_path = Path("inventory.yml")
    if inventory_path.exists():
        current_value = {}
        with inventory_path.open(encoding="utf-8") as f:
            current_value = yaml.safe_load(f)
        inventory = _merge_dict(new_value, current_value) if current_value is not None else new_value
        if backup is not None:
            inventory_path.rename(Path(inventory_path.parent, inventory_path.name + backup))
    else:
        inventory = new_value
    with inventory_path.open(mode="w", encoding="utf-8") as f:
        yaml.safe_dump(inventory, f)
    return inventory_path


def remove_group_from_inventory_yml(
    name: str, inventory_path: PathOptType = None, backup: str | None = ".bak", *, recursive: bool = False
) -> Path:
    if inventory_path is None:
        inventory_path = Path("inventory.yml")
    with inventory_path.open(encoding="utf-8") as f:
        inventory = yaml.safe_load(f)

    if recursive:

        def _remove_recursive(d: dict[str, Any]) -> bool:
            if "children" in d and isinstance(d["children"], dict):
                if name in d["children"]:
                    del d["children"][name]
                    return True
                for child in d["children"].values():
                    if isinstance(child, dict) and _remove_recursive(child):
                        return True
            return False

        if not _remove_recursive(inventory.get("all", {})):
            msg = f"Group '{name}' が見つかりません"
            raise KeyError(msg)
    else:
        del inventory["all"]["children"][name]

    if backup is not None:
        inventory_path.rename(Path(inventory_path.parent, inventory_path.name + backup))
    with inventory_path.open(mode="w", encoding="utf-8") as f:
        yaml.safe_dump(inventory, f)
    return inventory_path


# ============================================================================
# Slurm Features/Partitions Management
# ============================================================================


def update_slurm_features(
    ugroup_name: str, feature_name: str, feature_config: dict[str, Any], work_dir: PathStrType = None
) -> None:
    """
    slurm_features に Feature を追加・更新

    Args:
        ugroup_name: UnitGroup名
        feature_name: Feature名
        feature_config: Feature設定辞書
        work_dir: 作業ディレクトリ
    """
    gvars = load_group_vars(ugroup_name, work_dir)
    slurm_features = gvars.get("slurm_features", {})
    slurm_features[feature_name] = feature_config
    update_group_vars(ugroup_name, work_dir=work_dir, slurm_features=slurm_features)


def update_slurm_partitions(
    ugroup_name: str, partition_name: str, partition_config: dict[str, Any], work_dir: PathStrType = None
) -> None:
    """
    slurm_partitions に Partition を追加・更新

    Args:
        ugroup_name: UnitGroup名
        partition_name: Partition名
        partition_config: Partition設定辞書
        work_dir: 作業ディレクトリ
    """
    gvars = load_group_vars(ugroup_name, work_dir)
    slurm_partitions = gvars.get("slurm_partitions", {})
    slurm_partitions[partition_name] = partition_config
    update_group_vars(ugroup_name, work_dir=work_dir, slurm_partitions=slurm_partitions)


def add_feature_to_partition(
    ugroup_name: str, partition_name: str, feature_name: str, work_dir: PathStrType = None
) -> None:
    """
    PartitionにFeatureを追加する。

    Feature名からNodeset名（ns-{feature_name}）に変換してPartitionに追加する。
    Partition が存在しない場合は新規作成する（default: False）。

    Args:
        ugroup_name: UnitGroup名
        partition_name: Partition名
        feature_name: Feature名
        work_dir: 作業ディレクトリ
    """
    gvars = load_group_vars(ugroup_name, work_dir)
    is_new = check_nodeset_addable_to_partition(gvars, feature_name, partition_name)

    nodeset_name = f"ns-{feature_name}"
    if is_new:
        partition_config = {"nodesets": [nodeset_name], "default": False}
    else:
        partition_config = gvars["slurm_partitions"][partition_name]
        if "nodesets" not in partition_config:
            partition_config["nodesets"] = []
        partition_config["nodesets"].append(nodeset_name)

    update_slurm_partitions(ugroup_name, partition_name, partition_config, work_dir)


def build_slurm_hostlist(hostname_template: str, count: int, *, first_index: int = 1) -> str:
    """
    hostname_template とノード数から Slurm の hostlist 表記を生成する。

    Args:
        hostname_template: ホスト名テンプレート (例: "c{:02}", "gpu{}")
        count: ノード数
        first_index: 開始インデックス (デフォルト: 1)

    Returns:
        Slurm hostlist 表記 (例: "c[01-20]", "gpu[1-4]")
        count が 1 の場合は単一ホスト名 (例: "c01")
        count が 0 以下の場合は空文字列
    """
    if count <= 0:
        return ""

    first = hostname_template.format(first_index)

    if count == 1:
        return first

    last = hostname_template.format(first_index + count - 1)

    # ホスト名を prefix + 末尾の数字部分に分割
    m = match(r"^(.*?)(\d+)$", first)
    if not m:
        return first

    prefix = m.group(1)
    first_num = m.group(2)

    m_last = match(r"^(.*?)(\d+)$", last)
    last_num = m_last.group(2)

    return f"{prefix}[{first_num}-{last_num}]"


def find_affected_partitions(gvars: dict[str, Any], feature_name: str) -> list[str]:
    """
    Feature が属する Partition 名のリストを返す。

    Feature名からNodeset名(ns-{feature_name})を導出し、
    そのNodesetを含むPartitionを検索する。

    Args:
        gvars: group_vars辞書
        feature_name: Feature名

    Returns:
        Feature が属する Partition 名のリスト
    """
    nodeset_name = f"ns-{feature_name}"
    return [
        pname
        for pname, pconfig in gvars.get("slurm_partitions", {}).items()
        if nodeset_name in pconfig.get("nodesets", [])
    ]


def check_feature_deletion_impact(gvars: dict[str, Any], feature_name: str) -> tuple[list[str], list[str]]:
    """
    Feature 削除の影響を確認する。

    各 Partition について、Nodeset が残るか Partition ごと削除されるかを判定する。
    default Partition が削除される場合は RuntimeError を発生させる。

    Args:
        gvars: group_vars辞書
        feature_name: 削除する Feature 名

    Returns:
        (affected_partitions, deleted_partitions) のタプル。
        affected_partitions: 影響を受ける Partition 名のリスト
        deleted_partitions: Partition ごと削除される Partition 名のリスト
            (affected_partitions の部分集合)
    """
    affected_partitions = find_affected_partitions(gvars, feature_name)
    target_nodeset = f"ns-{feature_name}"
    deleted_partitions = []

    for pname in affected_partitions:
        pconfig = gvars["slurm_partitions"][pname]
        nodesets = pconfig["nodesets"]
        remaining = [ns for ns in nodesets if ns != target_nodeset]
        if not remaining:
            if pconfig.get("default", False):
                msg = (
                    f"Partition '{pname}' は default Partition のため削除できません。\n"
                    f"先に「085-Partitionの変更.ipynb」で default を別の Partition に変更してください。"
                )
                raise RuntimeError(msg)
            deleted_partitions.append(pname)

    return affected_partitions, deleted_partitions


def check_nodeset_addable_to_partition(gvars: dict[str, Any], feature_name: str, partition_name: str) -> bool:
    """
    Nodeset を Partition に追加可能かチェックする。

    追加不可の場合は例外を発生させる。
    Partition が存在しない場合は新規作成として扱い True を返す。

    Args:
        gvars: group_vars辞書
        feature_name: 追加する Feature 名
        partition_name: 追加先の Partition 名

    Returns:
        True: Partition が新規作成される場合
        False: 既存の Partition に追加する場合

    Raises:
        KeyError: Feature が見つからない場合
        ValueError: Nodeset が既に Partition に含まれている場合
    """
    if feature_name not in gvars.get("slurm_features", {}):
        msg = f"Feature '{feature_name}' が見つかりません"
        raise KeyError(msg)

    partitions = gvars.get("slurm_partitions", {})
    if partition_name not in partitions:
        return True

    nodeset_name = f"ns-{feature_name}"
    if nodeset_name in partitions[partition_name].get("nodesets", []):
        msg = f"Nodeset '{nodeset_name}' は既に Partition '{partition_name}' に含まれています"
        raise ValueError(msg)

    return False


def check_nodeset_removable_from_partition(gvars: dict[str, Any], feature_name: str, partition_name: str) -> list[str]:
    """
    Nodeset を Partition から除外可能かチェックする。

    除外後に空になる Partition 名のリストを返す。
    除外不可の場合は例外を発生させる。

    Args:
        gvars: group_vars辞書
        feature_name: 除外する Feature 名
        partition_name: 除外元の Partition 名

    Returns:
        除外後に空になり削除される Partition 名のリスト(0個または1個)

    Raises:
        KeyError: Partition や Nodeset が見つからない場合
        RuntimeError: 除外後に Nodeset がどの Partition にも属さなくなる場合、
                      または空になる Partition が default の場合
    """
    partitions = gvars.get("slurm_partitions", {})
    if partition_name not in partitions:
        msg = f"Partition '{partition_name}' が見つかりません"
        raise KeyError(msg)

    nodeset_name = f"ns-{feature_name}"
    pconfig = partitions[partition_name]
    if nodeset_name not in pconfig.get("nodesets", []):
        msg = f"Nodeset '{nodeset_name}' は Partition '{partition_name}' に含まれていません"
        raise KeyError(msg)

    # 除外後に Nodeset がどの Partition にも属さなくなるかチェック
    all_partitions = find_affected_partitions(gvars, feature_name)
    other_partitions = [p for p in all_partitions if p != partition_name]
    if not other_partitions:
        msg = (
            f"Nodeset '{nodeset_name}' は Partition '{partition_name}' にのみ所属しています。\n"
            f"除外するとどの Partition にも属さなくなるため、この操作はできません。\n"
            f"Feature ごと削除する場合は「084-Featureの削除.ipynb」を使用してください。"
        )
        raise RuntimeError(msg)

    # 除外後に Partition が空になる場合のチェック
    deleted_partitions = []
    remaining = [ns for ns in pconfig["nodesets"] if ns != nodeset_name]
    if not remaining:
        if pconfig.get("default", False):
            msg = (
                f"Partition '{partition_name}' は default Partition のため削除できません。\n"
                f"先に「085-Partitionの変更.ipynb」で default を別の Partition に変更してください。"
            )
            raise RuntimeError(msg)
        deleted_partitions.append(partition_name)

    return deleted_partitions


def format_allow_groups(allow_groups: list[str]) -> str:
    """AllowGroups のリストを表示用文字列に変換する。

    Args:
        allow_groups: AllowGroups のリスト

    Returns:
        表示用文字列
    """
    return ", ".join(allow_groups) if allow_groups else "なし（全ユーザー）"  # noqa: RUF001


def get_default_partition(gvars: dict[str, Any]) -> str | None:
    """
    現在の default Partition 名を返す。未設定の場合は None。

    Args:
        gvars: group_vars辞書

    Returns:
        default Partition 名、または None
    """
    return next(
        (pname for pname, pc in gvars.get("slurm_partitions", {}).items() if pc.get("default", False)),
        None,
    )


def set_default_partition(ugroup_name: str, partition_name: str, work_dir: PathStrType = None) -> None:
    """
    デフォルト Partition を設定する。
    既存のデフォルト Partition の `default` を False に変更し、
    指定した Partition の `default` を True に設定する。

    Args:
        ugroup_name: UnitGroup名
        partition_name: デフォルトに設定する Partition 名
        work_dir: 作業ディレクトリ

    Raises:
        KeyError: 指定した Partition が存在しない場合
    """
    gvars = load_group_vars(ugroup_name, work_dir)
    partitions = gvars.get("slurm_partitions", {})

    if partition_name not in partitions:
        msg = f"Partition '{partition_name}' が見つかりません"
        raise KeyError(msg)

    # 全 Partition の default を False に
    for pname in partitions:
        partitions[pname]["default"] = False

    # 指定した Partition を True に
    partitions[partition_name]["default"] = True

    update_group_vars(ugroup_name, work_dir=work_dir, slurm_partitions=partitions)


def update_partition_allow_groups(
    ugroup_name: str,
    partition_name: str,
    allow_groups: list[str],
    work_dir: PathStrType = None,
) -> None:
    """
    Partition の AllowGroups 設定を更新する。

    Args:
        ugroup_name: UnitGroup名
        partition_name: Partition 名
        allow_groups: 許可するグループのリスト(空リストの場合はアクセス制限なし)
        work_dir: 作業ディレクトリ

    Raises:
        KeyError: 指定した Partition が存在しない場合
    """
    gvars = load_group_vars(ugroup_name, work_dir)
    partitions = gvars.get("slurm_partitions", {})

    if partition_name not in partitions:
        msg = f"Partition '{partition_name}' が見つかりません"
        raise KeyError(msg)

    partition_config = dict(partitions[partition_name])

    if allow_groups:
        partition_config["allow_groups"] = allow_groups
    else:
        # 空リストの場合は allow_groups キーを削除(制限なし = AllowGroups=ALL)
        partition_config.pop("allow_groups", None)

    update_slurm_partitions(ugroup_name, partition_name, partition_config, work_dir)


def delete_slurm_feature(ugroup_name: str, feature_name: str, work_dir: PathStrType = None) -> None:
    """
    group_vars から Feature 定義を削除する。

    Args:
        ugroup_name: UnitGroup名
        feature_name: 削除する Feature 名
        work_dir: 作業ディレクトリ

    Raises:
        KeyError: 指定した Feature が存在しない場合
    """
    gvars = load_group_vars(ugroup_name, work_dir)

    if feature_name not in gvars.get("slurm_features", {}):
        msg = f"Feature '{feature_name}' が見つかりません"
        raise KeyError(msg)

    del gvars["slurm_features"][feature_name]
    update_group_vars(ugroup_name, work_dir=work_dir, slurm_features=gvars["slurm_features"])


def remove_feature_from_partition(
    ugroup_name: str, partition_name: str, feature_name: str, work_dir: PathStrType = None
) -> None:
    """
    Partition の nodesets から Feature に対応する Nodeset を削除する。
    Nodeset が1つしかない場合は Partition ごと削除する。

    Args:
        ugroup_name: UnitGroup名
        partition_name: Partition 名
        feature_name: 削除する Feature 名
        work_dir: 作業ディレクトリ

    Raises:
        KeyError: 指定した Partition または Feature に対応する Nodeset が存在しない場合
    """
    gvars = load_group_vars(ugroup_name, work_dir)
    partitions = gvars.get("slurm_partitions", {})

    if partition_name not in partitions:
        msg = f"Partition '{partition_name}' が見つかりません"
        raise KeyError(msg)

    nodeset_name = f"ns-{feature_name}"
    partition_config = partitions[partition_name]

    if nodeset_name not in partition_config.get("nodesets", []):
        msg = f"Nodeset '{nodeset_name}' は Partition '{partition_name}' に含まれていません"
        raise KeyError(msg)

    partition_config["nodesets"].remove(nodeset_name)

    if not partition_config["nodesets"]:
        # Nodeset が空になった場合は Partition ごと削除
        del partitions[partition_name]
    else:
        partitions[partition_name] = partition_config

    update_group_vars(ugroup_name, work_dir=work_dir, slurm_partitions=partitions)


# ============================================================================
# Slurm Custom Configuration Management
# ============================================================================

SLURM_CONF_MANAGED_PARAMS = [
    "ClusterName",
    "SlurmctldHost",
    "NodeSet",
    "PartitionName",
    "MaxNodeCount",
    "GresTypes",
]


def validate_slurm_custom_conf(content: str) -> list[str]:
    """
    カスタム設定の内容をバリデーションする。

    テンプレートで自動管理されるパラメータが含まれていないかチェックする。
    コメント行(# で始まる行)と空行はスキップする。

    Args:
        content: カスタム設定の内容(複数行文字列)

    Returns:
        エラーメッセージのリスト(空なら検証OK)
    """
    errors: list[str] = []
    managed_lower = {p.lower(): p for p in SLURM_CONF_MANAGED_PARAMS}

    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", maxsplit=1)[0].strip()
        key_lower = key.lower()
        if key_lower in managed_lower:
            canonical = managed_lower[key_lower]
            errors.append(
                f"行 {lineno}: '{key}' はテンプレートで自動管理されるパラメータです "
                f"({canonical})。カスタム設定には記述できません。"
            )
    return errors


def update_slurm_custom_conf(ugroup_name: str, content: str, work_dir: PathStrType = None) -> None:
    """
    slurm_custom_conf_content を group_vars に保存する。

    バリデーションを実行し、禁止パラメータが含まれている場合は ValueError を発生させる。
    空文字列の場合は slurm_custom_conf_content キーを group_vars から削除する。

    Args:
        ugroup_name: UnitGroup名
        content: カスタム設定の内容(複数行文字列)
        work_dir: 作業ディレクトリ

    Raises:
        ValueError: 禁止パラメータが含まれている場合
    """
    content = content.strip()

    if not content:
        remove_group_vars(ugroup_name, "slurm_custom_conf_content", work_dir=work_dir, if_exists=True)
        return

    errors = validate_slurm_custom_conf(content)
    if errors:
        msg = "カスタム設定に以下の問題があります:\n" + "\n".join(errors)
        raise ValueError(msg)

    update_group_vars(ugroup_name, work_dir=work_dir, slurm_custom_conf_content=content)
