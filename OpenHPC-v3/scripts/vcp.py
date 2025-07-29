from contextlib import redirect_stdout
from io import StringIO
from typing import Any

import yaml
from vcpsdk.vcpsdk import VcpSDK


def vcp_info(vcp: VcpSDK) -> dict[str, Any]:
    with redirect_stdout(StringIO()) as f:
        vcp.version()
    return yaml.safe_load(f.getvalue())


def vc_controller_version(vcp: VcpSDK) -> str:
    info = vcp_info(vcp)
    return info["vc_controller"]["vc_controller"]


def _version_to_tuple(version: str) -> tuple[int, ...]:
    """
    Convert a version string to a tuple of integers.
    Example: "1.2.3+xxxx" -> (1, 2, 3)
    """
    core_version = version.split("+")[0]  # Remove any suffix like "+20250401"
    return tuple(int(part) for part in core_version.split("."))


def has_minimum_vcc_version(vcp: VcpSDK, version: str) -> bool:
    """
    Check if the current VC Controller version is greater than or equal to the specified version.
    """
    current_version = vc_controller_version(vcp)
    return _version_to_tuple(current_version) >= _version_to_tuple(version)


def check_vcc_version(vcp: VcpSDK, version: str) -> None:
    """
    Check if the VC Controller version meets the minimum required version.
    Raises an error if the version is not sufficient.
    """
    if not has_minimum_vcc_version(vcp, version):
        current = vc_controller_version(vcp)
        msg = (
            f"VC Controller version {current} is lower than the required minimum version {version}."
        )
        raise RuntimeError(msg)

