import unittest
import stunnel_config_get
import stunnel_config_create
from find_free_stunnel_port import FindFreeSTunnelPort
import tempfile
import os
from datetime import datetime
import shutil
import socket
from unittest.mock import patch
from test_common import *

IN_PORTS_LIST1 = [10001, 10002, 10003, 10004, 10015]
IN_PORTS_LIST2 = [10001, 10002, 10003, 10004, 10015, 10025]
IN_PORTS_LIST3 = []
IN_PORTS_LIST4 = [10024]
IN_PORTS_LIST5 = [10001]
NUMBER_OF_PORTS_TO_FAKE_BIND = 100
LOOPBACK_ADDRESS = "127.0.0.1"


class TestFindFreeStunnelPort(unittest.TestCase):
    def get_lowest_free_permitted_port(self, port_array, min_port, max_port):

        for port in range(min_port, max_port + 1):
            if port not in port_array:
                return port
        return -1

    def find_next_port_after_binding_ports(self, port_finder, free_port, config_dir):
        with patch.object(
            FindFreeSTunnelPort,
            "is_port_unused",
            new=self.custom_is_port_unused_blocked_ports,
        ):
            return FindFreeSTunnelPort(LOOPBACK_ADDRESS).get_free_port(config_dir)

    #  This is to simulate a few potenial bound ports
    def custom_is_port_unused_blocked_ports(self, host, port):
        start_port = FindFreeSTunnelPort.START_PORT
        return port > start_port + NUMBER_OF_PORTS_TO_FAKE_BIND

    #  No ports are bound. This method is faked to avoid actual bind
    def custom_is_port_unused_no_blocked_ports(self, host, port):
        return True

    def test_get_ports_from_conf_files(self):

        array_of_port_arrays = [
            IN_PORTS_LIST1,
            IN_PORTS_LIST2,
            IN_PORTS_LIST3,
            IN_PORTS_LIST4,
            IN_PORTS_LIST5,
        ]
        for port_array in array_of_port_arrays:
            config_dir = tempfile.mkdtemp()
            # Creates one conf file per port_array element
            stc = StunnelCommon()

            stc.create_conf_files(config_dir, port_array)
            with patch.object(
                FindFreeSTunnelPort,
                "is_port_unused",
                new=self.custom_is_port_unused_no_blocked_ports,
            ):
                port_finder = FindFreeSTunnelPort(LOOPBACK_ADDRESS)
                detected_ports = sorted(
                    port_finder.get_ports_from_conf_files(config_dir)
                )
                self.assertEqual(detected_ports, sorted(port_array))
                should_find_this_port = self.get_lowest_free_permitted_port(
                    detected_ports, port_finder.START_PORT, port_finder.END_PORT
                )
                free_port = port_finder.get_free_port(config_dir)
                self.assertEqual(should_find_this_port, free_port)

            next_free_port = self.find_next_port_after_binding_ports(
                port_finder=port_finder, free_port=free_port, config_dir=config_dir
            )
            next_free_port_good = (
                next_free_port != free_port
                and port_finder.START_PORT + NUMBER_OF_PORTS_TO_FAKE_BIND
                < next_free_port
                < port_finder.END_PORT + 1
            )

            self.assertEqual(next_free_port_good, True)
            # Cleanup so that old conf files dont interfere with the next test
            shutil.rmtree(config_dir)


if __name__ == "__main__":
    unittest.main()
