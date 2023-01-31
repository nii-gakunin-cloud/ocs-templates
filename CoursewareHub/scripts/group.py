from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import errno
import os
import re
import yaml
import subprocess
from io import StringIO, BytesIO
import tempfile
import six
import glob
from pathlib import Path
from configparser import ConfigParser


GROUP_VARS_DIR = 'group_vars'


class Vault(str):
    pass


def vault_constructor(loader, node):
    value = loader.construct_scalar(node)
    return Vault(value)


def vault_representer(dumper, data):
    return dumper.represent_scalar(u'!vault', data, style='|')


yaml.add_constructor(u'!vault', vault_constructor)
yaml.add_representer(Vault, vault_representer)


def _load_group_vars_yml(path):
    if os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f)
    else:
        data = {}
    return data


def _load_group_vars(target_group, dir=os.getcwd()):
    parent = os.path.join(dir, GROUP_VARS_DIR, target_group)
    if os.path.isdir(parent):
        data = {}
        for x in glob.glob(f'{parent}/*.yml'):
            data.update(_load_group_vars_yml(x))
        return data
    else:
        return _load_group_vars_yml(
                os.path.join(dir, GROUP_VARS_DIR, target_group))


def load_group_vars(target_group, dir=os.getcwd()):
    data = _load_group_vars('all', dir)
    data.update(_load_group_vars(target_group, dir))
    return data


def load_group_var(target_group, name, dir=os.getcwd()):
    gvars = load_group_vars(target_group, dir)
    return gvars[name]


def store_group_vars(target_group, gvars, work_dir=os.getcwd()):
    path = os.path.join(work_dir, GROUP_VARS_DIR, target_group)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        yaml.safe_dump(gvars, f, default_flow_style=False)


def ansible_vault_encrypt(value):
    output = subprocess.check_output(
            ["ansible-vault", "encrypt_string", value])
    if isinstance(output, six.binary_type):
        f = BytesIO(output)
    else:
        f = StringIO(output)
    encrypt_value = yaml.safe_load(f)
    f.close()
    return encrypt_value


def ansible_vault_decrypt(value):
    work_file = tempfile.mkstemp()
    f = os.fdopen(work_file[0], 'w')
    f.write(value)
    f.close()
    try:
        subprocess.check_output(["ansible-vault", "decrypt", work_file[1]])
        with open(work_file[1]) as f:
            result = f.read()
        return result
    finally:
        os.remove(work_file[1])


def encrypt_args(**args):
    return dict([(k, ansible_vault_encrypt(v)) for k, v in args.items()])


def update_group_vars(_target_group, _encrypt=False, work_dir=os.getcwd(),
                      **args):
    if _encrypt:
        args = encrypt_args(**args)
    gvars = _load_group_vars(_target_group, dir=work_dir)
    gvars.update(args)
    store_group_vars(_target_group, gvars, work_dir=work_dir)


def remove_group_vars(_target_group, *args, work_dir=os.getcwd()):
    gvars = _load_group_vars(_target_group, dir=work_dir)
    for arg in args:
        gvars.pop(arg)
    store_group_vars(_target_group, gvars, work_dir=work_dir)


def show_group_vars(target_group, dir=os.getcwd(), show_all=False):
    path = os.path.join(dir, GROUP_VARS_DIR, target_group)
    with open(path) as f:
        lines = f.readlines()
    for line in lines:
        if show_all or not re.search('password', line, flags=re.IGNORECASE):
            print(line, end="")


def mkdir_p(path):
    os.makedirs(path, exist_ok=True)


def merge_dict(target, other):
    for key, value in other.items():
        if isinstance(value, dict):
            merge_dict(target.setdefault(key, {}), value)
        else:
            if key not in target:
                target[key] = value
    return target


def update_inventory_yml(
        new_value, inventory_path=Path('inventory.yml'), backup='.bak'):
    if inventory_path.exists():
        current_value = {}
        with inventory_path.open() as f:
            current_value = yaml.safe_load(f)
        inventory = (merge_dict(new_value, current_value)
                     if current_value is not None else new_value)
        if backup is not None:
            inventory_path.rename(
                Path(inventory_path.parent, inventory_path.name + backup))
    else:
        inventory = new_value
    with inventory_path.open(mode='w') as f:
        yaml.safe_dump(inventory, f)
    return inventory_path


def remove_group_from_inventory_yml(
        name, inventory_path=Path('inventory.yml'), backup='.bak'):
    with inventory_path.open() as f:
        inventory = yaml.safe_load(f)
    del(inventory['all']['children'][name])
    if backup is not None:
        inventory_path.rename(
            Path(inventory_path.parent, inventory_path.name + backup))
    with inventory_path.open(mode='w') as f:
        yaml.safe_dump(inventory, f)
    return inventory_path


def setup_ansible_cfg(inventory_path=Path('inventory.yml'), backup='.bak'):
    cfg = ConfigParser(interpolation=None)
    cfg_path = Path('ansible.cfg').resolve()
    if cfg_path.exists():
        with cfg_path.open() as f:
            cfg.read_file(f)
        if backup is not None:
            cfg_path.rename(Path(cfg_path.parent, cfg_path.name + backup))
    else:
        cfg['defaults'] = {}

    cfg['defaults']['inventory'] = str(inventory_path.resolve())
    cfg['defaults']['gathering'] = 'explicit'

    with cfg_path.open(mode='w') as f:
        cfg.write(f)
    cfg_dir = cfg_path.parent
    cfg_dir.chmod(cfg_dir.stat().st_mode & ~0o022)
    return cfg_path
