import shutil
import sys
from datetime import datetime, timezone
from difflib import unified_diff
from logging import INFO, basicConfig, getLogger
from pathlib import Path
from subprocess import PIPE, run

import yaml
from IPython.core.display import HTML
from jupyter_server import serverapp

WORKDIR = "edit"
META_YML = ".vcp-meta.yml"
logger = getLogger(__name__)
basicConfig(level=INFO, format="%(message)s")


def fetch_conf(target_path, ugroup, unit):
    local_path = download_conf_file(target_path, ugroup, unit)
    make_backup(local_path)
    return generate_edit_link(local_path)


def show_local_conf_diff(target_path, ugroup, unit=None, version=None):
    local_path = get_local_path(target_path, ugroup, unit, version)
    show_diff(_to_backup(local_path), local_path)


def upload_conf(target_path, ugroup, unit=None, version=None):
    show_local_conf_diff(target_path, ugroup, unit, version)
    local_path = get_local_path(target_path, ugroup, unit, version)
    upload_conf_file(local_path, target_path, ugroup, unit)


def download_conf_file(target_path, ugroup, unit):
    dest = generate_local_path(target_path, ugroup)
    ansible_arg = f"src={target_path} dest={dest} flat=yes"
    group = f"{ugroup}_{unit}"
    args = ["ansible", group, "-b", "-m", "fetch", "-a", ansible_arg]
    output = run(
        args,
        check=True,
        stdout=PIPE,
        text=True,
    ).stdout
    host_1 = output.split("\n", maxsplit=1)[0].split()[0]

    logger.info("Downloading %s from %s to %s", target_path, host_1, dest)
    make_metainfo(dest, target_path, unit, host_1)
    return dest


def _output_to_hosts(output):
    return ",".join(sorted([line.split()[0] for line in output.split("\n") if line.find("CHANGED =>") >= 0]))


def upload_conf_file(local_path, target_path, ugroup, unit=None):
    ansible_arg = f"dest={target_path} src={local_path} owner=no group=no perms=no"
    group = f"{ugroup}_{unit}" if unit is not None else ugroup
    args = ["ansible", group, "-b", "-m", "synchronize", "-a", ansible_arg]
    output = run(
        args,
        check=True,
        stdout=PIPE,
        text=True,
    ).stdout
    hosts = _output_to_hosts(output)
    logger.info("Uploading %s from %s to %s", target_path, local_path, hosts)


def generate_local_path(target_path, ugroup, version=None):
    ret = Path(WORKDIR).absolute() / ugroup
    if version is None:
        ret /= datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S%f")
    else:
        ret /= version
    ret /= Path(target_path).name
    return ret


def make_metainfo(local_path, target_path, unit, host):
    params = {
        "path": target_path,
        "unit": unit,
        "host": host,
        "version": list(local_path.parts)[-2],
    }
    with (local_path.parent / META_YML).open(mode="w") as f:
        yaml.safe_dump(params, stream=f, default_flow_style=False)


def make_backup(conf):
    org = _to_backup(conf)
    logger.info("Copy %s to %s", conf, org)
    shutil.copy2(conf, org)


def _to_backup(conf):
    return conf.parent / (conf.name + ".orig")


def generate_edit_link(conf):
    servers = list(serverapp.list_running_servers())
    if len(servers) == 0:
        return str(conf.absolute())
    nb_conf = servers[0]
    p = Path(nb_conf["base_url"]) / "edit" / conf.absolute().relative_to(nb_conf["root_dir"])
    return HTML(f'<a href={p} target="_blank">{p.name}</a>')


def get_local_path(target_path, ugroup, unit, version=None):
    if version is None:
        version = find_latest_version(target_path, ugroup, unit)
    return generate_local_path(target_path, ugroup, version)


def find_latest_version(target_path, ugroup, unit=None):
    return get_versions(target_path, ugroup, unit)[-1]


def get_versions(target_path, ugroup, unit=None):
    pdir = Path(WORKDIR).absolute() / ugroup
    return sorted([x.name for x in pdir.glob("*") if x.is_dir() and _match_metainfo(x, target_path, unit)])


def _match_metainfo(parent, target_path, unit=None):
    p = parent / META_YML
    if not p.exists():
        return False
    with p.open() as f:
        params = yaml.safe_load(f)
    return (
        isinstance(params, dict)
        and "path" in params
        and params["path"] == target_path
        and (unit is None or ("unit" in params and params["unit"] == unit))
    )


def show_diff(path_a, path_b):
    lines_a = []
    lines_b = []
    with path_a.open() as f:
        lines_a = f.readlines()
    with path_b.open() as f:
        lines_b = f.readlines()
    diff = list(unified_diff(lines_a, lines_b, fromfile=path_a.name, tofile=path_b.name))
    sys.stdout.writelines(diff)
    return len(diff)
