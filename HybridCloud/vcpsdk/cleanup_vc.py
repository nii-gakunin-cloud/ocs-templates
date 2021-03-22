#!/usr/bin/env python3

import os
from vcpsdk import vcpsdk

vcp_accesskey = os.environ['VCP_ACCESSKEY']
unit_group_name = os.environ['VC_NAME']

sdk = vcpsdk.VcpSDK(vcc_access_token=vcp_accesskey, verbose=10)
ugroup = sdk.get_ugroup(ugroup_name=unit_group_name)
if ugroup:
    ugroup.cleanup()
