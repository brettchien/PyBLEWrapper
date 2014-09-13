import sys
sys.dont_write_bytecode=True

import pyble
from pyble.handlers import PeripheralHandler, ProfileHandler

cm = pyble.CentralManager()
# scan a peripheral
p = cm.startScan()
cm.registerPeripheralHandler(MyPeripheral)
handler = MyPeripheralHandler(p)
cm.connectPeripheral(p)
cm.run()


class MyPeripheral(PeripheralHandler):
    def initialize(self):
        self.registerProfile("180D", MyProfile)

class MyProfile(ProfileHandler):
    def initialize(self):
        pass

    



if __name__ == "__main__":
    import pyble

