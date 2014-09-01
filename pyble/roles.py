
class Peripheral(object):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2

    def __init__(self, instance=None, uuid=None, name="", advertisementData=None, rssi=0, address=""):
        self.instance = instance
        self.name = name
        self.UUID = uuid
        self.advertisementData = advertisementData
        self._rssi = rssi
        self.address = address
        self.services = []
        self._serviceUUIDs = []
        self.delegate = None
        self._state = Peripheral.DISCONNECTED

        # callback functions
        self.update_state_callback = None
        self.update_rssi_callback = None

    @property
    def rssi(self):
        return self._rssi

    @rssi.setter
    def rssi(self, value):
        if self._rssi != value:
            self._rssi = value
            self.updateRSSI()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if self._state != value:
            self._state = value
            self.updateState()

    @property
    def serviceUUIDs(self):
        if len(self._serviceUUIDs) == 0:
            for service in self.services:
                self._serviceUUIDs.append(service.UUID)
        return self._serviceUUIDs

    @serviceUUIDs.setter
    def serviceUUIDs(self, value):
        try:
            self._serviceUUIDs = value[:]
        except:
            pass

    def __getitem__(self, key):
        if key in self.serviceUUIDs:
            for service in self.services:
                if service.UUID == key:
                    return service
        raise KeyError

    def keys(self):
        return self.serviceUUIDs

    # register callbacks
    def setNotifyState(self, func):
        self.update_state_callback = func

    def setNotifyRSSI(self, func):
        self.update_rssi_callback = func

    def updateState(self):
        if self.update_state_callback:
            try:
                self.update_state_callback(self.state)
            except Exception as e:
                print e

    def updateRSSI(self, rssi):
        if self.update_rssi_callback:
            try:
                self.update_rssi_callback(rssi)
            except Exception as e:
                print e

    def __repr__(self):
        if self.name:
            return "Peripheral{%s (%s)}" % (self.name, str(self.UUID).upper())
        else:
            return "Peripheral{UNKNOWN (%s)}" % (str(self.UUID).upper())

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (other.UUID == self.UUID)

    def __ne__(self, other):
        return not self.__eq__(other)

class Central(object):
    def __init__(self):
        pass
