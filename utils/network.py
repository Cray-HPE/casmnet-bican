from pyroute2 import NDB
ndb = NDB()

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
