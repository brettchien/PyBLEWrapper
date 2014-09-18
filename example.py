import sys
sys.dont_write_bytecode=True

import pyble
from pyble.handlers import PeripheralHandler, ProfileHandler
from pyble.osx.backend import OSXCentralManagerApp

#cm = pyble.CentralManager()
# scan a peripheral
#p = cm.startScan()
#cm.registerPeripheralHandler(MyPeripheral)
#handler = MyPeripheralHandler(p)
#cm.connectPeripheral(p)
#cm.run()


#class MyPeripheral(PeripheralHandler):
#    def initialize(self):
#        print "haha"

class MyDefeult(ProfileHandler):
    UUID = "*"

    def on_read(self, characteristic, data):
        ans = []
        for b in data:
            ans.append("%02X" % ord(b))
        ret = "0x" + "".join(ans)
        return ret

class GenericAccess(ProfileHandler):
    UUID = "1800"

    def on_read(self, characteristic, data):
        cUUID = characteristic.UUID
        if cUUID == "2A00":
            return str(data)
        elif cUUID == "2A03":
            address = []
            for b in data:
                address.append("%02X" % ord(b))
            return "-".join(address)
        else:
            ans = []
            for b in data:
                ans.append("0x%02X" % ord(b))
            return " ".join(ans)

class DeviceInformation(ProfileHandler):
    UUID = "180A"

    def on_read(self, characteristic, data):
        if characteristic.UUID == "2A23":
            address = []
            for b in data:
                address.append("%X" % ord(b))
            return "-".join(address)
        else:
            return str(data)

class MyProfile(ProfileHandler):
    UUID = "180F"

    def on_read(self, characteristic, data):
        if characteristic.UUID == "2A19":
            return ord(data)

def main():
    cm = pyble.CentralManager()
    if not cm.ready:
        return
    target = None
    while True:
        try:
            target = cm.startScan(withServices=["FFF0"])
            if target:
                print target
                break
        except Exception as e:
            print e
    p = cm.connectPeripheral(target)
    for service in p:
        print service
        for c in service:
            print "  {} : {}".format(c, str(c.value))
    cm.disconnectPeripheral(p)

if __name__ == "__main__":
    print ProfileHandler.handlers
    print ProfileHandler.handlers["180F"]
    print ProfileHandler["180F"]
    print ProfileHandler["2A23"]
#    app = OSXCentralManagerApp()
#    app.cmdloop()
    main()
