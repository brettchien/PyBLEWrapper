import objc

# Load IOBluetooth
objc.loadBundle('IOBluetooth', globals(),
                bundle_path=objc.pathForFramework("IOBluetooth.framework"))

# IOBluetooth CBCentralManager state CONSTS
CBCentralManagerStateUnkown = 0
CBCentralManagerStateResetting = 1
CBCentralManagerStateUnsupported = 2
CBCentralManagerStateUnauthorized = 3
CBCentralManagerStatePoweredOff = 4
CBCentralManagerStatePoweredOn = 5

# CBCentralManager option keys
CBCentralManagerScanOptionAllowDuplicatesKey = u"kCBScanOptionAllowDuplicates"
CBConnectPeripheralOptionNotifyOnDisconnectionKey = u"kCBConnectOptionNotifyOnDisconnection"

# CBCharacteristicWriteType CONSTS
CBCharacteristicWriteWithResponse = 0
CBCharacteristicWriteWithoutResponse = 1

# ADvertisement Data Retrieval Keys
CBAdvertisementDataLocalNameKey = u"kCBAdvDataLocalName"
CBAdvertisementDataManufacturerDataKey = u"kCBAdvDataManufacturerData"
CBAdvertisementDataServiceDataKey = u"kCBAdvDataServiceData"
CBAdvertisementDataServiceUUIDsKey = u"kCBAdvDataServiceUUIDs"
CBAdvertisementDataOverflowServiceUUIDsKey = u"kCBAdvDataOverflowService"
CBAdvertisementDataTxPowerLevelKey = u"kCBAdvDataTxPowerLevel"
CBAdvertisementDataIsConnectable = u"kCBAdvDataIsConnectable"
CBAdvertisementDataSolicitedServiceUUIDsKey = u"kCBAdvDataSolicitedServiceUUIDs"


# CBError Constants
CBErrorUnknown = 0
CBErrorInvalidParameters = 1
CBErrorInvalidHandle = 2
CBErrorNotConnected = 3
CBErrorOutOfSpace = 4
CBErrorOperationCancelled = 5
CBErrorConnectionTimeout = 6
CBErrorPeripheralDisconnected = 7
CBErrorUUIDNotAllowed = 8
CBErrorAlreadyAdvertising = 9

# CBATTError Constants
CBATTErrorSuccess = 0x00
CBATTErrorInvalidHandle = 0x01
CBATTErrorReadNotPermitted = 0x02
CBATTErrorWriteNotPermitted = 0x03
CBATTErrorInvalidPdu = 0x04
CBATTErrorInsufficientAuthentication = 0x05
CBATTErrorRequestNotSupported = 0x06
CBATTErrorInvalidOffset = 0x07
CBATTErrorInsufficientAuthorization = 0x08
CBATTErrorPrepareQueueFull = 0x09
CBATTErrorAttributeNotFound = 0x0A
CBATTErrorAttributeNotLong = 0x0B
CBATTErrorInsufficientEncryptionKeySize = 0x0C
CBATTErrorInvalidAttributeValueLength = 0x0D
CBATTErrorUnlikelyError = 0x0E
CBATTErrorInsufficientEncription = 0x0F
CBATTErrorUnsupportedGroupType = 0x10
CBATTErrorInsufficientResources = 0x11
