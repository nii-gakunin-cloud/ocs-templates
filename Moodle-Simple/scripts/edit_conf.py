import os
import shutil
import subprocess
import sys
from datetime import datetime
from difflib import unified_diff
from logging import INFO, basicConfig, getLogger
from pathlib import Path

import yaml
from IPython.core.display import HTML
from notebook import notebookapp

WORKDIR = "edit"
META_YML = ".vcp-meta.yml"
MOODLE_DIR = "/srv/moodle"
CONF_RELATIVE = "/etc"
ENV_INHERIT = ["VAULT_ADDR", "VAULT_TOKEN", "PATH", "REQUESTS_CA_BUNDLE"]
logger = getLogger(__name__)
basicConfig(level=INFO, format="%(message)s")


def generate_local_path(host, conf_path, version=None):
    ret = Path(WORKDIR).absolute() / host
    if version is None:
        ret /= datetime.now().strftime("%Y%m%d%H%M%S%f")
    else:
        ret /= version
    ret /= Path(conf_path).name
    return ret


def generate_remote_path(container, conf_path, relative_to=CONF_RELATIVE):
    return (
        Path(MOODLE_DIR) / container / "conf" / Path(conf_path).relative_to(relative_to)
    )


def get_local_path(host, container, conf_path, version=None):
    if version is None:
        version = find_latest_version(host, container, conf_path)
    return generate_local_path(host, conf_path, version)


def _match_metainfo(parent, container, conf_path):
    p = parent / META_YML
    if not p.exists():
        return False
    with p.open() as f:
        params = yaml.safe_load(f)
    return (
        isinstance(params, dict)
        and "container" in params
        and "container_path" in params
        and params["container"] == container
        and params["container_path"] == conf_path
    )


def _match_metainfo_by_remote_path(parent, remote_path):
    p = parent / META_YML
    if not p.exists():
        return False
    with p.open() as f:
        params = yaml.safe_load(f)
    return (
        isinstance(params, dict)
        and "remote_path" in params
        and params["remote_path"] == remote_path
    )


def get_versions(host, *args, match=_match_metainfo):
    pdir = Path(WORKDIR).absolute() / host
    return sorted([x.name for x in pdir.glob("*") if x.is_dir() and match(x, *args)])


def find_latest_version(host, container, conf_path):
    return get_versions(host, container, conf_path)[-1]


def find_latest_version_by_remote_path(host, remote_path):
    return get_versions(host, remote_path, match=_match_metainfo_by_remote_path)[-1]


def download_file(host, remote_path, conf_path=None):
    if conf_path is None:
        conf_path = Path(remote_path).name
    dest = generate_local_path(host, conf_path)
    ansible_arg = f"src={remote_path} dest={dest} flat=yes"
    out = subprocess.check_output(["ansible", host, "-m", "fetch", "-a", ansible_arg])
    host_1 = out.decode("utf-8").split("\n")[0].split()[0]
    logger.info(f"Downloading {remote_path} from {host_1} to {dest}")
    return dest


def download_conf_file(host, container, conf_path, relative_to=CONF_RELATIVE):
    src = generate_remote_path(container, conf_path, relative_to)
    return download_file(host, src, conf_path)


def create_conf_file(host, conf_path):
    dest = generate_local_path(host, conf_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.touch()
    return dest


def _to_backup(conf):
    return conf.parent / (conf.name + ".orig")


def make_backup(conf, quiet=False):
    org = _to_backup(conf)
    if not quiet:
        logger.info(f"Copy {conf} {org}")
    shutil.copy2(conf, org)


def make_metainfo(local_path, container, conf_path, relative_to=CONF_RELATIVE):
    params = {
        "container": container,
        "container_path": conf_path,
        "remote_path": str(generate_remote_path(container, conf_path, relative_to)),
        "version": list(local_path.parts)[-2],
    }
    with (local_path.parent / META_YML).open(mode="w") as f:
        yaml.safe_dump(params, stream=f, default_flow_style=False)


def make_simple_metainfo(local_path, remote_path):
    params = {
        "remote_path": remote_path,
        "version": list(local_path.parts)[-2],
    }
    with (local_path.parent / META_YML).open(mode="w") as f:
        yaml.safe_dump(params, stream=f, default_flow_style=False)


def generate_edit_link(conf):
    servers = list(notebookapp.list_running_servers())
    if len(servers) > 0:
        nb_conf = servers[0]
        p = (
            Path(nb_conf["base_url"])
            / "edit"
            / conf.absolute().relative_to(nb_conf["notebook_dir"])
        )
    else:
        p = conf.absolute()
    return HTML(f'<a href={p} target="_blank">{p.name}</a>')


def show_diff(path_a, path_b):
    lines_a = []
    lines_b = []
    with path_a.open() as f:
        lines_a = f.readlines()
    with path_b.open() as f:
        lines_b = f.readlines()
    diff = list(
        unified_diff(lines_a, lines_b, fromfile=path_a.name, tofile=path_b.name)
    )
    sys.stdout.writelines(diff)
    return len(diff)


def upload_conf_file(src, host, container, conf_path, relative_to=CONF_RELATIVE):
    dest = generate_remote_path(container, conf_path, relative_to)
    ansible_arg = f"mkdir -p {dest.parent}"
    subprocess.run(["ansible", host, "-a", ansible_arg])
    ansible_arg = f"dest={dest} src={src} backup=yes"
    out = subprocess.check_output(
        ["ansible", host, "-m", "copy", "-b", "-a", ansible_arg]
    )
    host_1 = out.decode("utf-8").split("\n")[0].split()[0]
    logger.info(f"Uploading {dest} from {src} to {host_1}")


def restart_container(host, container):
    cmd = f"chdir={MOODLE_DIR} docker compose restart {container}"
    logger.info(f"Restart container {container}")
    subprocess.check_call(["ansible", host, "-a", cmd])


def fetch_conf(host, container, conf_path, relative_to=CONF_RELATIVE, create=False):
    local_path = download_conf_file(host, container, conf_path, relative_to)
    make_backup(local_path)
    make_metainfo(local_path, container, conf_path, relative_to)
    return generate_edit_link(local_path)


def create_conf(host, container, conf_path, relative_to=CONF_RELATIVE, create=False):
    local_path = create_conf_file(host, conf_path)
    make_backup(local_path, quiet=True)
    make_metainfo(local_path, container, conf_path, relative_to)
    return generate_edit_link(local_path)


def apply_conf(
    host, container, conf_path, relative_to=CONF_RELATIVE, version=None, restart=True
):
    show_local_conf_diff(host, container, conf_path, version)
    local_path = get_local_path(host, container, conf_path, version)
    upload_conf_file(local_path, host, container, conf_path, relative_to)
    if restart:
        restart_container(host, container)


def revert_conf(host, container, conf_path, relative_to=CONF_RELATIVE, version=None):
    local_path = get_local_path(host, container, conf_path, version)
    backup_path = _to_backup(local_path)
    show_diff(local_path, backup_path)
    upload_conf_file(backup_path, host, container, conf_path, relative_to)
    restart_container(host, container)
    local_path.rename(local_path.parent / (local_path.name + ".revert"))


def show_local_conf(
    host, container, conf_path, relative_to=CONF_RELATIVE, version=None
):
    conf = get_local_path(host, container, conf_path, version)
    with conf.open() as f:
        print(f.read())


def edit_local_conf(
    host, container, conf_path, relative_to=CONF_RELATIVE, version=None
):
    conf = get_local_path(host, container, conf_path, version)
    return generate_edit_link(conf)


def show_local_conf_diff(host, container, conf_path, version=None):
    local_path = get_local_path(host, container, conf_path, version)
    show_diff(_to_backup(local_path), local_path)


def generate_docker_compose(host, conf_path, extra_vars, extra_vars_file):
    template = "template/docker/compose/compose.yaml"
    ansible_arg = f"src={template} dest={conf_path.parent}/"
    env = dict([(x, os.environ[x]) for x in ENV_INHERIT])
    args = ["ansible", host, "-m", "template", "-c", "local", "-a", ansible_arg]
    for k, v in extra_vars.items():
        args.extend(["-e", f"{k}={v}"])
    for x in extra_vars_file:
        args.extend(["-e", f"@{str(x)}"])
    subprocess.run(args=args, env=env, check=True)


def fetch_host_conf(host, conf_path):
    local_path = download_file(host, conf_path)
    make_backup(local_path)
    make_simple_metainfo(local_path, conf_path)
    return generate_edit_link(local_path)


def fetch_docker_compose(host):
    remote_path = MOODLE_DIR + "/compose.yaml"
    return fetch_host_conf(host, remote_path)


def get_local_host_conf(host, conf_path, version=None):
    if version is None:
        version = find_latest_version_by_remote_path(host, conf_path)
    return Path(WORKDIR).absolute() / host / version / Path(conf_path).name


def get_local_docker_compose(host, version=None):
    remote_path = MOODLE_DIR + "/compose.yaml"
    return get_local_host_conf(host, remote_path, version)


def show_local_host_conf_diff(host, conf_path, version=None):
    local_path = get_local_host_conf(host, conf_path, version)
    backup_path = _to_backup(local_path)
    show_diff(backup_path, local_path)


def show_local_docker_compose_diff(host, version=None):
    remote_path = MOODLE_DIR + "/compose.yaml"
    show_local_host_conf_diff(host, remote_path, version)


def _upload_host_conf(host, local_path, remote_path):
    ansible_arg = f"dest={remote_path} src={local_path} backup=yes"
    out = subprocess.check_output(
        ["ansible", host, "-m", "copy", "-b", "-a", ansible_arg]
    )
    host_1 = out.decode("utf-8").split("\n")[0].split()[0]
    logger.info(f"Uploading {remote_path} from {local_path} to {host_1}")


def upload_docker_compose(host, local_path, apply=True):
    remote_path = MOODLE_DIR + "/compose.yaml"
    _upload_host_conf(host, local_path, remote_path)
    if not apply:
        return
    ansible_arg = f"chdir={MOODLE_DIR} docker compose up -d --remove-orphans"
    args = ["ansible", host, "-a", ansible_arg]
    logger.info("Apply the changes in compose.yaml.")
    subprocess.run(args=args, check=True)


def upload_host_conf(host, conf_path, version=None):
    local_path = get_local_host_conf(host, conf_path, version)
    backup_path = _to_backup(local_path)
    show_diff(backup_path, local_path)
    _upload_host_conf(host, local_path, conf_path)


def apply_docker_compose(host, version=None):
    local_path = get_local_docker_compose(host, version)
    backup_path = _to_backup(local_path)
    show_diff(backup_path, local_path)
    upload_docker_compose(host, local_path)


def revert_host_conf(host, conf_path, version=None):
    local_path = get_local_host_conf(host, conf_path, version)
    backup_path = _to_backup(local_path)
    show_diff(local_path, backup_path)
    _upload_host_conf(host, backup_path, conf_path)
    local_path.rename(local_path.parent / (local_path.name + ".revert"))


def revert_docker_compose(host, version=None):
    local_path = get_local_docker_compose(host, version)
    backup_path = _to_backup(local_path)
    show_diff(local_path, backup_path)
    upload_docker_compose(host, backup_path)
    local_path.rename(local_path.parent / (local_path.name + ".revert"))


def generate_proxy_conf(host, conf_path, extra_vars):
    template = "template/docker/compose/moodle-proxy.conf.template"
    ansible_arg = f"src={template} dest={conf_path.parent}/moodle-proxy.conf"

    env = dict([(x, os.environ[x]) for x in ENV_INHERIT])
    args = ["ansible", host, "-m", "template", "-c", "local", "-a", ansible_arg]
    for k, v in extra_vars.items():
        args.extend(["-e", f"{k}={v}"])
    subprocess.run(args=args, env=env, check=True)


def update_proxy_conf(host, extra_vars={}):
    conf_path = Path("/usr/local/apache2/conf/moodle-proxy.conf")
    container = "proxy"
    link = fetch_conf(host, container, str(conf_path), str(conf_path.parent))
    version = find_latest_version(host, container, str(conf_path))
    local_path = generate_local_path(host, conf_path, version)
    generate_proxy_conf(host, local_path, extra_vars)
    show_local_conf_diff(host, container, conf_path, version)
    return link


def apply_proxy_conf(host, version=None, restart=True):
    conf_path = Path("/usr/local/apache2/conf/moodle-proxy.conf")
    apply_conf(host, "proxy", str(conf_path), str(conf_path.parent), version, restart)
