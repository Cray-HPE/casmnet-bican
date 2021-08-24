#!/usr/bin/env python3
import os
from pyroute2 import NDB
import re

ndb = NDB()

ip_address = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')

def get_interface_status(name):
    #get IP
    ip = list(ndb.interfaces[name].ipaddr.summary().select('address'))
    ip_str = str(ip[0])
    ip_addr = ip_str[2:-3]
    state = str(ndb.interfaces[name]['state'])
    carrier = bool(ndb.interfaces[name]['carrier'])
    if carrier == True:
        carrier_status = "up"
    else: 
        carrier_status = "down"
#return interface status and IP
    interface_status = (f"INTERFACE: {name} STATE: {state} CARRIER: {carrier_status} IP: {ip_addr}")
    return interface_status, ip_addr

def interface_exists(name):
    for interface in ndb.interfaces.dump():
        if name == interface.ifname:
            return True

if interface_exists("cmn") == True:
    print("CMN interface configured")
    interface_status, ip_addr = get_interface_status("cmn")
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