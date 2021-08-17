#!/usr/bin/env python3
import pprint
import os
from pyroute2 import IPRoute
from pyroute2 import NDB
from socket import AF_INET
import ipaddress
import platform
import sls
import sys
from jinja2 import Template

#ndb debug
ndb = NDB()

cmn_ifcfg = Template('''VLAN_PROTOCOL='ieee802-1Q'
ETHERDEVICE='bond0'
IPADDR={{ ip }}
BOOTPROTO='static'
STARTMODE='auto'
MTU='1500'
ONBOOT='yes'
VLAN='yes'
''')

#get hostname of NCN
hostname = (platform.node())
print(f"hostname: {hostname}")
#Call to SLS and get CMN IP address
ip = sls.get_ip(f"{hostname}-cmn")
print(f"CMN IP from SLS: {ip}")

#apply IP address to J2 template
cmn_ifcfg = cmn_ifcfg.render(ip = ip)

#Call to SLS to get CMN gateway info
sls_variables = sls.parse_sls_file()
CMN_Gateway = (sls_variables["CMN_IP_GATEWAY"])

#check for interface existance
def interface_exists(name):
    for interface in ndb.interfaces.dump():
        if name == interface.ifname:
            return True

#check for interface status, returns interface status
def get_interface_status(interface):
    ip = list(ndb.interfaces[interface].ipaddr.summary().select('address'))
    ip_list = []
    for i in ip:
        ip_list.append(i)
    state = str(ndb.interfaces[interface]['state'])
    carrier = bool(ndb.interfaces[interface]['carrier'])
    if carrier == True:
        carrier_status = "up"
    else: 
        carrier_status = "down"
    return (f"INTERFACE: {interface} STATE: {state} CARRIER: {carrier_status} IP: {ip_list}")

#create ifcfg file
def create_ifcfg_file(filename, contents):
    f = open(filename, "w")
    f.write(cmn_ifcfg)
    f.close

def write_ifcfg_file(filename):
    #check if file exists    
    if os.path.isfile(filename):
        print(f"{filename} exists")
    else:
        print(f"missing {filename}.")
        #calls create_ifcfg_file function if the ifcfg file does not exist
        create_ifcfg_file(filename, cmn_ifcfg)
        print(f"created {filename}")

#create cmn interface, VLAN, IP, and link set to up.
def create_interface():
    (ndb.interfaces.create(ifname='cmn', kind='vlan',link='bond0',vlan_id=13).commit())
    (ndb.interfaces['cmn'].add_ip(ip).commit())
    (ndb.interfaces['cmn'].set('state', 'up').commit())

#ping test with source interface.
def ping(source_interface, host):
    response = os.system(f"ping -I {source_interface} -c 1 {host} > /dev/null")
    if response == 0:
        return True
    else:
        return False

#cmn ifcfg path
ifcfg_path = '/etc/sysconfig/network/ifcfg-cmn'

#create ifcfg file
write_ifcfg_file(ifcfg_path)

if interface_exists("cmn") == True:
    print("CMN interface already configured")
    print(get_interface_status("cmn"))
    if ping("cmn", CMN_Gateway) == True:
        print(f"Ping test to {CMN_Gateway} from the CMM interface is successful")
    else:
        print(f"Ping test to {CMN_Gateway} from the CMM interface FAILED")
else:
    print("Missing CMM interface, configuring now.")
    create_interface()
    print(get_interface_status("cmn"))
    if ping("cmn", CMN_Gateway) == True:
        print(f"Ping test to {CMN_Gateway} from the CMM interface is successful")
    else:
        print(f"Ping test to {CMN_Gateway} from the CMM interface FAILED")
