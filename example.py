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

class MyProfile(ProfileHandler):
    UUID = "180F"

    def initialize(self):
        print "hehe"

    def on_notify(self, characteristic):
        print characteristic, " notify"

    def on_read(self, characteristic, data):
        if characteristic.UUID == "2A19":
            return ord(data)

    def on_write(self, characteristic, data):
        print characteristic, " write done"

if __name__ == "__main__":
    print ProfileHandler.handlers
    app = OSXCentralManagerApp()
    app.cmdloop()
