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
import pprint
import os
from pyroute2 import IPRoute
from pyroute2 import NDB
from socket import AF_INET
import ipaddress
import platform
import utils.sls
import utils.network
import sys
from jinja2 import Template
from netaddr import *

usage_message = "Usage ./bi-can-interface.py [CHN, CMN]"
try:
    desired_if = sys.argv[1].upper()
    if desired_if not in ["CHN", "CMN"]:
        print(usage_message)
        raise (SystemExit)
except IndexError:
    print(usage_message)
    raise (SystemExit)

ndb = NDB()

desired_if_lc = desired_if.lower()

if desired_if == 'CMN':
    if_name = "bond0.%s0" % desired_if_lc
elif desired_if == 'CHN':
    if_name = 'hsn0'

new_ifcfg = Template('''VLAN_PROTOCOL='ieee802-1Q'
ETHERDEVICE='bond0'
IPADDR={{ ip }}
PREFIXLEN={{ prefixlength }}
BOOTPROTO='static'
STARTMODE='auto'
MTU='9000'
ONBOOT='yes'
VLAN='yes'
VLAN_ID={{ VLAN }}
''')

#get hostname of NCN
hostname = (platform.node())
print(f"hostname: {hostname}")
#Call to SLS and get appropriate IP address
sls_variables = utils.sls.parse_sls_file()
VLAN = (sls_variables["%s_VLAN" % desired_if])
Gateway = (sls_variables["%s_IP_GATEWAY" % desired_if])
Network = IPNetwork(sls_variables[desired_if])

prefixlength = str(Network.prefixlen)
ip = utils.sls.get_ip(f"{hostname}-{desired_if_lc}")
print(f"{desired_if} IP from SLS: {ip}")
print(f"{desired_if}_Network from SLS: {Network}")
print(f"{desired_if}_VLAN from SLS: {VLAN}")

#apply IP address to J2 template
new_ifcfg = new_ifcfg.render(ip = ip, prefixlength = prefixlength, VLAN = VLAN)

#create ifcfg file
def create_ifcfg_file(filename, contents):
    f = open(filename, "w")
    f.write(new_ifcfg)
    f.close

def write_ifcfg_file(filename):
    #check if file exists
    if os.path.isfile(filename):
        print(f"{filename} exists")
    else:
        print(f"missing {filename}.")
        #calls create_ifcfg_file function if the ifcfg file does not exist
        create_ifcfg_file(filename, new_ifcfg)
        print(f"created {filename}")

#create new interface, VLAN, IP, and link set to up.
def create_interface():
    (ndb.interfaces.create(ifname=desired_if_lc, kind='vlan',link='bond0',vlan_id=VLAN).commit())
    (ndb.interfaces[desired_if_lc].add_ip(ip).commit())
    (ndb.interfaces[desired_if_lc].set('state', 'up').commit())

#ping test with source interface.
def ping(source_interface, host):
    response = os.system(f"ping -I {source_interface} -c 1 {host} > /dev/null")
    if response == 0:
        return True
    else:
        return False

ifcfg_path = "/etc/sysconfig/network/ifcfg-%s" % if_name

#create ifcfg file
write_ifcfg_file(ifcfg_path)

if utils.network.interface_exists(if_name) == True:
    print(f"{desired_if} interface already configured")
    print(utils.network.get_interface_status(if_name))
    if ping(if_name, Gateway) == True:
        print(f"Ping test to {Gateway} from the {desired_if} interface is successful")
    else:
        print(f"Ping test to {Gateway} from the {desired_if} interface FAILED")
else:
    print("Missing {desired_if} interface, configuring now.")
    create_interface()
    print(utils.network.get_interface_status(if_name))
    if ping(desired_if_lc, Gateway) == True:
        print(f"Ping test to {Gateway} from the {desired_if} interface is successful")
    else:
        print(f"Ping test to {Gateway} from the {desired_if} interface FAILED")
