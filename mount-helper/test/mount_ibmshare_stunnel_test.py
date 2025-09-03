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
import stat
import subprocess
import find_free_stunnel_port
import logging
from unittest.mock import patch

STUNNEL_COMMAND = "stunnel"
FAKE_IP_ADDRESS = "100.100.100.100"
MOUNT_IP = "10.1.1.1"
MOUNT_PATH = "/C0FFEE"


class TestMountIbmshare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def setUp(self):
        self.saved_stunnel_dir = stunnel_config_get.StunnelConfigGet.STUNNEL_DIR_NAME
        self.saved_pid_file_dir = (
            stunnel_config_get.StunnelConfigGet.STUNNEL_PID_FILE_DIR
        )
        config_dir = tempfile.mkdtemp()
        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = config_dir
        self.config_dir = config_dir

    def tearDown(self):
        stunnel_config_get.StunnelConfigGet.STUNNEL_DIR_NAME = self.saved_stunnel_dir
        stunnel_config_get.StunnelConfigGet.STUNNEL_PID_FILE_DIR = (
            self.saved_pid_file_dir
        )
        self.delete_conf_files_dir(self.config_dir)

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
        mis.pid_from_file = MagicMock(return_value=999999999)
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
        mis.pid_from_file = MagicMock(return_value=999999999)
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
            f"connect = {MOUNT_IP}:20049"
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
        return config_filename

    @mock.patch("os.kill")
    def test_kill_pid(self, os_kill_pid):

        counter = 0
        for pid in ["999999", "88888", "100000"]:
            call_count_before = os_kill_pid.call_count
            self.kill_pid(pid)
            self.assertEqual(os_kill_pid.call_count, call_count_before + 1)
            pid_from_call = os_kill_pid.call_args_list[counter][0][0]
            counter += 1
            self.assertEqual(str(pid_from_call), pid)
            saved_pid = pid

        for pid in ["0", "-1", "xxxx", ""]:
            call_count_before = os_kill_pid.call_count
            self.kill_pid(pid)
            self.assertEqual(os_kill_pid.call_count, call_count_before)
            self.assertEqual(str(pid_from_call), saved_pid)

    def test_pid_from_file(self):
        config_file_name = os.path.join(
            self.config_dir,
            "ibmshare_C0FFEE" + StunnelConfigGet.STUNNEL_CONF_EXT,
        )
        pidval = "1000"
        conf_file = self.create_custom_conf_file(
            self.config_dir, config_file_name, pidval
        )
        st = StunnelConfigGet()
        st.parse_with_full_path(conf_file)
        mis = mount_ibmshare.MountIbmshare()
        ret = mis.pid_from_file(st.get_pid_file())
        self.assertEqual(str(ret), pidval)

        ret = mis.pid_from_file("non existant file")
        self.assertEqual(ret, None)

        pidval = "-1"
        conf_file = self.create_custom_conf_file(
            self.config_dir, config_file_name, pidval
        )
        ret = mis.pid_from_file(st.get_pid_file())
        self.assertEqual(ret, None)

    def kill_pid(self, pidval, eye_catcher="ibmshare_C0FFEE"):
        config_dir = tempfile.mkdtemp()
        config_filename = os.path.join(
            config_dir,
            eye_catcher + StunnelConfigGet.STUNNEL_CONF_EXT,
        )

        # Mock the DIR and PID dirs.
        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = config_dir
        conf_file = self.create_custom_conf_file(config_dir, config_filename, pidval)

        st = StunnelConfigGet()
        st.parse_with_full_path(conf_file)

        mis = mount_ibmshare.MountIbmshare()
        mis.kill_stunnel_pid(st)
        self.delete_conf_files_dir(config_dir)

    def fake_get_trusted_ca_file(self):
        return "/dev/null"

    @mock.patch("subprocess.run")
    def test_start_stunnel(self, subprocess_handle):
        with patch.object(
            StunnelConfigCreate,
            "get_trusted_ca_file",
            new=self.fake_get_trusted_ca_file,
        ):
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
                os.path.join(self.config_dir, "ibmshare_C0FFEE_10-10-1-1.conf"),
                subprocess_handle.call_args[0][0][1],
            )

            subprocess_handle.return_value = subprocess.CompletedProcess(
                args=["stunnel", "This_is_an_Incorrect_file_name.conf"],
                returncode=99,
                stdout="",
                stderr="This error was intentionally simulated in a unit test".encode(
                    "utf-8"
                ),
            )
            ret = mis.start_stunnel(10001, "10.10.1.1", "/C0FFEE")
            self.assertEqual(ret, False)

    def setup_mocks(self, mis, is_share_mounted=False):

        mis.start_stunnel = MagicMock(return_value=True)
        mis.is_share_mounted = MagicMock(return_value=is_share_mounted)
        mis.run_stunnel_mount_command = MagicMock(return_value=True)
        mis.kill_stunnel_pid = MagicMock(return_value=True)

        mis.configure_default_umask = MagicMock(return_value=True)
        dummy_success = DummySuccessObject()
        mis.RunCmd = MagicMock(return_value=dummy_success)

    @mock.patch("subprocess.run")
    @mock.patch.object(find_free_stunnel_port.FindFreeSTunnelPort, "get_free_port")
    def test_process_stunnel_mount(
        self, find_free_stunnel_port_handle, subprocess_handle
    ):
        config_filename = self.get_generic_config_filename(self.config_dir)
        pidval = "99999999"
        find_free_stunnel_port_handle.return_value = 20001
        subprocess_handle.return_value = subprocess.CompletedProcess(
            args=["stunnel", "All good"],
            returncode=0,
            stdout="no error".encode("utf-8"),
            stderr="All is well",
        )

        # Create config file.

        sys.argv = ["mount", "-o", "stunnel", f"{MOUNT_IP}:{MOUNT_PATH}", "/mnt"]
        ao = ArgsHandler()
        ao.parse()
        args = ArgsHandler.get_mount_args()
        mis = mount_ibmshare.MountIbmshare()

        # test that we fail if we cannot set the required umask.
        mis.configure_default_umask = MagicMock(return_value=False)
        ret = mis.process_stunnel_mount(args)
        self.assertEqual(ret, False)

        # test that we fail if we cannot find a free port for stunnel
        self.setup_mocks(mis)
        saved_port = find_free_stunnel_port_handle.return_value
        find_free_stunnel_port_handle.return_value = -1
        self.assertEqual(ret, False)
        ret = mis.process_stunnel_mount(args)
        self.assertEqual(ret, False)

        # Undo incorrect setting.
        find_free_stunnel_port_handle.return_value = saved_port

        saved_config_dir = StunnelConfigGet.STUNNEL_PID_FILE_DIR
        file_path = os.path.join(self.config_dir, "a_simple_file_for_testing")

        # Set a file as a dir to simulate an error. And set it back.
        self.setup_mocks(mis)
        saved_pid_file_dir = StunnelConfigGet.get_pid_file_dir
        StunnelConfigGet.get_pid_file_dir = MagicMock(return_value=file_path)
        with open(file_path, "w"):
            pass

        ret = mis.process_stunnel_mount(args)
        self.assertEqual(ret, False)
        StunnelConfigGet.get_pid_file_dir = saved_pid_file_dir

        # There is another test possible here. To make the pid_file_dir not writable.
        # If the UID is root, it is always writable and the test fails. So skipping.

        # This section checks that start_stunnel and run_stunnel_mount_command are invoked
        # when there is no config file already present( from a previous setup)
        # and there is not already a mount of the volume that is being requested to be mounted.
        # Basically a fresh mount. Checks if both start_stunnel and run_stunnel_mount_command
        # get executed.

        # config_file_found = false is_share_mounted = false

        self.setup_mocks(mis)
        ret = mis.process_stunnel_mount(args)
        self.assertEqual(ret, True)

        self.assertEqual(mis.run_stunnel_mount_command.call_count, 1)
        self.assertEqual(mis.start_stunnel.call_count, 1)
        self.assertEqual(mis.kill_stunnel_pid.call_count, 0)

        # Config_file_found and share is mounted.
        # Even if it is mounted, go head and make the mount call.
        # If same mount point, it is ignored( by the os), but a different
        # mount point still gets mounted.

        # Create the conf file.
        sc = StunnelConfigCreate("127.0.0.1", saved_port, MOUNT_IP, 20049, MOUNT_PATH)
        sc.get_trusted_ca_file = MagicMock(return_value="")
        sc.write_file()

        self.setup_mocks(mis)
        self.setup_mocks(mis, is_share_mounted=True)

        ret = mis.process_stunnel_mount(args)
        self.assertEqual(ret, True)

        # Conf file is found.  So only call mounter

        self.assertEqual(mis.run_stunnel_mount_command.call_count, 1)

        self.assertEqual(mis.start_stunnel.call_count, 0)
        self.assertEqual(mis.kill_stunnel_pid.call_count, 0)

    @mock.patch("os.remove")
    def test_run_stunnel_mount_command(self, os_remove_handle):
        mis = mount_ibmshare.MountIbmshare()
        dummy_success = DummySuccessObject()
        mis.RunCmd = MagicMock(return_value=dummy_success)
        mis.kill_stunnel_pid = MagicMock(return_value=True)
        ret = mis.run_stunnel_mount_command(10001, "/C0FFEE", FAKE_IP_ADDRESS)
        self.assertEqual(mis.kill_stunnel_pid.call_count, 0)
        self.assertEqual(os_remove_handle.call_count, 0)

        config_filename = self.get_generic_config_filename(self.config_dir)

        self.create_custom_conf_file(self.config_dir, config_filename, "9999999")

        dummy_error = DummyErrorObject()
        mis.RunCmd = MagicMock(return_value=dummy_error)
        mis.kill_stunnel_pid = MagicMock(return_value=True)
        ret = mis.run_stunnel_mount_command(10001, "/C0FFEE", FAKE_IP_ADDRESS, True)
        self.assertEqual(mis.kill_stunnel_pid.call_count, 1)
        self.assertEqual(os_remove_handle.call_count, 1)

    def get_generic_config_filename(self, config_dir):
        return os.path.join(
            config_dir,
            "ibmshare_C0FFEE" + StunnelConfigGet.STUNNEL_CONF_EXT,
        )

    def test_configure_default_umask(self):

        # Save mask to restore after running test.
        saved_umask = os.umask(0)

        test_umasks = [0, 0o22, 0o44, 0o55, 0o66, 0o77]

        for mask in test_umasks:

            mis = mount_ibmshare.MountIbmshare()
            os.umask(mask)
            # Umask should change due to the method invoked.
            mis.configure_default_umask()
            result = self.check_temp_file_permissions(
                mount_ibmshare.MountIbmshare.DESIRED_DEFAULT_UMASK
            )
            self.assertEqual(result, True)

        # Umask remains at whatever it was set to.
        for mask in test_umasks:
            os.umask(mask)
            result = self.check_temp_file_permissions(mask)
            self.assertEqual(result, True)

        # Finally restore to original.
        os.umask(saved_umask)

    def check_temp_file_permissions(self, desired_umask):
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, "testfile.txt")
        with open(file_path, "w") as temp_file_name:
            file_stat = os.stat(file_path)
            file_permissions = stat.S_IMODE(file_stat.st_mode)

            expected_permissions = 0o666 & ~desired_umask
            os.remove(file_path)
        os.rmdir(temp_dir)
        return file_permissions == expected_permissions


class DummySuccessObject:
    def __init__(self):
        self.stdout = "stdout".encode("utf-8")
        self.stderr = "stderr".encode("utf-8")
        self.returncode = 0

    def get_error(self):
        return ""

    def is_error(self):
        return False


class DummyErrorObject:
    def __init__(self):
        self.stderr = "stderr".encode("utf-8")
        self.stdout = "stdout".encode("utf-8")
        self.returncode = 1

    def get_error(self):
        return "dummy error"

    def is_error(self):
        return True


if __name__ == "__main__":
    unittest.main()
