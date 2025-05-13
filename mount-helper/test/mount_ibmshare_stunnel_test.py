# Copyright (c) IBM Corp. 2023. All Rights Reserved.
# Project name: VPC File Storage Mount Helper
# This project is licensed under the MIT License, see LICENSE file in the root directory.

from unittest.mock import MagicMock
from unittest import mock
import mount_ibmshare
import common
import unittest
import sys
from test_common import *
from stunnel_config_create import StunnelConfigCreate
from stunnel_config_get import StunnelConfigGet
from renew_certs import RenewCerts
from args_handler import ArgsHandler
import time
import subprocess
import find_free_stunnel_port

STUNNEL_COMMAND = "stunnel"


class TestMountIbmshare(unittest.TestCase):

    def create_conf_files(self):
        config_dir = tempfile.mkdtemp()
        stc = StunnelCommon()
        port_array = [10002, 10001, 10003, 1004, 10005, 10006, 10007, 10008]
        stc.create_conf_files(config_dir, port_array)
        return config_dir, len(port_array)

    def delete_conf_files_dir(self, config_dir):
        shutil.rmtree(config_dir)

    # Call stale cleanup when there no mounts.
    def test_cleanup_stale_conf_when_shares_not_mounted(self):

        config_dir, count = self.create_conf_files()
        mis = mount_ibmshare.MountIbmshare()
        mis.is_share_mounted = MagicMock(return_value=False)
        mis.RemoveFile = MagicMock(return_value=True)
        mis.kill_stunnel_pid = MagicMock(return_value=True)
        mis.cleanup_stale_conf(dirname=config_dir)

        # Kill pid and remove file should have been called as many times
        # as there are config files that are stale.
        self.assertEqual(mis.kill_stunnel_pid.call_count, count)
        self.assertEqual(mis.RemoveFile.call_count, count)
        self.assertEqual(mis.is_share_mounted.call_count, count)
        self.delete_conf_files_dir(config_dir)

    # Call stale cleanup when there are mounts.
    def test_cleanup_stale_conf_shares_mounted(self):
        config_dir, count = self.create_conf_files()
        mis = mount_ibmshare.MountIbmshare()
        mis.is_share_mounted = MagicMock(return_value=True)
        mis.RemoveFile = MagicMock(return_value=True)
        mis.kill_stunnel_pid = MagicMock(return_value=True)
        mis.cleanup_stale_conf(dirname=config_dir)

        # Kill pid and remove file should not have been called.
        # because we are faking that none are stale.
        self.assertEqual(mis.kill_stunnel_pid.call_count, 0)
        self.assertEqual(mis.RemoveFile.call_count, 0)
        self.assertEqual(mis.is_share_mounted.call_count, count)
        self.delete_conf_files_dir(config_dir)

    # Conf file in a requested dir
    def create_custom_conf_file(self, conf_dir, config_filename, pidval):
        pid_file_name = os.path.join(conf_dir, "ibmshare_C0FFEE.pid")
        with open(pid_file_name, "w") as out_file:
            out_file.write(pidval)
        buffer = (
            "########################################################################"
            "\n"
            "# Generated Stunnel config for mounting ibmshare for EIT. Do not edit. #"
            "\n"
            "# Time of creation : 2025-05-10 14:40:57.020503"
            "\n"
            "########################################################################"
            "\n"
            "# stunnel_identifier = /C0FFEE"
            "\n"
            f"pid = {pid_file_name}"
            "\n"
            "[ibmshare-C0FFEE]"
            "\n"
            "client = yes"
            "\n"
            "accept = 127.0.0.1:12001"
            "\n"
            "connect = 10.0.0.1:20049"
            "\n"
            "verifyPeer = yes"
            "\n"
            "verifyChain = yes"
            "\n"
            "cafile = allca.pem"
            "\n"
        )
        with open(config_filename, "w") as out_file:
            out_file.write(buffer)

    @mock.patch("os.kill")
    def test_kill_pid(self, os_kill_pid):

        call_count_before = os_kill_pid.call_count
        pid = "999999"
        self.kill_pid(pid)
        self.assertEqual(os_kill_pid.call_count, call_count_before + 1)

        pid_from_call = os_kill_pid.call_args_list[0][0][0]
        self.assertEqual(str(pid_from_call), pid)

        call_count_before = os_kill_pid.call_count
        pid = "888888888"
        self.kill_pid(pid)
        self.assertEqual(os_kill_pid.call_count, call_count_before + 1)
        call_count_before = os_kill_pid.call_count

        self.kill_pid("0")
        self.assertEqual(os_kill_pid.call_count, call_count_before)

        call_count_before = os_kill_pid.call_count
        self.kill_pid("99999", "BAD_EYE_CATHCER_KILL_PID_WILL_NOT_FIND_FILE")
        self.assertEqual(os_kill_pid.call_count, call_count_before)

    def kill_pid(self, pidval, eye_catcher="ibmshare_C0FFEE"):
        config_dir = tempfile.mkdtemp()
        config_filename = os.path.join(
            config_dir,
            eye_catcher + StunnelConfigGet.STUNNEL_CONF_EXT,
        )

        # Mock the DIR and PID dirs.
        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = config_dir
        self.create_custom_conf_file(config_dir, config_filename, pidval)

        mis = mount_ibmshare.MountIbmshare()
        mis.kill_stunnel_pid("/C0FFEE")
        self.delete_conf_files_dir(config_dir)

    @mock.patch("subprocess.run")
    def test_start_stunnel(self, subprocess_handle):
        config_dir = tempfile.mkdtemp()
        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = config_dir
        subprocess_handle.return_value.returncode = 0
        subprocess_handle.return_value = subprocess.CompletedProcess(
            args=["dummy", "dummy"], returncode=0
        )
        mis = mount_ibmshare.MountIbmshare()
        ret = mis.start_stunnel(10001, "10.10.1.1", "/C0FFEE")
        self.assertEqual(ret, True)
        self.assertEqual(1, subprocess_handle.call_count)
        self.assertEqual(subprocess_handle.call_args[0][0][0], STUNNEL_COMMAND)
        self.assertEqual(
            os.path.join(config_dir, "ibmshare_C0FFEE.conf"),
            subprocess_handle.call_args[0][0][1],
        )

        subprocess_handle.return_value = subprocess.CompletedProcess(
            args=["stunnel", "conf file not found"],
            returncode=99,
            stdout="",
            stderr="cannot find conf file",
        )
        ret = mis.start_stunnel(10001, "10.10.1.1", "/C0FFEE")
        self.assertEqual(ret, False)
        self.delete_conf_files_dir(config_dir)

    def setup_mocks(self, mis, is_share_mounted=False):

        mis.start_stunnel = MagicMock(return_value=True)
        mis.is_share_mounted = MagicMock(return_value=is_share_mounted)
        mis.run_stunnel_mount_command = MagicMock(return_value=True)
        mis.kill_stunnel_pid = MagicMock(return_value=True)

        dummy_success = DummySuccessObject()
        mis.RunCmd = MagicMock(return_value=dummy_success)

    @mock.patch("subprocess.run")
    @mock.patch.object(find_free_stunnel_port.FindFreeSTunnelPort, "get_free_port")
    def test_process_stunnel_mount(
        self, find_free_stunnel_port_handle, subprocess_handle
    ):
        config_dir = tempfile.mkdtemp()
        config_filename = self.get_generic_config_filename(config_dir)
        pidval = "99999999"
        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = config_dir
        find_free_stunnel_port_handle.return_value = 20001
        subprocess_handle.return_value = subprocess.CompletedProcess(
            args=["stunnel", "All good"], returncode=0, stdout="", stderr="All is well"
        )

        # Create config file.

        sys.argv = ["mount", "-o", "stunnel", "10.1.1.1:/C0FFEE", "/mnt"]
        ao = ArgsHandler()
        ao.parse()
        args = ArgsHandler.get_mount_args()
        mis = mount_ibmshare.MountIbmshare()

        # This section checks that start_stunnel and run_stunnel_mount_command are invoked
        # when there is no config file already present( from a previous setup)
        # and there is not already a mount of the volume that is being requested to be mounted.
        # Basically a fresh mount. Checks if both start_stunnel and run_stunnel_mount_command
        # get executed.

        # config_file_found = false is_share_mounted = false

        self.setup_mocks(mis)
        ret = mis.process_stunnel_mount(args)
        self.assertEqual(ret, True)

        self.assertEqual(mis.start_stunnel.call_count, 1)
        self.assertEqual(mis.run_stunnel_mount_command.call_count, 1)
        self.assertEqual(mis.kill_stunnel_pid.call_count, 0)

        # This is a case where a user has deleted their conf file
        # But the mount is present. Leave it alone.
        # config_file_found = False is_share_mounted = True

        self.setup_mocks(mis, is_share_mounted=True)
        ret = mis.process_stunnel_mount(args)

        self.assertEqual(mis.run_stunnel_mount_command.call_count, 0)
        self.assertEqual(mis.start_stunnel.call_count, 0)
        self.assertEqual(mis.kill_stunnel_pid.call_count, 0)

        # This section tests if a config_file for the share being mounted but the
        # actual mount is missing.
        # Basically, the user has umounted a once mounted share.
        # Test that the follwoing methods run once:
        # kill_stunnel_pid, start_stunnel and run_stunnel_mount_command
        # config_file_found = True is_share_mounted = false

        # Make config_file_found = True
        self.create_custom_conf_file(config_dir, config_filename, pidval)

        self.setup_mocks(mis)

        ret = mis.process_stunnel_mount(args)
        self.assertEqual(ret, True)

        self.assertEqual(mis.run_stunnel_mount_command.call_count, 1)
        self.assertEqual(mis.start_stunnel.call_count, 1)
        self.assertEqual(mis.kill_stunnel_pid.call_count, 1)

        # Config_file_found and share is mounted.
        # Do nothing.
        # config_file_found = True is_share_mounted = True

        self.setup_mocks(mis, is_share_mounted=True)

        ret = mis.process_stunnel_mount(args)
        self.assertEqual(ret, True)

        self.assertEqual(mis.run_stunnel_mount_command.call_count, 0)
        self.assertEqual(mis.start_stunnel.call_count, 0)
        self.assertEqual(mis.kill_stunnel_pid.call_count, 0)

        self.delete_conf_files_dir(config_dir)

    @mock.patch("os.remove")
    def test_run_stunnel_mount_command(self, os_remove_handle):
        mis = mount_ibmshare.MountIbmshare()
        dummy_success = DummySuccessObject()
        mis.RunCmd = MagicMock(return_value=dummy_success)
        mis.kill_stunnel_pid = MagicMock(return_value=True)
        ret = mis.run_stunnel_mount_command(10001, "/C0FFEE")
        self.assertEqual(mis.kill_stunnel_pid.call_count, 0)
        self.assertEqual(os_remove_handle.call_count, 0)

        config_dir = tempfile.mkdtemp()
        config_filename = self.get_generic_config_filename(config_dir)

        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = config_dir
        self.create_custom_conf_file(config_dir, config_filename, "9999999")
        dummy_error = DummyErrorObject()
        mis.RunCmd = MagicMock(return_value=dummy_error)
        mis.kill_stunnel_pid = MagicMock(return_value=True)
        ret = mis.run_stunnel_mount_command(10001, "/C0FFEE")
        self.assertEqual(mis.kill_stunnel_pid.call_count, 1)
        self.assertEqual(os_remove_handle.call_count, 1)
        self.delete_conf_files_dir(config_dir)

    def get_generic_config_filename(self, config_dir):
        return os.path.join(
            config_dir,
            "ibmshare_C0FFEE" + StunnelConfigGet.STUNNEL_CONF_EXT,
        )


class DummySuccessObject:
    def __init__(self):
        self.stderr = "stderr"
        self.stdout = "stdout"
        self.returncode = 0

    def get_error(self):
        return "dummy error"

    def is_error(self):
        return False


class DummyErrorObject:
    def __init__(self):
        self.stderr = "stderr"
        self.stdout = "stdout"
        self.returncode = 1

    def get_error(self):
        return "dummy error"

    def is_error(self):
        return True


if __name__ == "__main__":
    unittest.main()
