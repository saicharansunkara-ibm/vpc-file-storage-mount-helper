#!/usr/bin/env python3
#
# Copyright (c) IBM Corp. 2025. All Rights Reserved.
# Project name: VPC File Storage Mount Helper
# This project is licensed under the MIT License, see LICENSE file in the root directory.

import os
import re
import socket
from stunnel_config_get import StunnelConfigGet


class FindFreeSTunnelPort:
    START_PORT = 10001
    END_PORT = 20000

    def __init__(self, host):
        self.CONF_FILE_EXT = StunnelConfigGet.STUNNEL_CONF_EXT
        self.host = host

    def is_port_unused(self, host, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return True
        except socket.error:
            return False

    def get_free_port(self, conf_dir=StunnelConfigGet.STUNNEL_DIR_NAME):
        ports = self.get_ports_from_conf_files(conf_dir)

        for port in range(self.START_PORT, self.END_PORT):
            if port not in ports and self.is_port_unused(self.host, port):
                return port
        return -1

    def get_ports_from_conf_files(self, conf_dir=StunnelConfigGet.STUNNEL_DIR_NAME):

        ports = []
        pattern = re.compile(
            # Sample: 127.0.0.1:10001
            rf"\s*{StunnelConfigGet.STUNNEL_ACCEPT}\s*=\s*((\d{{1,3}}\.){{3}}\d{{1,3}}):(\d+)"
        )

        for filename in os.listdir(conf_dir):
            file_path = os.path.join(conf_dir, filename)

            if (
                os.path.isfile(file_path)
                # Not restricting it just to ibmshare conf files.
                and file_path.endswith(StunnelConfigGet.STUNNEL_CONF_EXT)
            ):
                with open(file_path, "r") as file:
                    for line in file:

                        match = pattern.search(line)
                        if match:
                            ports.append(int(match.group(3)))
                            break

        return ports
