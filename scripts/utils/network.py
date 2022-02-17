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
from pyroute2 import NDB
ndb = NDB()

def get_interface_status(name):
    #get IP
    ip=list(ndb.interfaces[name].ipaddr.summary())
    ip_addr = ip[0]['address']
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
