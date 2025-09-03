#!/usr/bin/env python3
#
# Copyright (c) IBM Corp. 2025. All Rights Reserved.
# Project name: VPC File Storage Mount Helper
# This project is licensed under the MIT License, see LICENSE file in the root directory.

import os
import re
from datetime import datetime
from stunnel_config_get import StunnelConfigGet


class StunnelConfigCreate:
    WRITE_ERROR = "The following exception occurred on write to file - "

    def __init__(self, accept_ip, accept_port, connect_ip, connect_port, remote_path):
        self.accept_ip = accept_ip
        self.accept_port = accept_port
        self.connect_ip = connect_ip
        self.connect_port = connect_port
        self.remote_path = remote_path
        self.valid = False
        self.error = None
        self.filepath = self.filepath = (
            StunnelConfigGet.get_v2_config_file_from_remote_path(
                remote_path, connect_ip
            )
        )

    def get_stunnel_env(
        self,
        conf_file_name=StunnelConfigGet.CONFIG_FILE_NAME,
        key_name=StunnelConfigGet.STUNNEL_ENV_KEY,
    ):
        value = self.get_from_config_file(conf_file_name, key_name)
        if value is not None:
            value = value.lower()

        # Prod users dont need to set this.
        if (
            value == StunnelConfigGet.STUNNEL_ENV_DEV
            or value == StunnelConfigGet.STUNNEL_ENV_STAGE
        ):
            ret = value
        else:
            ret = StunnelConfigGet.STUNNEL_ENV_PROD

        return ret

    def get_trusted_ca_file(
        self,
        conf_file_name=StunnelConfigGet.CONFIG_FILE_NAME,
        key_name=StunnelConfigGet.CA_FILE_KEY,
    ):
        return self.get_from_config_file(conf_file_name, key_name)

    # Extract the value from the key value in conf file.
    def get_from_config_file(self, conf_file_name, key_name):
        value = None
        self.valid = True
        try:
            with open(conf_file_name, "r") as file:
                for line in file:
                    if line.lstrip().startswith(key_name):
                        value = line.split("=", 1)[1]
        except Exception as e:
            self.valid = False
            self.error = f"Could not read from {conf_file_name} due to exception {e}"

        if value is None:
            self.valid = False
        else:
            value = value.strip()

        return value

    def write_file(self):

        if (
            not self.accept_ip
            or not self.accept_port
            or not self.connect_port
            or not self.connect_ip
            or not self.remote_path
        ):
            self.error = f"Invalid args: accept_ip = '{self.accept_ip}' , accept_port = '{self.accept_port}' connect_port = '{self.connect_port}', connect_ip = '{self.connect_ip}', remote_path = '{self.remote_path}'"
            self.valid = False
            return -1

        self.valid = True
        ca_file = self.get_trusted_ca_file()
        if self.valid is False:
            self.error = f"get_trusted_ca_file failed. Please re-run install_stunnel.sh"
            return -1

        st_eyecatcher = StunnelConfigGet.get_sanitized_remote_path(
            self.remote_path, str(self.accept_port)
        )
        pid_file_name = os.path.join(
            StunnelConfigGet.get_pid_file_dir(), st_eyecatcher + ".pid"
        )

        stunnel_env = self.get_stunnel_env()
        log_file = os.path.join(
            StunnelConfigGet.STUNNEL_LOG_DIR, st_eyecatcher + ".log"
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
            "log = overwrite"
            "\n"
            f"output = {log_file}"
            "\n"
            "debug = 7"
            "\n"
            f"[{st_eyecatcher}]"
            "\n\n"
            "client = yes"
            "\n"
            f"{StunnelConfigGet.STUNNEL_ACCEPT} = {self.accept_ip}:{self.accept_port}"
            "\n"
            f"{StunnelConfigGet.STUNNEL_CONNECT} = {self.connect_ip}:{self.connect_port}"
            "\n"
            "verifyChain = yes"
            "\n"
            f"checkHost = {stunnel_env}.is-share.appdomain.cloud"
            "\n"
            f"cafile = {ca_file}"
            "\n"
        )
        filepath = self.filepath
        try:
            with open(filepath, "w") as file:
                file.write(buffer)
        except Exception as e:
            self.error = f"{StunnelConfigCreate.WRITE_ERROR} '{filepath}': {e}"
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
