from Foundation import *
from IOBluetooth import *
from objc import *

from pyble.roles import Peripheral
from gatt import OSXBLEService, OSXBLECharacteristic, OSXBLEDescriptor
from util import CBUUID2String

import uuid
import logging
import struct
from pprint import pformat
import time

logger = logging.getLogger(__name__)

class OSXPeripheral(NSObject, Peripheral):
    def init(self):
        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))
        self.instance = None
        self.peripheral = None
        self.name = ""
        self.uuid = ""
        self._state = Peripheral.DISCONNECTED
        self.services = []
        self._rssi = 0

        # callbacks
        self.update_state_callback = None
        self.update_rssi_callback = None
        self.update_services_callback = None
        self.update_characteristic_callback = None

        return self

    # register callbacks
    def setPeriStateCallback(self, func):
        self.update_state_callback = func

    def setPeriServicesCallback(self, func):
        self.update_services_callback = func

    def setPeriRSSICallback(self, func):
        self.update_rssi_callback = func

    def setPeriCharCallback(self, func):
        self.update_characteristic_callback = func

    @property
    def rssi(self):
        self.instance.readRSSI()
        # delay for getting an newer RSSI value
        NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantFuture())
        return self._rssi

    @rssi.setter
    def rssi(self, value):
        self._rssi = value
        if self.update_rssi_callback:
            try:
                self.update_rssi_callback(self._rssi)
            except Exception as e:
                print e

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if value == Peripheral.DISCONNECTED:
            self.logger.debug("%s is disconnected" % self)
            self._state = value
        elif value == Peripheral.CONNECTING:
            self.logger.debug("Connecting to %s" % self)
            self._state = value
        elif value == Peripheral.CONNECTED:
            self.logger.debug("peripheral is connected")
            self._state = value
            # peripheral is connected, init. delegate to self
            # collecting gatt information
            if self.instance:
                self.instance.setDelegate_(self)
        else:
            self._state = Peripheral.DISCONNECTED
            self.logger.error("UNKOWN Peripheral State: " + value)
        if self.update_rssi_callback:
            try:
                self.update_state_callback(self._state)
            except Exception as e:
                print e

    def discoverServices(self):
        self.instance.discoverServices_(None)

    def __repr__(self):
        if self.name:
            return "Peripheral{%s (%s)}" % (self.name, str(self.UUID).upper())
        else:
            return "Peripheral{UNKOWN (%s)}" % (str(self.UUID).upper())

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (other.UUID == self.UUID)

    def __ne__(self, other):
        return not self.__eq__(other)

    def findServiceByServiceInstance(self, instance):
        uuidBytes = instance._.UUID._.data
        for s in self.services:
            if str(s.UUID)  == CBUUID2String(uuidBytes):
                return s
        return None

    def findServiceByCharacteristicInstance(self, instance):
        uuidBytes = instance._.service._.UUID._.data
        for s in self.services:
            if str(s.UUID)  == CBUUID2String(uuidBytes):
                return s
        return None

    def findServiceByDescriptorInstance(self, instance):
        uuidBytes = instance._.characteristic._.service._.UUID._.data
        for s in self.services:
            if str(s.UUID)  == CBUUID2String(uuidBytes):
                return s
        return None

    def findCharacteristicByDescriptorInstance(self, instance):
        service = self.findServiceByDescriptorInstance(instance)
        uuidBytes = instance._.characteristic._.UUID._.data
        for c in service.characteristics:
            if str(c.UUID) == CBUUID2String(uuidBytes):
                return c
        return None

    # CBPeripheral Delegate functions
    # Discovering Services
    def peripheral_didDiscoverServices_(self, peripheral, error):
        if error != nil:
            if error._.code == CBErrorNotConnected:
                self.state = Peripheral.DISCONNECT
            return
        if peripheral._.services:
            self.logger.debug("%s discovered services" % self)
            for service in peripheral._.services:
                s = OSXBLEService(self, service)
                self.services.append(s)
                if s.UUID not in ["1800", "1801"]:
                    peripheral.discoverCharacteristics_forService_(nil, service)

        # service list callback
        if self.update_services_callback:
            try:
                self.update_services_callback(self.services)
            except Exception as e:
                print e

    def peripheral_didDiscoverIncludeServicesForService_error_(self, peripheral, service, error):
        self.logger.debug("%s discovered Include Services" % self)

    # Discovering Characteristics and Characteristic Descriptors
    def peripheral_didDiscoverCharacteristicsForService_error_(self, peripheral, service, error):
        if error != nil:
            print error
            return
        s = self.findServiceByServiceInstance(service)
        p = s.peripheral
        self.logger.debug("%s:%s discovered characteristics" % (p, s))
        for c in service._.characteristics:
            characteristic = OSXBLECharacteristic(s, c)
            s.addCharacteristic(characteristic)
            peripheral.discoverDescriptorsForCharacteristic_(c)
            if characteristic.properties["read"]:
                peripheral.readValueForCharacteristic_(c)

    def peripheral_didDiscoverDescriptorsForCharacteristic_error_(self, peripheral, characteristic, error):
        s = self.findServiceByCharacteristicInstance(characteristic)
        p = s.peripheral
        c = s.findCharacteristicByInstance(characteristic)
        self.logger.debug("%s:%s:%s discovered descriptors" % (p, s, c))
        for d in characteristic._.descriptors:
            descriptor = OSXBLEDescriptor(c, d)
            c.addDescriptor(descriptor)
            if descriptor.UUID == "2901":
                peripheral.readValueForDescriptor_(d)

    # Retrieving Characteristic and characteristic Descriptor Values
    def peripheral_didUpdateValueForCharacteristic_error_(self, peripheral, characteristic, error):
        s = self.findServiceByCharacteristicInstance(characteristic)
        p = s.peripheral
        c = s.findCharacteristicByInstance(characteristic)
        value = None
        if error == nil:
            # converting NSData to bytestring
            value = bytes(characteristic._.value)
            c.value = value
#            peripheral.readRSSI()
            self.logger.debug("%s:%s:%s updated value: %s" % (p, s, c, pformat(value)))
        else:
            self.logger.debug("%s:%s:%s %s" % (p, s, c, str(error)))

    def peripheral_didUpdateValueForDescriptor_error_(self, peripheral, descriptor, error):
        s = self.findServiceByDescriptorInstance(descriptor)
        p = s.peripheral
        c = self.findCharacteristicByDescriptorInstance(descriptor)
        d = c.findDescriptorByInstance(descriptor)
        value = None
        if error == nil:
            # converting NSData to bytes
            value = bytes(descriptor._.value)
            d.value = value
            self.logger.debug("%s:%s:%s:%s updated value: %s" % (p, s, c, d, pformat(value)))
        else:
            self.logger.debug("%s:%s:%s:%s %s" % (p, s, c, d, str(error)))

    # Writing Characteristic and Characteristic Descriptor Values
    def peripheral_didWriteValueForCharacteristic_error_(self, peripheral, characteristic, error):
        s = self.findServiceByCharacteristicInstance(characteristic)
        p = s.peripheral
        c = s.findCharacteristicByInstance(characteristic)
        self.logger.debug("Characteristic Value Write Done")

    def peripheral_didWriteValueForDescriptor_error_(self, peripheral, descriptor, error):
        self.logger.debug("Descriptor Value write Done")

    # Managing Notifications for a Characteristic's Value
    def peripheral_didUpdateNotificationStateForCharacteristic_error_(self, peripheral, characteristic, error):
        s = self.findServiceByCharacteristicInstance(characteristic)
        p = s.peripheral
        c = s.findCharacteristicByInstance(characteristic)
        result = "Success"
        if error != nil:
            result = "Fail"
            print error
        self.logger.debug("%s:%s:$s set Notification %s" % (p, s, c, result))

    # Retrieving a Peripheral's Received Signal Strength Indicator(RSSI) Data
    def peripheralDidUpdateRSSI_error_(self, peripheral, error):
        if error == nil:
            rssi = int(peripheral.RSSI())
            if rssi == 127:
                # RSSI value cannot be read
                return
            self.logger.debug("%s updated RSSI value: %d -> %d" % (self, self._rssi, rssi))
            self.rssi = rssi
        else:
            print error

    # Monitoring Changes to a Peripheral's Name or Services
    def peripheralDidUpdateName_(self, peripheral):
        self.logger.debug("%s updated name " % self)
        self.name = peripheral._.name

    def peripheral_didModifyServices_(self, peripheral, invalidatedServices):
        self.logger.debug("%s updated services" % self)

