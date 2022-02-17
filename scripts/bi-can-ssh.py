#!/usr/bin/env python3
# Copyright 2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)
import os
import re
import sys
import utils.network

usage_message = "Usage ./bi-can-ssh.py [CHN, CMN]"
try:
    desired_if = sys.argv[1].upper()
    if desired_if not in ["CHN", "CMN"]:
        print(usage_message)
        raise (SystemExit)
except IndexError:
    print(usage_message)
    raise (SystemExit)

desired_if_lc = desired_if.lower()
if_name = "bond0.%s0" % desired_if_lc

if utils.network.interface_exists(if_name) == True:
    print(f"{desired_if} interface configured")
    interface_status, ip_addr = utils.network.get_interface_status(if_name)
    print(ip_addr)
    print(interface_status)
    with open('/etc/ssh/sshd_config', 'r+') as f:
        if f"ListenAddress {ip_addr}" in f.read():
            print(f'"ListenAddress {ip_addr}" is in /etc/ssh/sshd_config')
            print(f"This is the correct configuration")
            f.close()
        else:
            print("/etc/ssh/sshd_config is missing the correct configuration, adding it now")
            f.write(f"\nListenAddress {ip_addr}\n")
            print(f'"ListenAddress {ip_addr}" appended to /etc/ssh/sshd_config')
else:
    print(f"Missing {desired_if} interface")
