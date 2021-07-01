from datetime import datetime
from difflib import unified_diff
from logging import basicConfig, getLogger, INFO
import os
from pathlib import Path
import yaml
import shutil
import subprocess
import sys
import copy

from notebook import notebookapp
from IPython.core.display import HTML


WORKDIR = 'edit'
META_YML = '.vcp-meta.yml'
ENV_INHERIT = ['PATH', 'REQUESTS_CA_BUNDLE']
COMMON_VARS = 'playbooks/roles/common/defaults/main.yml'

logger = getLogger(__name__)
basicConfig(level=INFO, format='%(message)s')


def generate_docker_compose(
    target, remote_path, var_files=[], extra_vars={},
    template='template/docker-compose.yml',
):
    conf = _generate_local_path(target, remote_path)
    extra_var_files = copy.copy(var_files)
    if COMMON_VARS not in extra_var_files:
        extra_var_files.append(COMMON_VARS)
    _generate_docker_compose(conf, extra_var_files, extra_vars, template)
    _make_backup(conf, quiet=True)
    _make_metainfo(conf, remote_path=remote_path)
    return generate_edit_link(conf)


def upload_file(target, remote_path, version=None):
    conf = _get_local_path(target, remote_path, version)
    _upload_file(target, conf, remote_path)


def show_local_diff(target, remote_path, version=None):
    conf = _get_local_path(target, remote_path, version)
    _show_local_diff(conf)


def generate_edit_link(conf):
    servers = list(notebookapp.list_running_servers())
    if len(servers) > 0:
        nb_conf = servers[0]
        p = (Path(nb_conf['base_url']) / 'edit' /
             conf.absolute().relative_to(nb_conf['notebook_dir']))
    else:
        p = conf.absolute()
    return HTML(f'<a href={p} target="_blank">{p.name}</a>')


def _build_local_path(target, remote_path, version):
    return (
        Path(WORKDIR).absolute() / target / version / Path(remote_path).name)


def _generate_local_path(target, remote_path):
    version = datetime.now().strftime("%Y%m%d%H%M%S%f")
    ret = _build_local_path(target, remote_path, version)
    ret.parent.mkdir(parents=True)
    return ret


def _get_local_path(target, remote_path, version=None):
    if version is None:
        version = _find_latest_version(target, remote_path=remote_path)
    return _build_local_path(target, remote_path, version)


def _find_latest_version(target, **kwargs):
    return _get_versions(target, kwargs)[-1]


def _match_metainfo(parent_path, params):
    meta_path = parent_path / META_YML
    if not meta_path.exists():
        return False
    with meta_path.open() as f:
        meta = yaml.safe_load(f)
    return all([k in meta and meta[k] == v for k, v in params.items()])


def _get_versions(target, *args, match=_match_metainfo):
    pdir = Path(WORKDIR).absolute() / target
    return sorted([
        x.name for x in pdir.glob('*')
        if x.is_dir() and match(x, *args)
    ])


def _generate_docker_compose(
    conf, extra_var_files, extra_vars, template='template/docker-compose.yml',
):
    ansible_arg = f'src={template} dest={conf}'
    env = dict([(x, os.environ[x]) for x in ENV_INHERIT])
    args = [
        'ansible', 'localhost', '-m', 'template', '-c', 'local',
        '-a', ansible_arg,
    ]
    for k, v in extra_vars.items():
        args.extend(['-e', f'{k}={v}'])
    for x in extra_var_files:
        args.extend(['-e', f'@{str(x)}'])
    ret = subprocess.run(args=args, env=env, capture_output=True)
    if ret.returncode != 0:
        logger.warn(ret.stdout)
    ret.check_returncode()


def _make_backup(conf, quiet=False):
    org = _to_backup(conf)
    if not quiet:
        logger.info(f'Copy {conf} {org}')
    shutil.copy2(conf, org)


def _to_backup(conf):
    return conf.parent / (conf.name + '.orig')


def _make_metainfo(local_path, **kwargs):
    params = copy.copy(kwargs)
    params['version'] = list(local_path.parts)[-2]
    with (local_path.parent / META_YML).open(mode='w') as f:
        yaml.safe_dump(params, stream=f, default_flow_style=False)


def _upload_file(target, src, dest):
    logger.info(f'Uploading {Path(dest).name} from {src} to "{target}"')
    ret = subprocess.run([
            'ansible', target, '-m', 'copy', '-a',
            f'src={src} dest={dest} backup=yes',
        ], capture_output=True, text=True)
    if ret.returncode != 0:
        logger.warn(ret.stdout)
    else:
        host_1 = ret.stdout.split("\n")[0].split()[0]
        logger.info(f'The upload to {host_1} has been completed')
    ret.check_returncode()


def _show_local_diff(local_path):
    _show_diff(_to_backup(local_path), local_path)


def _show_diff(path_a, path_b):
    lines_a = []
    lines_b = []
    with path_a.open() as f:
        lines_a = f.readlines()
    with path_b.open() as f:
        lines_b = f.readlines()
    diff = list(unified_diff(
        lines_a, lines_b, fromfile=path_a.name, tofile=path_b.name))
    sys.stdout.writelines(diff)
    return len(diff)
