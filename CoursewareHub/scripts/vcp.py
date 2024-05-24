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

