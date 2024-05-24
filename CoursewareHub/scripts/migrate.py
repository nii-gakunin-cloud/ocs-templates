import random
from datetime import datetime as dt
from logging import INFO, basicConfig, getLogger
from pathlib import Path

from group import GROUP_VARS_DIR, load_group_vars, store_group_vars

logger = getLogger(__name__)
basicConfig(level=INFO, style="{")


def migrate_group_vars(target_group):
    gvars = load_group_vars(target_group)
    if "registry_pass" in gvars:
        logger.info(
            '"{target_group}" does nothing as it has already been migrated.',
            target_group=target_group,
        )
        return
    backup_group_vars(target_group)
    new_gvars = migrate_202309_gvars(gvars)
    store_group_vars(target_group, new_gvars)


def backup_group_vars(target_group):
    group_vars_path = Path(GROUP_VARS_DIR, target_group)
    if group_vars_path.exists():
        ts = dt.strftime(dt.now(), "%Y%m%d%H%M%S")
        group_vars_path.rename(group_vars_path.parent / f".{group_vars_path.name}.{ts}")
        logger.info(
            '".{target_group}.{ts}" as a backup for "{target_group}".',
            target_group=target_group,
            ts=ts,
        )


def migrate_202309_gvars(old_gvars):
    unchanged_keys = [
        "cousewarehub_backend",
        "db_name",
        "db_user",
        "disk_unit_group",
        "docker_address_pool",
        "manager_disk_size",
        "manager_flavor",
        "master_fqdn",
        "nfs_flavor",
        "nfs_ipaddress",
        "nfs_mac_address",
        "nfs_root_disk_size",
        "nfs_target",
        "rsc_yml",
        "ssh_private_key_path",
        "ssh_public_key_path",
        "ugroup_name",
        "vc_nfs_disk_size",
        "vc_provider",
        "vc_mac_address",
        "worker_disk_size",
        "worker_flavor",
        "worker_nodes",
        "worker_ipaddresses",
        "worker_mac_addresses",
        "auth_fqdn",
        "cg_groups",
        "cg_fqdn",
        "path_docker_cli",
        "power_ctl_dir",
        "power_ctl_schedule",
    ]
    gvars = {k: v for k, v in old_gvars.items() if k in unchanged_keys}
    cron_secret = "".join([random.choice("0123456789abcdef") for _ in range(32)])
    registry_pass = "".join([random.choice("0123456789abcdef") for _ in range(32)])
    gvars.update(
        {
            "db_pass": old_gvars["db_password"],
            "manager_ipaddress": old_gvars["vc_ipaddress"],
            "master_ip": old_gvars["vc_ipaddress"],
            "jupyterhub_singleuser_default_url": "/tree",
            "cron_secret": cron_secret,
            "registry_pass": registry_pass,
            "jupyterhub_image": "niicloudoperation/coursewarehub-jupyterhub:master",
            "auth_proxy_image": "niicloudoperation/coursewarehub-auth-proxy:master",
            "singleuser_image": "niicloudoperation/notebook",
            "lti_config": old_gvars.get("lti", {}),
            "migration": True,
        }
    )
    jupyterhub_params = old_gvars["jupyterhub_params"]
    jupyterhub_envs = [
        "CULL_SERVER",
        "CULL_SERVER_EVERY",
        "CULL_SERVER_IDLE_TIMEOUT",
        "CULL_SERVER_MAX_AGE",
        "SPAWNER_HTTP_TIMEOUT",
        "SPAWNER_RESTART_MAX_ATTEMPTSA",
        "SPAWNER_START_TIMEOUT",
        "CONCURRENT_SPAWN_LIMIT",
    ]
    for name in jupyterhub_envs:
        if name in jupyterhub_params:
            gvars[name.lower()] = jupyterhub_params[name]
    test_federation = "https://sptest.cg.gakunin.jp/"
    if any(x.startswith(test_federation) for x in gvars.get("cg_groups", [])):
        gvars["enable_test_federation"] = True
    if "federation" in old_gvars:
        gvars["enable_federation"] = True
        gvars["enable_test_federation"] = old_gvars["federation"] == "test"
    if "ds_fqdn" in old_gvars:
        gvars["gakunin_ds_hostname"] = old_gvars["ds_fqdn"]

    return gvars
