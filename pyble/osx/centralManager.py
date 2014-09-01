from objc import *
from Foundation import *
from IOBluetooth import *

from peripheral import OSXPeripheral
from pyble.roles import Peripheral

import logging
logger = logging.getLogger(__name__)

import uuid
from util import CBUUID2String
import time

class OSXCentralManager(NSObject):
    """
    CentralManager is the host handle for performing scan, connect, disconnect to peripheral(s).
    After a peripheral is connected, a peripheral handle would be returned.

    CBCentralManager Class Reference:
    https://developer.apple.com/librarY/mac/documentation/CoreBluetooth/Reference/CBCentralManager_Class/translated_content/CBCentralManager.html

    CBCentralManagerDelegate Protocol Reference:
    https://developer.apple.com/librarY/mac/documentation/CoreBluetooth/Reference/CBCentralManagerDelegate_Protocol/translated_content/CBCentralManagerDelegate.html
    """

    def init(self):
        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))
        # initialize manager with delegate
        self.logger.info("Initialize CBCentralManager")
        self.manager = CBCentralManager.alloc().initWithDelegate_queue_(self, nil)
        self.scanedList = []
        self.connectedList = []
        self.BLEReady_callback = None
        self.BLEAvailableList_callback = None
        self.BLEConnectedList_callback = None
        return self

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

    def stop(self):
        self.logger.debug("Cleaning Up")

    def startScan(self, allowDuplicates=False):
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

    def stopScan(self):
        self.logger.debug("Stop Scan")
        self.manager.stopScan()

    def getScanedList(self):
        return self.scanedList

    def getConnectedList(self):
        return self.connectedList

    def connectPeripheral(self, peripheral):
        self.logger.debug("Connecting to Peripheral: " + str(peripheral))
        options = NSDictionary.dictionaryWithObject_forKey_(
            NSNumber.numberWithBool_(YES),
            CBConnectPeripheralOptionNotifyOnDisconnectionKey
        )
        peripheral.state = Peripheral.CONNECTING
        self.manager.connectPeripheral_options_(peripheral.instance, options)

    def disconnectAllPeripherals(self):
        self.logger.debug("Disconnecting all Peripherals")
        for p in self.connectedList:
            self.disconnectPeripheral(p)

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
        self.logger.debug("Peripheral %s (%s) is connected" %
                          (peripheral._.name, peripheral._.identifier.UUIDString())
                          )
        p = self.findPeripheralFromList(peripheral, self.scanedList)
        if p:
            if p not in self.connectedList:
                self.connectedList.append(p)
            if p in self.scanedList:
                self.scanedList.remove(p)
            # update peripheral state
            p.state = Peripheral.CONNECTED
        # update lists
        self.updateAvailableList()
        self.updateConnectedList()

    def centralManager_didDisconnectPeripheral_error_(self, central, peripheral, error):
        self.logger.debug("Peripheral %s disconnected" % peripheral._.name)
        p = self.findPeripheralFromList(peripheral, self.connectedList)
        if p:
            p.state = Peripheral.DISCONNECTED
            self.connectedList.remove(p)
            if p in self.scanedList:
                self.scanedList.remove(p)
        # update lists
        self.updateConnectedList()

    def centralManager_didFailToConnectPeripheral_error_(self, central, peripheral, error):
        self.logger.debug("Fail to connect Peripheral %s" % peripheral._.name)
        p = self.findPeripheralFromList(peripheral, self.scanedList)
        if p:
#            self.scanedList.remove(p)
            p.state = Peripheral.DISCONNECTED
        # update lists
        self.updateAvailableList()

    # Discovering and Retrieving Peripherals
    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(self, central, peripheral, advertisementData, rssi):
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
        p.name=peripheral._.name
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
            print p.advIsConnectable
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
        self.logger.debug("didRetrieveConnectedPeripherals")

    def centralManager_didRetrievePeripherals_(self, central, peripherals):
        self.logger.debug("didRetrievePeripherals")

    # Monitoring Changes to the Central Manager's State
    def centralManagerDidUpdateState_(self, central):
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
