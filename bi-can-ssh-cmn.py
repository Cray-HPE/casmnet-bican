#!/usr/bin/env python3
import os
import re
import utils.network

if utils.network.interface_exists("cmn") == True:
    print("CMN interface configured")
    interface_status, ip_addr = utils.network.get_interface_status("cmn")
    print(interface_status)
    with open('/etc/ssh/sshd_config', 'r+') as f:
        if f"ListenAddress {ip_addr}" in f.read():
            print(f'"ListenAddress {ip_addr}" is in /etc/ssh/sshd_config')
            print(f"This is the correct configuration")
            f.close()
        else:
            print("/etc/ssh/sshd_config is missing the correct configuration, adding it now")
            f.write(f"ListenAddress {ip_addr}")
            print(f'"ListenAddress {ip_addr}" appended to /etc/ssh/sshd_config')
else:
    print("Missing CMM interface")