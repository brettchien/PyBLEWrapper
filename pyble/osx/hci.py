
from  pyble.hci import HCICommand
import logging

class OSXHCICommand(HCICommand):
    def __init__(self, centralManager):
        self.centralManager = centralManager
        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

    def startScan(self):
        self.logger.debug("OSX HCI Start Scan")
        peripherals = self.centralManager.startScan()

    def stopScan(self):
        self.logger.debug("OSX HCI Stop Scan")
        return self.centralManager.stopScan()

    def connect(self, peripheral):
        self.logger.debug("OSX HCI Connect: %s" % peripheral)
        self.centralManager.connectPeripheral(peripheral)

    def list(self):
        self.logger.debug("OSX HCI List connected peripherals")
        peripherals = self.centralManager.getConnectedList()
        self.logger.info("Connected Peripherals:")
        if len(peripherals):
            for p in peripherals:
                self.logger.info("\t" + str(p))
        else:
            self.logger.info("\tNone")

    def disconnect(self, peripheral):
        self.logger.debug("OSX HCI Disconnect: " + peripheral.name)
        self.centralManager.disconnectPeripheral(peripheral)

    def disconnectAll(self):
        self.logger.debug("OSX HCI Disconnect all connected peripherals")
        self.centralManager.disconnectAllPeripherals()

