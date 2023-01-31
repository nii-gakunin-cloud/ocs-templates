from configparser import ConfigParser
from io import StringIO
from pathlib import Path
from subprocess import run
from tempfile import NamedTemporaryFile

import yaml

GROUP_VARS_DIR = "group_vars"
GROUP_VARS_EXTS = ["", ".yml", ".yaml", ".json"]
DEFAULT_GROUP_VARS_FILE = "00-params.yml"


class Vault(str):
    pass


def vault_constructor(loader, node):
    value = loader.construct_scalar(node)
    return Vault(value)


def vault_representer(dumper, data):
    return dumper.represent_scalar("!vault", data, style="|")


yaml.add_constructor("!vault", vault_constructor)
yaml.add_representer(Vault, vault_representer)


def _load_group_vars_yml(path):
    if path.exists():
        with path.open() as f:
            return yaml.load(f, Loader=yaml.Loader)
    else:
        return {}


def _store_group_vars_yml(path, vars):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode="w") as f:
        yaml.dump(vars, f, default_flow_style=False, Dumper=yaml.Dumper)


def _group_vars_files(target_group, work_dir="."):
    group_path = Path(work_dir) / GROUP_VARS_DIR / target_group
    if group_path.is_dir():
        return sorted(
            [
                x
                for x in group_path.glob("*")
                if x.suffix in GROUP_VARS_EXTS and x.is_file()
            ]
        )
    else:
        for x in GROUP_VARS_EXTS:
            path = group_path.parent / f"{target_group}{x}"
            if path.exists():
                return [path]
        return []


def _load_group_vars(target_group, work_dir="."):
    file_list = _group_vars_files(target_group, work_dir)
    data = {}
    for x in file_list:
        data.update(_load_group_vars_yml(x))
    return data


def _decrypt_var(value):
    return value if not isinstance(value, Vault) else ansible_vault_decrypt(value)


def _decrypt_vars(vars):
    return dict([(key, _decrypt_var(value)) for key, value in vars.items()])


def load_group_vars(target_group, work_dir=".", _decrypt=False):
    data = _load_group_vars("all", work_dir)
    data.update(_load_group_vars(target_group, work_dir))
    if _decrypt:
        data = _decrypt_vars(data)
    return data


def load_group_var(target_group, name, work_dir=".", _decrypt=False):
    gvars = load_group_vars(target_group, work_dir, _decrypt)
    return gvars[name]


def _ansible_vault_encrypt(value):
    res = run(
        ["ansible-vault", "encrypt_string", str(value)],
        check=True,
        capture_output=True,
        text=True,
    )
    f = StringIO(res.stdout)
    encrypt_value = yaml.load(f, Loader=yaml.Loader)
    return encrypt_value


def ansible_vault_decrypt(value):
    with NamedTemporaryFile(mode="w+") as f:
        f.write(value)
        f.flush()
        res = run(
            ["ansible-vault", "decrypt", "--output", "-", f.name],
            check=True,
            capture_output=True,
            text=True,
        )
        ff = StringIO(res.stdout)
        return yaml.safe_load(ff)


def _encrypt_args(**args):
    return dict([(k, _ansible_vault_encrypt(v)) for k, v in args.items()])


def update_group_vars(target_group, _file=None, _encrypt=False, work_dir=".", **args):
    if _encrypt:
        args = _encrypt_args(**args)

    file_list = _group_vars_files(target_group, work_dir)
    if _file is not None:
        file_list = [x for x in file_list if x.name == _file or x.stem == _file]
    if len(file_list) == 0:
        filename = _file if _file is not None else DEFAULT_GROUP_VARS_FILE
        file_list = [Path(work_dir) / GROUP_VARS_DIR / target_group / filename]

    updated = set()
    for file in file_list:
        vars = _load_group_vars_yml(file)
        keys = set(vars.keys()) & set(args.keys())
        updated |= keys
        for key in keys:
            vars[key] = args[key]
        _store_group_vars_yml(file, vars)

    file = file_list[-1]
    vars = _load_group_vars_yml(file)
    remain_vars = dict(
        [(key, value) for key, value in args.items() if key not in updated]
    )
    vars.update(remain_vars)
    _store_group_vars_yml(file, vars)


def remove_group_vars(target_group, *args, work_dir="."):
    file_list = _group_vars_files(target_group, work_dir)
    for file in file_list:
        vars = dict(
            [
                (key, value)
                for key, value in _load_group_vars_yml(file).items()
                if key not in args
            ]
        )
        _store_group_vars_yml(file, vars)


def _merge_dict(target, other):
    for key, value in other.items():
        if isinstance(value, dict):
            _merge_dict(target.setdefault(key, {}), value)
        else:
            if key not in target:
                target[key] = value
    return target


def update_inventory_yml(
    new_value, inventory_path=Path("inventory.yml"), backup=".bak"
):
    if inventory_path.exists():
        current_value = {}
        with inventory_path.open() as f:
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
    with inventory_path.open(mode="w") as f:
        yaml.safe_dump(inventory, f)
    return inventory_path


def remove_group_from_inventory_yml(
    name, inventory_path=Path("inventory.yml"), backup=".bak"
):
    with inventory_path.open() as f:
        inventory = yaml.safe_load(f)
    del inventory["all"]["children"][name]
    if backup is not None:
        inventory_path.rename(Path(inventory_path.parent, inventory_path.name + backup))
    with inventory_path.open(mode="w") as f:
        yaml.safe_dump(inventory, f)
    return inventory_path


def setup_ansible_cfg(inventory_path=Path("inventory.yml"), backup=".bak"):
    cfg = ConfigParser(interpolation=None)
    cfg_path = Path("ansible.cfg").resolve()
    if cfg_path.exists():
        with cfg_path.open() as f:
            cfg.read_file(f)
        if backup is not None:
            cfg_path.rename(Path(cfg_path.parent, cfg_path.name + backup))
    else:
        cfg["defaults"] = {}
        cfg["ssh_connection"] = {}

    cfg["defaults"]["inventory"] = str(inventory_path.resolve())
    cfg["ssh_connection"]["ssh_args"] = " ".join(
        [
            "-C",
            "-o",
            "ControlMaster=auto",
            "-o",
            "ControlPersist=60s",
            "-o",
            "ControlPath=~/.ansible/cp/%r@%h:%p",
        ]
    )

    with cfg_path.open(mode="w") as f:
        cfg.write(f)
    cfg_dir = cfg_path.parent
    cfg_dir.chmod(cfg_dir.stat().st_mode & ~0o022)
    return cfg_path
