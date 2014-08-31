
class Peripheral(object):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2

    def __init__(self, instance=None, uuid=None, name="", advertisementData=None, rssi=0, address=""):
        self.instance = instance
        self.name = name
        self.UUID = uuid
        self.advertisementData = advertisementData
        self.rssi = rssi
        self.address = address
        self.services = []
        self.delegate = None
        self.state = Peripheral.DISCONNECTED

    def setNotifyOnName(self, func):
        pass

    def setNotifyOnRSSI(self, func):
        pass

    def updatePeripheral(self):
        pass

    def __repr__(self):
        if self.name:
            return "%s (%s)" % (self.name, str(self.UUID).upper())
        else:
            return "UNKNOWN (%s)" % (str(self.UUID).upper())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (other.UUID == self.UUID)

    def __ne__(self, other):
        return not self.__eq__(other)


class Central(object):
    def __init__(self):
        pass
