#!/usr/bin/env python3
#
# Copyright (c) IBM Corp. 2025. All Rights Reserved.
# Project name: VPC File Storage Mount Helper
# This project is licensed under the MIT License, see LICENSE file in the root directory.

import os
import re
from datetime import datetime


class StunnelConfigCreate:
    def __init__(self, accept_ip, accept_port, connect_ip, connect_port, remote_path):
        self.accept_ip = accept_ip
        self.accept_port = accept_port
        self.connect_ip = connect_ip
        self.connect_port = connect_port
        self.remote_path = remote_path
        self.filepath = None
        self.valid = False
        self.error = None
        self.filepath = StunnelConfigGet.get_config_file_from_remote_path(remote_path)
        self.write_file()

    def write_file(self):

        if (
            not self.accept_ip
            or not self.accept_port
            or not self.connect_port
            or not self.connect_ip
            or not self.remote_path
        ):
            self.valid = False
            return -1

        st_eyecatcher = StunnelConfigGet.get_sanitized_remote_path(self.remote_path)
        pid_file_name = os.path.join(
            StunnelConfigGet.get_pid_file_dir(), st_eyecatcher + ".pid"
        )

        buffer = (
            "########################################################################"
            "\n"
            "# Generated Stunnel config for mounting ibmshare for EIT. Do not edit. #"
            "\n"
            f"# Time of creation : {datetime.now()}"
            "\n"
            "########################################################################"
            "\n\n"
            f"# {StunnelConfigGet.STUNNEL_IDENTIFIER} = {self.remote_path}"
            "\n"
            f"pid = {pid_file_name}"
            "\n"
            f"[{st_eyecatcher}]"
            "\n\n"
            "client = yes"
            "\n"
            f"{StunnelConfigGet.STUNNEL_ACCEPT} = {self.accept_ip}:{self.accept_port}"
            "\n"
            f"{StunnelConfigGet.STUNNEL_CONNECT} = {self.connect_ip}:{self.connect_port}"
            "\n"
            "verifyPeer = yes"
            "\n"
            "verifyChain = yes"
            "\n"
            f"cafile = {StunnelConfigGet.TLS_CA_NAME}"
            "\n"
        )
        filepath = self.filepath
        try:
            with open(filepath, "w") as file:
                file.write(buffer)
        except Exception as e:
            self.error = (
                f"an exception on an operation occurred on file {filepath}: {e}"
            )
            self.valid = False
            return
        self.valid = True
        return

    def is_valid(self):
        return self.valid

    def get_error(self):
        return self.error

    def get_config_file(self):
        return self.filepath
