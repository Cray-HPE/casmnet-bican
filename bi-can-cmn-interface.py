#!/usr/bin/env python3
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

#ndb debug
ndb = NDB()

cmn_ifcfg = Template('''VLAN_PROTOCOL='ieee802-1Q'
ETHERDEVICE='bond0'
IPADDR={{ ip }}
PREFIXLEN={{ prefixlength }}
BOOTPROTO='static'
STARTMODE='auto'
MTU='1500'
ONBOOT='yes'
VLAN='yes'
VLAN_ID={{ VLAN }}
''')

#get hostname of NCN
hostname = (platform.node())
print(f"hostname: {hostname}")
#Call to SLS and get CMN IP address
sls_variables = utils.sls.parse_sls_file()
VLAN = (sls_variables["CMN_VLAN"])
CMN_Gateway = (sls_variables["CMN_IP_GATEWAY"])
CMN_Network = IPNetwork(sls_variables["CMN"])

prefixlength = str(CMN_Network.prefixlen)
ip = utils.sls.get_ip(f"{hostname}-cmn")
print(f"CMN IP from SLS: {ip}")

#apply IP address to J2 template
cmn_ifcfg = cmn_ifcfg.render(ip = ip, prefixlength = prefixlength, VLAN = VLAN)

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
    (ndb.interfaces.create(ifname='cmn', kind='vlan',link='bond0',vlan_id=VLAN).commit())
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

if utils.network.interface_exists("cmn") == True:
    print("CMN interface already configured")
    print(utils.network.get_interface_status("cmn"))
    if ping("cmn", CMN_Gateway) == True:
        print(f"Ping test to {CMN_Gateway} from the CMM interface is successful")
    else:
        print(f"Ping test to {CMN_Gateway} from the CMM interface FAILED")
else:
    print("Missing CMM interface, configuring now.")
    create_interface()
    print(utils.network.get_interface_status("cmn"))
    if ping("cmn", CMN_Gateway) == True:
        print(f"Ping test to {CMN_Gateway} from the CMM interface is successful")
    else:
        print(f"Ping test to {CMN_Gateway} from the CMM interface FAILED")
