import unittest
from stunnel_config_create import StunnelConfigCreate
from stunnel_config_get import StunnelConfigGet
import tempfile
import os
from datetime import datetime
import shutil
import filecmp
from unittest.mock import MagicMock
import tempfile
from test_common import read_file, write_file, print_file_contents

ACCEPT_IP = "127.0.0.1"
ACCEPT_PORT = 10001
CONNECT_IP = "10.240.64.83"
CONNECT_PORT = 20049
REMOTE_PATH = "/FACECE8985B6479F9EA06464DCFBAD68"
PRE_GENERATED_CONFIG_FILE_NAME = (
    "/etc/stunnel/ibmshare_FACECE8985B6479F9EA06464DCFBAD68_10-240-64-83.conf"
)
EYE_CATCHER = "ibmshare-C0FFEE"


class TestStunnelConfigCreate(unittest.TestCase):

    def setUp(self):
        self.saved_stunnel_dir = StunnelConfigGet.STUNNEL_DIR_NAME
        self.saved_pid_file_dir = StunnelConfigGet.STUNNEL_PID_FILE_DIR
        self.config_dir = tempfile.mkdtemp()

    def tearDown(self):
        StunnelConfigGet.STUNNEL_DIR_NAME = self.saved_stunnel_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = self.saved_pid_file_dir
        shutil.rmtree(self.config_dir)

    def write_working_sample(self, working_sample):
        buffer = (
            "# stunnel_identifier = /FACECE8985B6479F9EA06464DCFBAD68"
            "\n"
            f"pid = /var/run/stunnel4/ibmshare_FACECE8985B6479F9EA06464DCFBAD68_{ACCEPT_PORT}.pid"
            "\n"
            "log = overwrite"
            "\n"
            f"output = /var/log/stunnel/ibmshare_FACECE8985B6479F9EA06464DCFBAD68_{ACCEPT_PORT}.log"
            "\n"
            "debug = 7"
            "\n"
            f"[ibmshare_FACECE8985B6479F9EA06464DCFBAD68_{ACCEPT_PORT}]"
            "\n"
            "\n"
            "client = yes"
            "\n"
            "accept = 127.0.0.1:10001"
            "\n"
            "connect = 10.240.64.83:20049"
            "\n"
            "verifyChain = yes"
            "\n"
            "checkHost = staging.is-share.appdomain.cloud"
            "\n"
            "cafile = /etc/ssl/tls.pem"
            "\n"
        )

        with open(working_sample, "w") as out_file:
            out_file.write(buffer)

    # Remove all lines starting with a hash until an empty line
    def compare_files(self, in_file1, in_file2):
        return filecmp.cmp(in_file1, in_file2, shallow=False)

    def remove_conf_header(self, in_file, cleaned_file):
        write_all = False
        with open(in_file, "r") as read_file, open(cleaned_file, "w") as write_file:
            for line in read_file:

                if line.strip() == "":
                    if not write_all:
                        write_all = True
                        continue
                if not line.startswith("#") or write_all:
                    write_file.write(line)

    def test_write_with_null_input(self):
        s = StunnelConfigCreate("", "", "", "", "")
        s.write_file()
        self.assertEqual(s.is_valid(), False)

    def test_write_file_failure(self):
        s = StunnelConfigCreate(
            ACCEPT_IP, ACCEPT_PORT, CONNECT_IP, CONNECT_PORT, REMOTE_PATH
        )
        s.filepath = "/tmp"
        s.get_trusted_ca_file = MagicMock(return_value="/tmp/file.conf")
        s.write_file()
        self.assertEqual(s.is_valid(), False)
        res = s.get_error().startswith(StunnelConfigCreate.WRITE_ERROR)
        self.assertEqual(res, True)

    def test_get_trusted_ca_file(self):
        config_dir = self.config_dir
        made_up_file_name = "/etc/ssl/tls.pem"
        # Good file has the key value pair and bad does not.
        good_file = os.path.join(config_dir, "good_file.conf")
        bad_file = os.path.join(config_dir, "bad_file.conf")
        good_content = f"TRUSTED_ROOT_CACERT={made_up_file_name}"
        bad_content = "This does not contain the content we are looking for"

        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir

        write_file(good_file, good_content)
        write_file(bad_file, bad_content)
        s = StunnelConfigCreate(
            ACCEPT_IP, ACCEPT_PORT, CONNECT_IP, CONNECT_PORT, REMOTE_PATH
        )

        ret = s.get_trusted_ca_file(good_file, StunnelConfigGet.CA_FILE_KEY)
        self.assertEqual(ret, made_up_file_name)
        self.assertEqual(s.is_valid(), True)
        ret = s.get_trusted_ca_file(bad_file, StunnelConfigGet.CA_FILE_KEY)
        self.assertEqual(ret, None)
        self.assertEqual(s.is_valid(), False)

    def run_get_stunnel_env_test(self, stunnel_obj, magic_method, expected_return):
        stunnel_obj.get_from_config_file = magic_method
        ret = stunnel_obj.get_stunnel_env()
        self.assertEqual(ret, expected_return)

    def test_get_stunnel_env(self):
        s = StunnelConfigCreate(
            ACCEPT_IP, ACCEPT_PORT, CONNECT_IP, CONNECT_PORT, REMOTE_PATH
        )

        self.run_get_stunnel_env_test(
            s,
            MagicMock(return_value=StunnelConfigGet.STUNNEL_ENV_DEV.upper()),
            StunnelConfigGet.STUNNEL_ENV_DEV,
        )
        self.run_get_stunnel_env_test(
            s,
            MagicMock(return_value=StunnelConfigGet.STUNNEL_ENV_DEV.lower()),
            StunnelConfigGet.STUNNEL_ENV_DEV,
        )
        self.run_get_stunnel_env_test(
            s,
            MagicMock(return_value=StunnelConfigGet.STUNNEL_ENV_STAGE.lower()),
            StunnelConfigGet.STUNNEL_ENV_STAGE,
        )
        self.run_get_stunnel_env_test(
            s,
            MagicMock(return_value=StunnelConfigGet.STUNNEL_ENV_STAGE.upper()),
            StunnelConfigGet.STUNNEL_ENV_STAGE,
        )
        self.run_get_stunnel_env_test(
            s,
            MagicMock(return_value=StunnelConfigGet.STUNNEL_ENV_PROD.lower()),
            StunnelConfigGet.STUNNEL_ENV_PROD,
        )
        self.run_get_stunnel_env_test(
            s,
            MagicMock(return_value=StunnelConfigGet.STUNNEL_ENV_PROD.upper()),
            StunnelConfigGet.STUNNEL_ENV_PROD,
        )

        ## Test for default.
        self.run_get_stunnel_env_test(
            s,
            MagicMock(return_value="not dev or stage"),
            StunnelConfigGet.STUNNEL_ENV_PROD,
        )
        self.run_get_stunnel_env_test(
            s, MagicMock(return_value=None), StunnelConfigGet.STUNNEL_ENV_PROD
        )

    def test_write_file_success(self):
        StunnelConfigGet.STUNNEL_DIR_NAME = "/etc/stunnel"
        s = StunnelConfigCreate(
            ACCEPT_IP, ACCEPT_PORT, CONNECT_IP, CONNECT_PORT, REMOTE_PATH
        )
        config_dir = self.config_dir

        conf_filepath = s.filepath

        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = "/var/run/stunnel4"
        generated_file = os.path.join(config_dir, "generated.int.conf")
        s.filepath = generated_file
        s.get_trusted_ca_file = MagicMock(return_value="/etc/ssl/tls.pem")
        s.get_stunnel_env = MagicMock(return_value="staging")
        s.write_file()
        cleaned_file = os.path.join(config_dir, "generated.conf")
        working_sample = os.path.join(config_dir, "working_sample")
        self.write_working_sample(working_sample)
        self.remove_conf_header(generated_file, cleaned_file)
        self.assertEqual(conf_filepath, PRE_GENERATED_CONFIG_FILE_NAME)
        cmp = self.compare_files(cleaned_file, working_sample)
        self.assertEqual(cmp, True)
        self.assertEqual(s.is_valid(), True)
        self.assertEqual(s.get_error(), None)


if __name__ == "__main__":
    unittest.main()
