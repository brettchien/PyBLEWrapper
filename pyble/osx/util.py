# some utility functions
import uuid

from subprocess import Popen, PIPE
from plistlib import readPlistFromString
from collections import namedtuple

def CBUUID2String(uuidBytes):
    ret = ""
    if len(uuidBytes) == 2:
        for b in uuidBytes:
            ret += "%02X" % ord(b)
    elif len(uuidBytes) == 16:
        ret = str(uuid.UUID(bytes=uuidBytes)).upper()
    else:
        return None
    return ret

def readDeviceInfo():
    BluetoothDevice = namedtuple('BluetoothDevice', ['MACAddress', 'name', 'powerOn'])
    sp = Popen(["system_profiler", "-xml", "-detailLevel", "basic", "SPBluetoothDataType"], stdout=PIPE).communicate()[0]
    info = readPlistFromString(sp)
    dev = info[0]['_items'][0]['local_device_title']
    address = dev['general_address']
    name = ""
    if "general_name" in dev:
        name = dev['general_name']
    on = ("attrib_On" == dev['general_power'])
    return BluetoothDevice(address, name, on)
