#!/usr/bin/env python3
#
# Copyright (c) IBM Corp. 2025. All Rights Reserved.
# Project name: VPC File Storage Mount Helper
# This project is licensed under the MIT License, see LICENSE file in the root directory.

import os
import re
from common import *
from stunnel_config_get import *
from mount_ibmshare import MountIbmshare


class CleanUpStaleConf(MountIbmshare):
    def __init__(self):
        pass

    def doit(self):
        for filename in os.listdir(StunnelConfigGet.STUNNEL_DIR_NAME):
            if (
                filename.endswith(tunnelConfigGet.STUNNEL_CONF_EXT)
                and StunnelConfigGet.IBM_SHARE_SIG in filename
            ):
                st = StunnelConfigGet()
                full_file_name = os.path.join(StunnelConfigGet.STUNNEL_DIR_NAME, filename)
                st.open_with_full_path(full_file_name)
                if st.is_found():
                    mount_path = st.get_full_mount_path()
                    if not self.is_share_mounted(LOOPBACK_ADDRESS, mount_path):
                        self.kill_stunnel_pid(mount_path)
                        self.RemoveFile(full_file_name)
