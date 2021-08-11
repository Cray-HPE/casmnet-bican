#!/usr/bin/env python3
import pprint
import os
from pyroute2 import IPRoute
from pyroute2 import NDB
from socket import AF_INET
import ipaddress
import sls
import sys

usage_message = "Usage ./bi-can.py [CAN, CHN]"
# take in switch IP and path as arguments
try:
    desired_default_route = sys.argv[1].upper()
    if desired_default_route not in ["CAN", "CHN"]:
        print(usage_message)
        raise (SystemExit)
except IndexError:
    print(usage_message)
    raise (SystemExit)

#ndb debug
ndb = NDB()

#retreive all the SLS network variables.
sls_variables = sls.parse_sls_file()

HSN_Gateway = (sls_variables['HSN_IP_GATEWAY'])
CAN_Gateway = (sls_variables['CAN_IP_GATEWAY'])

if desired_default_route == 'CAN':
    default_route_interface = 'vlan007'
    desired_default_route = CAN_Gateway
elif desired_default_route == 'CHN':
    desired_default_route = HSN_Gateway
    default_route_interface = 'hsn'

print("HSN Default Gateway " + HSN_Gateway)
print("CAN Default Gateway " + CAN_Gateway)

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
        
# Check interface status
def get_interface_status(name):
    for interface in name:
        #get IP
        ip = list(ndb.interfaces[interface].ipaddr.summary().select('address'))
        state = str(ndb.interfaces[interface]['state'])
        carrier = bool(ndb.interfaces[interface]['carrier'])
        if carrier == True:
            carrier_status = "up"
        else: 
            carrier_status = "down"
    #print HSN interface status
    return (f"INTERFACE: {interface} STATE: {state} CARRIER: {carrier_status} IP: {ip[0]}")

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

def write_ifroute_file(gateway, filename):
    ifroute_default = (f'default {gateway} - -')
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
        (ndb.routes['default'].remove().create(dst='default', gateway=gateway).commit())
    else:
        print(f"connection to {gateway} failed")
        raise (SystemExit)

my_interfaces = get_interface(default_route_interface)
print("INTERFACE STATUS")
print(get_interface_status(my_interfaces))
print()
switch_default_gateway(desired_default_route)
ifcfg_path = '/etc/sysconfig/network/'

for interface in my_interfaces:
    file = (f'{ifcfg_path}ifroute-{interface}')
    write_ifroute_file(desired_default_route, file)

# find home for this github?
#goss test for pre-flight checks for next hop and connectivity
#run