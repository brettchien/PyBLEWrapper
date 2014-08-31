import logging

class HCICommand(object):
    def __init__(self):
        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

    def startScan(self):
        self.logger.debug("HCI start scan")

    def stopSacn(self):
        self.logger.debug("HCI stop scan")

    def showConnections(self):
        self.logger.debug("HCI show connected connections")

    def showRSSI(self, conn):
        self.logger.debug("HCI show connected connection link quality")

    def showPeripherals(self, peripheral):
        self.logger.debug("HCI show connected peripherals")

    def showDevices(self):
        self.logger.debug("HCI show Bluetooth Smart devices")

