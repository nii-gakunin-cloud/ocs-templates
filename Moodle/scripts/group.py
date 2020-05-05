from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import errno
import os
import os.path
import re
import yaml
import subprocess
from io import StringIO, BytesIO
import tempfile
import six
import glob


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
        for x in glob.glob("{}/*.yml".format(parent)):
            data.update(_load_group_vars_yml(x))
        return data
    else:
        return _load_group_vars_yml(
                os.path.join(dir, GROUP_VARS_DIR, target_group + '.yml'))


def load_group_vars(target_group, dir=os.getcwd()):
    data = _load_group_vars('all', dir)
    data.update(_load_group_vars(target_group, dir))
    return data


def load_group_var(target_group, name, dir=os.getcwd()):
    gvars = load_group_vars(target_group, dir)
    return gvars[name]


def store_group_vars(target_group, gvars, work_dir=os.getcwd()):
    path = os.path.join(work_dir, GROUP_VARS_DIR, target_group + '.yml')
    mkdir_p(os.path.dirname(path))
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
    path = os.path.join(dir, GROUP_VARS_DIR, target_group + '.yml')
    with open(path) as f:
        lines = f.readlines()
    for line in lines:
        if show_all or not re.search('password', line, flags=re.IGNORECASE):
            print(line, end="")


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
