import sys
sys.dont_write_bytecode = True

import pyble
from pyble.handlers import PeripheralHandler, ProfileHandler

import time
import struct


class MyDefault(ProfileHandler):
    UUID = "3D9FFEC0-50BB-3960-8782-C593EDBC35EA"
    _AUTOLOAD = True
    names = {
        "3D9FFEC0-50BB-3960-8782-C593EDBC35EA": "EcoZen Profile",
        "3D9FFEC1-50BB-3960-8782-C593EDBC35EA": "EcoZen Char 1",
        "3D9FFEC2-50BB-3960-8782-C593EDBC35EA": "EcoZen Char 2",
        "3D9FFEC3-50BB-3960-8782-C593EDBC35EA": "EcoZen Char 3"
    }

    def initialize(self):
        print "init"
        pass

    def on_read(self, characteristic, data):
        ans = []
        for b in data:
            ans.append("%02X" % ord(b))
        ret = "0x" + "".join(ans)
        return ret


class Acceleration(ProfileHandler):
    UUID = "FFA0"
    _AUTOLOAD = True
    names = {
        "FFA0": "3-axis Acceleration",
        "FFA1": "Sensor Enable",
        "FFA2": "Acceleration Rate",
        "FFA3": "X-axis",
        "FFA4": "Y-axis",
        "FFA5": "Z-axis",
        "FFA6": "All axis"
    }

    def initialize(self):
        pass

    def on_read(self, characteristic, data):
        ans = []
        for b in data:
            ans.append("%02X" % ord(b))
        ret = "0x" + "".join(ans)
        return ret

    def on_notify(self, characteristic, data):
        cUUID = characteristic.UUID
        if cUUID == "FFA6":
            x, y, z = self.handleXYZ(data)
            print x, y, z

    def handleXYZ(self, data):
        x, y, z = struct.unpack(">HHH", data)
        x = (0.0 + (x >> 4)) / 1000
        y = (0.0 + (y >> 4)) / 1000
        z = (0.0 + (z >> 4)) / 1000
        x =  2.0 if x >  2.0 else x
        x = -2.0 if x < -2.0 else x
        y =  2.0 if y >  2.0 else y
        y = -2.0 if y < -2.0 else y
        z =  2.0 if z >  2.0 else z
        z = -2.0 if z < -2.0 else z
        return (x, y, z)


class MyPeripheral(PeripheralHandler):

    def initialize(self):
        self.addProfileHandler(MyDefault)

    def on_connect(self):
        print self.peripheral, "connect"

    def on_disconnect(self):
        print self.peripheral, "disconnect"

    def on_rssi(self, value):
        print self.peripheral, " update RSSI:", value


def main():
    cm = pyble.CentralManager()
    if not cm.ready:
        return
    target = None
    while True:
        try:
#            target = cm.startScan(withServices=["180D"])
            target = cm.startScan()
            if target and target.name == "EcoZe1":
#            if target:
                print target
                break
        except Exception as e:
            print e
#    target.delegate = MyPeripheral
    p = cm.connectPeripheral(target)
    for service in p:
        #        if service.UUID == "FFF0":
#            continue
#        if service.UUID == "180A":
#            continue
        print service
        for c in service:
            print c, " : ",
            print c.value
#            print c
#            print "description: ", c.description
#            print "value      : ", c.value

#    c = p["FFA0"]["FFA1"]
#    p["FFA0"]["FFA6"].notify = True
#    c.value = bytearray(chr(1))
#    cm.loop(duration=10)
#    cm.loop()
    cm.disconnectPeripheral(p)

if __name__ == "__main__":
    #    print ProfileHandler.handlers
    main()
