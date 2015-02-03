#import logging
from patterns import LoggerObject
from handlers import ProfileHandler


class Peripheral(LoggerObject):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2

    def __init__(self, uuid=None, name="", rssi=0, address=""):
        try:
            super().__init__()
        except:
            super(Peripheral, self).__init__()
        self.name = name
        self.UUID = uuid
        self._rssi = rssi
        self.address = address
        self.services = []
        self._serviceUUIDs = []
        self._state = Peripheral.DISCONNECTED

        # callback functions
        self.update_state_callback = None
        self.update_rssi_callback = None

        self._delegate = None

    @property
    def delegate(self):
        if self._delegate:
            return self._delegate
        else:
            return None

    @delegate.setter
    def delegate(self, handler_cls):
        if handler_cls:
            self._delegate = handler_cls(self, self.UUID)
            self._delegate.initialize()
        else:
            self._delegate = None

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

    def __iter__(self):
        return iter(self.services)

    def __getitem__(self, key):
        if self.delegate:
            found = False
            for pHandler in self.delegate.profile_handlers.values():
                if pHandler.names:
                    for uuid, name in pHandler.names.iteritems():
                        if name == key:
                            key = uuid
                            found = True
                            break
                    if found:
                        break
        key = key.upper()
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
        if self._delegate:
            if self.state == Peripheral.CONNECTED:
                self._delegate.on_connect()
            elif self.state == Peripheral.DISCONNECTED:
                self._delegate.on_disconnect()

        if self.update_state_callback:
            try:
                self.update_state_callback(self.state)
            except Exception as e:
                print e

    def updateRSSI(self, rssi):
        if self._delegate:
            self._delegate.on_rssi(rssi)

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


class Central(LoggerObject):
    def __init__(self):
        try:
            super().__init__()
        except:
            super(Central, self).__init__()

        self.availableList = []
        self.connectedList = []
