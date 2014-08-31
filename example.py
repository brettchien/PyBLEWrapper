import sys
sys.dont_write_bytecode=True

from pyble import backend

import logging
import time

logging.basicConfig(format="%(asctime)s:%(levelname)-8s:%(name)s:%(message)s", level=logging.DEBUG)

#app = backend.load(shell=True)
#inq, outq = app.getTunnels()
#while not app.isReady():
#    pass
#logging.info("backend load complete, wait 3 sec and leave...")
#time.sleep(3)
#inq.put("stop")

class MyPeripheral(Peripheral):
    def __init__(self):
        super().__init__()

    @connected
    def onConnected(self):
        pass

    @disconnected
    def onDisconnected(self):
        pass


class MyProfile(Profile):
    UUID="180D"

    def __init__(self):
        # customized implementation registration through super class
        super().__init__()

    @characteristic(UUID="202A", event="update")
    def handler(self, characteristic):
        # handler for char with UUID 202A
        print characteristic


if __name__ == "__main__":
    app = backend.load(shell=True)
    app.ProfilePath.append(os.path.basename(__file__))
    app.scan()
    time.sleep(10)
    avialable = app.stopScan()
    peri = app.connect(avialable[0])
    while not peri.connected:
        pass

    while peri.connected:
        time.sleep(60)
        c = peri.getCharacteristic(UUID="202B")
        c.write("123")
