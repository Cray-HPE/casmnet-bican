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
import sys
import utils.sls
import utils.network

usage_message = "Usage ./bi-can-default-route.py [CHN, CMN]"
# take in switch IP and path as arguments
try:
    desired_default_route = sys.argv[1].upper()
    if desired_default_route not in ["CHN", "CMN"]:
        print(usage_message)
        raise (SystemExit)
except IndexError:
    print(usage_message)
    raise (SystemExit)

desired_default_route_lc = desired_default_route.lower()

ndb = NDB()

#retreive all the SLS network variables.
sls_variables = utils.sls.parse_sls_file()

Gateway = (sls_variables["%s_IP_GATEWAY" % desired_default_route])
sls_default_route = Gateway

if desired_default_route == 'CMN':
    default_route_interface = desired_default_route_lc
elif desired_default_route == 'CHN':
    default_route_interface = 'hsn'

print(f"{desired_default_route} Default Gateway {Gateway}")

# Get current default route
current_default_route = ndb.routes["default"]['gateway']
print(f"The current default gateway is {current_default_route}")

#Get interfaces
def get_interface(name):
    interfaces = []
    for interface in ndb.interfaces.dump():
        if name in interface.ifname:
            interfaces.append(interface.ifname)
    return interfaces

#create default route ifcfg file
def create_ifroute_file(filename, contents):
    f = open(filename, "w")
    f.write(contents)
    f.close
    if "hsn" in filename and os.path.exists(f"{ifcfg_path}ifroute-vlan007"):
        os.remove(f'{ifcfg_path}ifroute-vlan007')
        print('deleting ifroute-vlan007')
    elif "vlan007" in filename and os.path.exists(f"{ifcfg_path}ifroute-hsn0"):
        os.remove(f'{ifcfg_path}ifroute-hsn0')
        print('deleting ifroute-hsn0')

def ping(host):
    response = os.system(f"ping -c 1 {host} > /dev/null")
    if response == 0:
        return True
    else:
        return False

def write_ifroute_file(gateway, filename, interface):
    ifroute_default = (f'default {gateway} - {interface}\n')
    #check if file exists
    if os.path.isfile(filename):
        #check contents of file
        f = open(filename, 'r')
        route=(f.read())
        if route == ifroute_default:
            print(f"{filename} already exists and file contents are correct")
            f.close()
        else:
            print(f"ifroute file incorrect, overwritting {filename}.")
            create_ifroute_file(file, ifroute_default)
    else:
        print(f"missing {filename}.")
        create_ifroute_file(filename, ifroute_default)
        print(f"created {filename}")

#Switch default gateway if ping is successful
def switch_default_gateway(gateway):
    if gateway == current_default_route:
        print(f"your default route is already set to {gateway}")
    elif ping(gateway) == True:
        print(f"ping test to {gateway} passed")
        print(f"changing the default route to {gateway}")
        (ndb.routes['default'].remove().commit())
        (ndb.routes.create(dst='default', gateway=gateway).commit())
    else:
        print(f"connection to {gateway} failed")
        raise (SystemExit)

my_interfaces = get_interface(default_route_interface)
print("INTERFACE STATUS")
print(my_interfaces)
for interface in my_interfaces:
    print(utils.network.get_interface_status(interface))

print()
switch_default_gateway(sls_default_route)
ifcfg_path = '/etc/sysconfig/network/'

for interface in my_interfaces:
    file = (f'{ifcfg_path}ifroute-{interface}')
    write_ifroute_file(sls_default_route, file, interface)
