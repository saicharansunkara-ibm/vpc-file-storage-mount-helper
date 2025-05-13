import unittest
from stunnel_config_get import StunnelConfigGet
import tempfile
import os
from datetime import datetime
import shutil
from test_common import *

ACCEPT_IP = "127.0.0.1"
ACCEPT_PORT = 12001
CONNECT_IP = "10.0.0.1"
CONNECT_PORT = 20049
CA_CERT_NAME = "allca.pem"
STUNNEL_PID_FILE_DIR = "/var/run/stunnel4"
PID_FILE_BASENAME = "test_pid_file.pid"
REMOTE_PATH = "/C0FFEE"
PRE_GENERATED_CONFIG_FILE_NAME = "/etc/stunnel/ibmshare_C0FFEE.conf"
PRE_GENERATED_PID_FILE_NAME = "/var/run/stunnel4/ibmshare_C0FFEE.pid"
EYE_CATCHER = "ibmshare-C0FFEE"


class TestStunnelConfigGet(unittest.TestCase):

    def setUp(self):
        self.saved_stunnel_dir = StunnelConfigGet.STUNNEL_DIR_NAME
        self.saved_pid_file_dir = StunnelConfigGet.STUNNEL_PID_FILE_DIR

    def tearDown(self):
        StunnelConfigGet.STUNNEL_DIR_NAME = self.saved_stunnel_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = self.saved_pid_file_dir

    def test_get_pid_file_dir(self):
        result = StunnelConfigGet.get_pid_file_dir()
        self.assertEqual(result, STUNNEL_PID_FILE_DIR)

    def test_get_sanitized_remote_path(self):
        path = "a/b/c/d"
        sanitized_path = StunnelConfigGet.IBM_SHARE_SIG + "a_b_c_d"
        result = StunnelConfigGet.get_sanitized_remote_path(path)
        self.assertEqual(result, sanitized_path)

    def test_open_with_full_path_is_a_directory(self):
        is_a_dir = "/tmp"
        s = StunnelConfigGet()
        s.open_with_full_path(is_a_dir)

        self.assertEqual(s.is_found(), False)
        err = s.get_error()
        res = err.startswith(StunnelConfigGet.FILE_OPEN_GENERIC_ERR)
        self.assertEqual(res, True)

    def test_open_with_full_path_non_existant(self):
        non_existant_file = "/it/is/a/non-existant/file/for/sure.conf"
        s = StunnelConfigGet()
        s.open_with_full_path(non_existant_file)

        self.assertEqual(s.is_found(), False)
        err = s.get_error()
        res = err.startswith(StunnelConfigGet.FILE_NOT_FOUND_ERR)
        self.assertEqual(res, True)

    def test_get_config_file_from_remote_path(self):
        self.assertEqual(
            PRE_GENERATED_CONFIG_FILE_NAME,
            StunnelConfigGet.get_config_file_from_remote_path(REMOTE_PATH),
        )

    def create_conf_file(self, config_filename):
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
            "pid =  /var/run/stunnel4/ibmshare_C0FFEE.pid"
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

    def test_get_operations_on_conf_file(self):

        config_dir = tempfile.mkdtemp()
        config_filename = os.path.join(
            config_dir,
            EYE_CATCHER + StunnelConfigGet.STUNNEL_CONF_EXT,
        )

        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = config_dir

        self.create_conf_file(config_filename)

        s = StunnelConfigGet()
        s.open_with_full_path(config_filename)

        self.assertEqual(s.is_found(), True)
        self.assertEqual(s.get_error(), None)
        self.assertEqual(s.get_pid_file(), PRE_GENERATED_PID_FILE_NAME)
        self.assertEqual(s.get_config_file(), config_filename)
        self.assertEqual(s.get_full_mount_path(), REMOTE_PATH)
        shutil.rmtree(config_dir)
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = self.saved_pid_file_dir
        StunnelConfigGet.STUNNEL_DIR_NAME = self.saved_stunnel_dir


if __name__ == "__main__":
    unittest.main()
