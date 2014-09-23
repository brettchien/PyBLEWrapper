from Foundation import *
from IOBluetooth import *
from objc import *

from pyble._roles import Peripheral
from gatt import OSXBLEService, OSXBLECharacteristic, OSXBLEDescriptor
from util import CBUUID2String

import uuid
import logging
import struct
from pprint import pformat
import time

from threading import Condition

from functools import wraps

from pyble.patterns import Trace

logger = logging.getLogger(__name__)

@Trace
class OSXPeripheral(NSObject, Peripheral):
    """
    Connected Peripheral

    CBPeripheral calss Reference:
    https://developer.apple.com/librarY/mac/documentation/CoreBluetooth/Reference/CBPeripheral_Class/translated_content/CBPeripheral.html

    CBPeripheralDelegate Protocol Reference:
    https://developer.apple.com/library/ios/documentation/CoreBluetooth/Reference/CBPeripheralDelegate_Protocol/translated_content/CBPeripheralDelegate.html
    """
    def init(self):
        Peripheral.__init__(self)
        self.trace.traceInstance(self)

        self.instance = None

        self.cv = Condition()
        self.ready = False
        self.state = Peripheral.DISCONNECTED

        # advertisement data
        self.advLocalName = None
        self.advManufacturerData = None
        self.advServiceUUIDs = []
        self.advServiceData = None
        self.advOverflowServiceUUIDs = []
        self.advIsConnectable = False
        self.advTxPowerLevel = 0
        self.advSolicitedServiceUUIDs = []

        return self

    @property
    def isConnected(self):
        return self.state == Peripheral.CONNECTED

    @property
    def services(self):
        if len(self._services) == 0 and self.instance:
            self.discoverServices()
        return self._services

    @services.setter
    def services(self, value):
        self._services = value

    @property
    def rssi(self):
        # retrive RSSI if peripheral is connected
        if self.state == Peripheral.CONNECTED:
            self.readRSSI()
        return self._rssi

    @rssi.setter
    def rssi(self, value):
        if self._rssi != value:
            self._rssi = value
            self.updateRSSI(self._rssi)

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
        self.updateState()

    # decorators for condition variables
    def _waitResp(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            with self.cv:
                self.ready = False
                func(self, *args, **kwargs)
                while True:
                    self.cv.wait(0)
                    NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantPast())
                    if self.ready:
                        break
        return wrapper

    def _notifyResp(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            self.ready = True
            with self.cv:
                try:
                    self.cv.notifyAll()
                except Exception as e:
                    print e
        return wrapper

    @_waitResp
    def readRSSI(self):
        self.instance.readRSSI()

    @_waitResp
    def discoverServices(self):
        self.instance.discoverServices_(None)

    @_waitResp
    def discoverCharacteristicsForService(self, service):
        self.instance.discoverCharacteristics_forService_(nil, service)

    @_waitResp
    def discoverDescriptorsForCharacteristic(self, characteristic):
        self.instance.discoverDescriptorsForCharacteristic_(characteristic)

    @_waitResp
    def readValueForCharacteristic(self, characteristic):
        self.instance.readValueForCharacteristic_(characteristic)

    @_waitResp
    def readValueForDescriptor(self, descriptor):
        self.instance.readValueForDescriptor_(descriptor)

    @_waitResp
    def writeValueForCharacteristic(self, value, characteristic, withResponse=True):
        writeType = CBCharacteristicWriteWithResponse if withResponse else CBCharacteristicWriteWithoutResponse
        self.instance.writeValue_forCharacteristic_type_(value, characteristic, writeType)

    @_waitResp
    def setNotifyForCharacteristic(self, flag, characteristic):
        self.instance.setNotifyValue_forCharacteristic_(flag, characteristic)

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
    # objc delegate functions cannot be applied with decorators
    # make addtional functions to enable decorators
    # Discovering Services
    def peripheral_didDiscoverServices_(self, peripheral, error):
        self.didDiscoverServices(peripheral, error)

    @_notifyResp
    def didDiscoverServices(self, peripheral, error):
        if error != nil:
            if error._.code == CBErrorNotConnected:
                self.state = Peripheral.DISCONNECTED
            return
        if peripheral._.services:
            self.logger.debug("%s discovered services" % self)
            for service in peripheral._.services:
                s = OSXBLEService(peripheral=self, instance=service)
                self._services.append(s)

    def peripheral_didDiscoverIncludeServicesForService_error_(self, peripheral, service, error):
        self.logger.debug("%s discovered Include Services" % self)

    # Discovering Characteristics and Characteristic Descriptors
    def peripheral_didDiscoverCharacteristicsForService_error_(self, peripheral, service, error):
        self.didDiscoverCharacteristicsForService(peripheral, service, error)

    @_notifyResp
    def didDiscoverCharacteristicsForService(self, peripheral, service, error):
        if error != nil:
            print error
            return
        s = self.findServiceByServiceInstance(service)
        p = s.peripheral
        self.logger.debug("%s:%s discovered characteristics" % (p, s))
        for c in service._.characteristics:
            characteristic = OSXBLECharacteristic(service=s, profile=s, instance=c)
            s.addCharacteristic(characteristic)

    def peripheral_didDiscoverDescriptorsForCharacteristic_error_(self, peripheral, characteristic, error):
        self.didDiscoverDescriptorsForCharacteristic(peripheral, characteristic, error)

    @_notifyResp
    def didDiscoverDescriptorsForCharacteristic(self, peripheral, characteristic, error):
        s = self.findServiceByCharacteristicInstance(characteristic)
        p = s.peripheral
        c = s.findCharacteristicByInstance(characteristic)
        self.logger.debug("%s:%s:%s discovered descriptors" % (p, s, c))
        for d in characteristic._.descriptors:
            descriptor = OSXBLEDescriptor(characteristic=c, instance=d)
            c.addDescriptor(descriptor)

    # Retrieving Characteristic and characteristic Descriptor Values
    def peripheral_didUpdateValueForCharacteristic_error_(self, peripheral, characteristic, error):
        self.didUpdateValueForCharacteristic(peripheral, characteristic, error)

    @_notifyResp
    def didUpdateValueForCharacteristic(self, peripheral, characteristic, error):
        s = self.findServiceByCharacteristicInstance(characteristic)
        p = s.peripheral
        c = s.findCharacteristicByInstance(characteristic)
        value = None
        if error == nil:
            # converting NSData to bytestring
            value = bytes(characteristic._.value)
            c._value = value
            if c.notify:
                c.handler.on_notify(c, value)
            self.logger.debug("%s:%s:%s updated value: %s" % (p, s, c, pformat(value)))
        else:
            self.logger.debug("%s:%s:%s %s" % (p, s, c, str(error)))


    def peripheral_didUpdateValueForDescriptor_error_(self, peripheral, descriptor, error):
        self.didUpdateValueForDescriptor(peripheral, descriptor, error)

    @_notifyResp
    def didUpdateValueForDescriptor(self, peripheral, descriptor, error):
        s = self.findServiceByDescriptorInstance(descriptor)
        p = s.peripheral
        c = self.findCharacteristicByDescriptorInstance(descriptor)
        d = c.findDescriptorByInstance(descriptor)
        value = None
        if error == nil:
            # converting NSData to bytes
            value = bytes(descriptor._.value)
            d.value = value
            self.logger.info("%s:%s:%s:%s updated value: %s" % (p, s, c, d, pformat(value)))
        else:
            self.logger.error("%s:%s:%s:%s %s" % (p, s, c, d, str(error)))

    # Writing Characteristic and Characteristic Descriptor Values
    def peripheral_didWriteValueForCharacteristic_error_(self, peripheral, characteristic, error):
        self.didWriteValueForCharacteristic(peripheral, characteristic, error)

    @_notifyResp
    def didWriteValueForCharacteristic(self, peripheral, characteristic, error):
        s = self.findServiceByCharacteristicInstance(characteristic)
        p = s.peripheral
        c = s.findCharacteristicByInstance(characteristic)
        if error == nil:
            self.logger.debug("Characteristic Value Write Done")
        else:
            self.logger.error("Characteristic Value Write Fail")

    def peripheral_didWriteValueForDescriptor_error_(self, peripheral, descriptor, error):
        if error == nil:
            self.logger.debug("Descriptor Value write Done")
        else:
            self.logger.debug("Descriptor Value write Fail")

    # Managing Notifications for a Characteristic's Value
    def peripheral_didUpdateNotificationStateForCharacteristic_error_(self, peripheral, characteristic, error):
        self.didUpdateNotificationStateForCharacteristic(peripheral, characteristic, error)

    @_notifyResp
    def didUpdateNotificationStateForCharacteristic(self, peripheral, characteristic,  error):
        s = self.findServiceByCharacteristicInstance(characteristic)
        p = s.peripheral
        c = s.findCharacteristicByInstance(characteristic)
        result = "Success"
        if error != nil:
            result = "Fail"
            self.logger.info(error)
            c._notify = False
        else:
            c._notify = True
        self.logger.debug("%s:%s:%s set Notification %s" % (p, s, c, result))

    # Retrieving a Peripheral's Received Signal Strength Indicator(RSSI) Data
    def peripheralDidUpdateRSSI_error_(self, peripheral, error):
        self.didUpdateRSSI(peripheral, error)

    @_notifyResp
    def didUpdateRSSI(self, peripheral, error):
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
        self.logger.info("%s updated name " % self)
        self.name = peripheral._.name

    def peripheral_didModifyServices_(self, peripheral, invalidatedServices):
        self.logger.debug("%s updated services" % self)

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

