import unittest
from stunnel_config_create import StunnelConfigCreate
from stunnel_config_get import StunnelConfigGet
import tempfile
import os
from datetime import datetime
import shutil
import filecmp

ACCEPT_IP = "127.0.0.1"
ACCEPT_PORT = 10001
CONNECT_IP = "10.240.64.83"
CONNECT_PORT = 20049
REMOTE_PATH = "/FACECE8985B6479F9EA06464DCFBAD68"
PRE_GENERATED_CONFIG_FILE_NAME = (
    "/etc/stunnel/ibmshare_FACECE8985B6479F9EA06464DCFBAD68.conf"
)
EYE_CATCHER = "ibmshare-C0FFEE"


class TestStunnelConfigCreate(unittest.TestCase):

    def setUp(self):
        self.saved_stunnel_dir = StunnelConfigGet.STUNNEL_DIR_NAME
        self.saved_pid_file_dir = StunnelConfigGet.STUNNEL_PID_FILE_DIR

    def tearDown(self):
        StunnelConfigGet.STUNNEL_DIR_NAME = self.saved_stunnel_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = self.saved_pid_file_dir

    def write_working_sample(self, working_sample):
        buffer = (
            "# stunnel_identifier = /FACECE8985B6479F9EA06464DCFBAD68"
            "\n"
            "pid = /var/run/stunnel4/ibmshare_FACECE8985B6479F9EA06464DCFBAD68.pid"
            "\n"
            "[ibmshare_FACECE8985B6479F9EA06464DCFBAD68]"
            "\n"
            "\n"
            "client = yes"
            "\n"
            "accept = 127.0.0.1:10001"
            "\n"
            "connect = 10.240.64.83:20049"
            "\n"
            "verifyPeer = yes"
            "\n"
            "verifyChain = yes"
            "\n"
            "cafile = /etc/stunnel/allca.pem"
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
        s.write_file()
        self.assertEqual(s.is_valid(), False)
        res = s.get_error().startswith(StunnelConfigCreate.WRITE_ERROR)
        self.assertEqual(res, True)

    def test_write_file_success(self):
        StunnelConfigGet.STUNNEL_DIR_NAME = "/etc/stunnel"
        s = StunnelConfigCreate(
            ACCEPT_IP, ACCEPT_PORT, CONNECT_IP, CONNECT_PORT, REMOTE_PATH
        )
        config_dir = tempfile.mkdtemp()

        conf_filepath = s.filepath

        StunnelConfigGet.STUNNEL_DIR_NAME = config_dir
        StunnelConfigGet.STUNNEL_PID_FILE_DIR = "/var/run/stunnel4"
        generated_file = os.path.join(config_dir, "generated.int.conf")
        s.filepath = generated_file
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
        shutil.rmtree(config_dir)


if __name__ == "__main__":
    unittest.main()
