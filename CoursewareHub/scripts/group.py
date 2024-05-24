import json
from configparser import ConfigParser
from pathlib import Path
from re import IGNORECASE, search
from typing import Any, TypeAlias

import yaml

GROUP_VARS_DIR = "group_vars"

PathStrType: TypeAlias = Path | str | None
PathOptType: TypeAlias = Path | None


def _load_group_vars_yml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def _load_group_vars(target_group: str, work_dir: PathOptType = None) -> dict[str, Any]:
    if work_dir is None:
        work_dir = Path.cwd()
    target_path = work_dir / GROUP_VARS_DIR / target_group
    if target_path.is_dir():
        data: dict[str, Any] = {}
        for gv_path in target_path.glob("*.yml"):
            data.update(_load_group_vars_yml(gv_path))
        return data

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


def store_group_vars(
    target_group: str, gvars: dict[str, Any], work_dir: PathStrType = None
) -> None:
    if work_dir is None:
        work_dir = Path.cwd()
    if isinstance(work_dir, str):
        work_dir = Path(work_dir)
    gv_path = work_dir / GROUP_VARS_DIR / target_group
    gv_path.parent.mkdir(parents=True, exist_ok=True)
    with gv_path.open(mode="w", encoding="utf-8") as f:
        yaml.safe_dump(gvars, f, default_flow_style=False)


def update_group_vars(
    _target_group: str, work_dir: PathStrType = None, **kwargs
) -> None:
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


def show_group_vars(
    target_group: str, work_dir: PathStrType = None, show_all: bool = False
) -> None:
    gvars = load_group_vars(target_group, work_dir)
    for key, value in gvars.items():
        if show_all or not search("password", key, flags=IGNORECASE):
            print(f"{key}: {json.dumps(value)}")


def _merge_dict(target: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    for key, value in other.items():
        if isinstance(value, dict):
            _merge_dict(target.setdefault(key, {}), value)
        else:
            if key not in target:
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
        inventory = (
            _merge_dict(new_value, current_value)
            if current_value is not None
            else new_value
        )
        if backup is not None:
            inventory_path.rename(
                Path(inventory_path.parent, inventory_path.name + backup)
            )
    else:
        inventory = new_value
    with inventory_path.open(mode="w", encoding="utf-8") as f:
        yaml.safe_dump(inventory, f)
    return inventory_path


def remove_group_from_inventory_yml(
    name: str, inventory_path: PathOptType = None, backup: str | None = ".bak"
) -> Path:
    if inventory_path is None:
        inventory_path = Path("inventory.yml")
    with inventory_path.open(encoding="utf-8") as f:
        inventory = yaml.safe_load(f)
    del inventory["all"]["children"][name]
    if backup is not None:
        inventory_path.rename(Path(inventory_path.parent, inventory_path.name + backup))
    with inventory_path.open(mode="w", encoding="utf-8") as f:
        yaml.safe_dump(inventory, f)
    return inventory_path


def setup_ansible_cfg(
    inventory_path: PathOptType = None, backup: str | None = ".bak"
) -> Path:
    if inventory_path is None:
        inventory_path = Path("inventory.yml")
    cfg = ConfigParser(interpolation=None)
    cfg_path = Path("ansible.cfg").resolve()
    if cfg_path.exists():
        with cfg_path.open(encoding="utf-8") as f:
            cfg.read_file(f)
        if backup is not None:
            cfg_path.rename(Path(cfg_path.parent, cfg_path.name + backup))
    else:
        cfg["defaults"] = {}

    cfg["defaults"]["inventory"] = str(inventory_path.resolve())

    with cfg_path.open(mode="w", encoding="utf-8") as f:
        cfg.write(f)
    cfg_dir = cfg_path.parent
    cfg_dir.chmod(cfg_dir.stat().st_mode & ~0o022)
    return cfg_path
