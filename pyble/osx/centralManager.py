from objc import *
from Foundation import *
from IOBluetooth import *

from pyble._roles import Central, Peripheral
from peripheral import OSXPeripheral

import logging
logger = logging.getLogger(__name__)

import uuid
from util import CBUUID2String
from datetime import datetime, timedelta
from pyble.patterns import Trace
from threading import Thread, Condition, Event
from functools import wraps

class BLETimeoutError(Exception):
    def __init__(self, message=""):
        Exception.__init__(self, message)
        self.message = message

class BLECentralManagerStateError(Exception):
    def __init__(self, message=""):
        Exception.__init__(self, message)
        self.message = message

@Trace
class OSXCentralManager(NSObject, Central):
    """
    CentralManager is the host handle for performing scan, connect, disconnect to peripheral(s).
    After a peripheral is connected, a peripheral handle would be returned.

    CBCentralManager Class Reference:
    https://developer.apple.com/librarY/mac/documentation/CoreBluetooth/Reference/CBCentralManager_Class/translated_content/CBCentralManager.html

    CBCentralManagerDelegate Protocol Reference:
    https://developer.apple.com/librarY/mac/documentation/CoreBluetooth/Reference/CBCentralManagerDelegate_Protocol/translated_content/CBCentralManagerDelegate.html
    """

    def init(self):
        try:
            super().__init__()
        except:
            super(OSXCentralManager, self).__init__()
        # enable trace
        self.trace.traceInstance(self)
        # initialize manager with delegate
        self.logger.info("Initialize CBCentralManager")
        self.manager = CBCentralManager.alloc().initWithDelegate_queue_(self, nil)

        self.scanedList = []
        self.connectedList = []
        self.BLEReady_callback = None
        self.BLEAvailableList_callback = None
        self.BLEConnectedList_callback = None

        self.cv = Condition()
        self.ready = False
        self.wait4Startup()
        self._stop = Event()

        return self

    # decorators for condition variables
    def _waitResp(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            with self.cv:
                self.ready = False
                ret = func(self, *args, **kwargs)
                while True:
                    self.cv.wait(0)
                    NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantPast())
                    if self.ready:
                        break
                return ret
        return wrapper

    def _notifyResp(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            ret = func(self, *args, **kwargs)
            self.ready = True
            with self.cv:
                try:
                    self.cv.notify()
                except Exception as e:
                    print e
            return ret
        return wrapper

    @_waitResp
    def wait4Startup(self):
        self.logger.debug("Waiting CentralManager to be ready ...")

    def setBLEReadyCallback(self, func):
        self.BLEReady_callback = func

    def setBLEAvailableListCallback(self, func):
        self.BLEAvailableList_callback = func

    def setBLEConnectedListCallback(self, func):
        self.BLEConnectedList_callback = func

    def updateAvailableList(self):
        if self.BLEAvailableList_callback:
            try:
                self.BLEAvailableList_callback(self.scanedList)
            except:
                pass

    def updateConnectedList(self):
        if self.BLEConnectedList_callback:
            try:
                self.BLEConnectedList_callback(self.connectedList)
            except:
                pass

    def loop(self, duration=0):
        if duration == 0:
            self.logger.info("Stop the loop by Ctrl+C ...")
        startTime = datetime.now()
        while True:
            try:
                NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantPast())
                if duration > 0 and datetime.now() - startTime > timedelta(seconds=duration):
                    break
                if self._stop.isSet():
                    break
            except KeyboardInterrupt:
                print "\nEnd loop ..."
                break

    def stop(self):
        self._stop.set()

    def startScan(self, withServices=[], timeout=5, numOfPeripherals=1, allowDuplicates=False):
        self.logger.debug("Start Scan")

        if len(self.scanedList):
            del self.scanedList
        self.scanedList = []

        if allowDuplicates:
            value = NSNumber.numberWithBool_(YES)
        else:
            value = NSNumber.numberWithBool_(NO)
        options = NSDictionary.dictionaryWithObject_forKey_(
            value,
            CBCentralManagerScanOptionAllowDuplicatesKey
        )
        self.manager.scanForPeripheralsWithServices_options_(nil, options)

        startTime = datetime.now()
        with self.cv:
            while True:
                self.cv.wait(0.1)
                NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantPast())
                if timeout > 0 and datetime.now() - startTime > timedelta(seconds=timeout):
                    self.stopScan()
                    raise BLETimeoutError("Scan timeout after %s seconds!!" % timeout)
                if len(withServices):
                    if len(self.scanedList):
                        tmpList = self.scanedList[:]
                        self.scanedList = []
                        for service in withServices:
                            for p in tmpList:
                                if service in p.advServiceUUIDs:
                                    self.scanedList.append(p)
                if numOfPeripherals > 0 and len(self.scanedList) >= numOfPeripherals:
                    self.logger.info("Found %s peripherals." % len(self.scanedList))
                    break
        self.stopScan()

        # return the first found peripheral
        if len(self.scanedList):
            return self.scanedList[0]
        return None
 
    def stopScan(self):
        self.logger.debug("Stop Scan")
        self.manager.stopScan()

    def getScanedList(self):
        return self.scanedList

    def getConnectedList(self):
        return self.connectedList

    @_waitResp
    def retrieveConnectedPeripherals(self):
        self.logger.info("Deprecated in OSX v10.9.")
        return 
#        self.manager.retrieveConnectedPeripherals()

    def retrieveConnectedPeripheralsWithServices(self, services):
        if not isinstance(services, list) and isinstance(services, str):
            services = list(services.split())
        known_services = NSMutableArray.alloc().init()
        for service in services:
            UUID = CBUUID.UUIDWithString_(service)
            if UUID is not nil:
                known_services.addObject_(UUID)
        peripherals = self.manager.retrieveConnectedPeripheralsWithServices_(known_services)
        for p in peripherals:
            if not self.findPeripheralFromList(p, self.scanedList):
                temp = OSXPeripheral.alloc().init()
                temp.instance = p
                temp.UUID = uuid.UUID(p._.identifier.UUIDString())
                temp.name=p._.name
                self.scanedList.append(temp)
        # update lists
        self.updateAvailableList()

    def retrievePeriphersWithIdentifiers(self, identifiers):
        if not isinstance(identifiers, list) and isinstance(identifiers, str):
            identifiers = list(identifiers.split())
        known_identifiers = NSMutableArray.alloc().init()
        for identifier in identifiers:
            UUID = NSUUID.alloc().UUIDWithString_(identifer)
            if UUID is not nil:
                known_identifiers.addObject_(UUID)
        peripherals = self.manager.retrievePeripheralsWithIdentifiers_(known_identifiers)
        for p in peripherals:
            if not self.findPeripheralFromList(p, self.scanedList):
                temp = OSXPeripheral.alloc().init()
                temp.instance = p
                temp.UUID = uuid.UUID(p._.identifier.UUIDString())
                temp.name=p._.name
                self.scanedList.append(temp)
        # update lists
        self.updateAvailableList()

    def connectPeripheral(self, peripheral):
        with self.cv:
            self.ready = False
            self.logger.debug("Connecting to Peripheral: " + str(peripheral))
            options = NSDictionary.dictionaryWithObject_forKey_(
                        NSNumber.numberWithBool_(YES),
                        CBConnectPeripheralOptionNotifyOnDisconnectionKey
                      )
            peripheral.state = Peripheral.CONNECTING
            self.manager.connectPeripheral_options_(peripheral.instance, options)

            while True:
                self.cv.wait(0)
                NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantPast())
                if self.ready == True:
                    break

        # return the newly added peripheral
        if peripheral in self.connectedList:
            return peripheral
        return None
 
    def disconnectAllPeripherals(self):
        self.logger.debug("Disconnecting all Peripherals")
        for p in self.connectedList:
            self.disconnectPeripheral(p)

    @_waitResp
    def disconnectPeripheral(self, peripheral):
        self.logger.debug("Disconnecting Peripheral: " + str(peripheral))
        self.manager.cancelPeripheralConnection_(peripheral.instance)

    @staticmethod
    def findPeripheralFromList(peripheral, peripherals):
        name = peripheral._.name
        UUID = uuid.UUID(peripheral._.identifier.UUIDString())
        for p in peripherals:
            if not isinstance(p, Peripheral):
                return None
            if name == p.name and UUID == p.UUID:
                return p
        return None

    # CBCentralManager delegate methods
    # Monitoring Connections with Peripherals
    def centralManager_didConnectPeripheral_(self, central, peripheral):
        self.didConnectPeripheral(central, peripheral)

    @_notifyResp
    def didConnectPeripheral(self, central, peripheral):
        self.logger.info("Peripheral %s (%s) is connected" %
                          (peripheral._.name, peripheral._.identifier.UUIDString())
                          )
        p = self.findPeripheralFromList(peripheral, self.scanedList)
        if p:
            if p not in self.connectedList:
                self.connectedList.append(p)
            self.scanedList.remove(p)
            # update peripheral state
            p.state = Peripheral.CONNECTED

        # update lists
        self.updateAvailableList()
        self.updateConnectedList()

    def centralManager_didDisconnectPeripheral_error_(self, central, peripheral, error):
        self.didDisconnectPeripheral(central, peripheral, error)

    @_notifyResp
    def didDisconnectPeripheral(self, central, peripheral, error):
        self.logger.info("Peripheral %s is disconnected" % peripheral._.name)
        p = self.findPeripheralFromList(peripheral, self.connectedList)
        if p:
            p.state = Peripheral.DISCONNECTED
            self.connectedList.remove(p)
            if p not in self.scanedList:
                self.scanedList.append(p)
        # update lists
        self.updateConnectedList()

    def centralManager_didFailToConnectPeripheral_error_(self, central, peripheral, error):
        self.didFailtoConnectPeripheral(central, peripheral, error)

    @_notifyResp
    def didFailtoConnectPeripheral(self, central, peripheral, error):
        self.logger.debug("Fail to connect Peripheral %s" % peripheral._.name)
        p = self.findPeripheralFromList(peripheral, self.scanedList)
        if p:
            p.state = Peripheral.DISCONNECTED
        # update lists
        self.updateAvailableList()

    # Discovering and Retrieving Peripherals
    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(self, central, peripheral, advertisementData, rssi):
        self.didDiscoverPeripheral(central, peripheral, advertisementData, rssi)

    @_notifyResp
    def didDiscoverPeripheral(self, central, peripheral, advertisementData, rssi):
        temp = OSXPeripheral.alloc().init()
        idx = -1
        p = None
        try:
            idx = self.scanedList.index(temp)
        except ValueError:
            idx = -1
        except Exception as e:
            self.logger.error(str(e))
        if idx >= 0:
            p = self.scanedList[idx]
        else:
            p = temp

        p.instance = peripheral
        p.UUID = uuid.UUID(peripheral._.identifier.UUIDString())
        p.name = peripheral._.name
        # handle advertisement data
        #   local name
        if CBAdvertisementDataLocalNameKey in advertisementData:
            p.advLocalName = advertisementData[CBAdvertisementDataLocalNameKey]
        #   manufacturer data
        if CBAdvertisementDataManufacturerDataKey in advertisementData: 
            p.advManufacturerData = advertisementData[CBAdvertisementDataManufacturerDataKey]
        #   provided services UUIDs
        if CBAdvertisementDataServiceUUIDsKey in advertisementData: 
            p.advServiceUUIDS = []
            UUIDs = advertisementData[CBAdvertisementDataServiceUUIDsKey]
            for UUID in UUIDs:
                p.advServiceUUIDs.append(CBUUID2String(UUID._.data))
        #   Tx Power Level
        if CBAdvertisementDataTxPowerLevelKey in advertisementData:
            p.advTxPowerLevel = int(advertisementData[CBAdvertisementDataTxPowerLevelKey])
        #   ServiceData
        if CBAdvertisementDataServiceDataKey in advertisementData:
            p.advServiceData = advertisementData[CBAdvertisementDataServiceDataKey]
        #   OverflowServiceUUIDs
        if CBAdvertisementDataOverflowServiceUUIDsKey in advertisementData:
            p.advOverflowServiceUUIDs = []
            UUIDs = advertisementData[CBAdvertisementDataOverflowServiceUUIDsKey]
            for UUID in UUIDs:
                p.advOverflowServiceUUIDs.append(CBUUID2String(UUID._.data))
        #   IsConnectable 
        if CBAdvertisementDataIsConnectable in advertisementData:
            p.advIsConnectable = advertisementData[CBAdvertisementDataIsConnectable]
        #   SolicitedServiceUUIDs
        if CBAdvertisementDataSolicitedServiceUUIDsKey in advertisementData:
            p.advSolicitedServiceUUIDs = []
            UUIDs = advertisementData[CBAdvertisementDataSolicitedServiceUUIDsKey]
            for UUID in UUIDs:
                p.advSolicitedServiceUUIDs.append(CBUUID2String(UUID._.data))
        # RSSI
        p.rssi = rssi

        if p not in self.scanedList:
            self.scanedList.append(p)
            self.logger.info("Found Peripheral %s", peripheral._.name)
            self.logger.info("RSSI: %d", rssi)
            self.logger.info("UUID: %s", peripheral._.identifier.UUIDString())
            self.logger.info("State: %s", peripheral._.state)

        # update lists
        self.updateAvailableList()

    def centralManager_didRetrieveConnectedPeripherals_(self, central, peripherals):
        self.didRetrieveConnectedPeripherals(central, peripherals)

    @_notifyResp
    def didRetrieveConnectedPeripherals(self, central, peripherals):
        self.logger.info("Deprecated in OSX v10.9.")
        return 
        self.logger.info("didRetrieveConnectedPeripherals")
        for p in peripherals:
            print p

    def centralManager_didRetrievePeripherals_(self, central, peripherals):
        self.logger.info("didRetrievePeripherals")

    # Monitoring Changes to the Central Manager's State
    def centralManagerDidUpdateState_(self, central):
        self.didUpdateState(central)

    @_notifyResp
    def didUpdateState(self, central):
        ble_state = central._.state
        if ble_state == CBCentralManagerStateUnkown:
            self.logger.debug("CentralManager State: Unkown")
        elif ble_state == CBCentralManagerStateResetting:
            self.logger.debug("CentralManager State: Resetting")
        elif ble_state == CBCentralManagerStateUnsupported:
            self.logger.debug("CentralManager State: Unsupported")
        elif ble_state == CBCentralManagerStateUnauthorized:
            self.logger.debug("CentralManager State: Unauthorized")
        elif ble_state == CBCentralManagerStatePoweredOff:
            self.logger.debug("CentralManager State: PoweredOff")
        elif ble_state == CBCentralManagerStatePoweredOn:
            self.logger.debug("CentralManager State: PoweredOn")
            self.logger.info("BLE is ready!!")
            if self.BLEReady_callback:
                try:
                    self.BLEReady_callback()
                except Exception as e:
                    self.logger.error("BLEReady_callback error")
                    self.logger.error(str(e))
        else:
            self.logger.info("Cannot get CBCentralManager's state!!")
            raise BLECentralManagerStateError

    def centralManager_willRestoreState_(self, central, dict):
        pass
