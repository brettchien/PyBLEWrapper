from __future__ import absolute_import

import os
import inspect

# loading base classes
from ._roles import Peripheral as PeripheralBase
from ._roles import Central as CentralBase

from ._gatt import Service as ServiceBase
from ._gatt import Profile as ProfileBase
from ._gatt import Characteristic as CharacteristicBase
from ._gatt import Descriptor as DescriptorBase

# loading profiles
from .handlers import ProfileHandler
from . import profile

default_profilepath = os.path.abspath(os.path.dirname(inspect.getfile(profile)))
ProfileHandler.register_path(default_profilepath)
#ProfileHandler.find_handlers()


# loading customized class base on operating system
class Peripheral(object):
    def __new__(cls, *args, **kwargs):
        import platform
        system = platform.system()
        if system == "Darwin":
            from .osx.peripheral import OSXPeripheral
            return OSXPeripheral.alloc().init()
        elif system == "Linux":
            pass
        else:
            # windows
            pass
        return None


class CentralManager(object):
    def __new__(cls, *args, **kwargs):
        import platform
        system = platform.system()
        if system == "Darwin":
            from .osx.centralManager import OSXCentralManager
            return OSXCentralManager.alloc().init()
        elif system == "Linux":
            pass
        else:
            # windows
            pass


class Service(object):
    def __new__(cls, *args, **kwargs):
        import platform
        system = platform.system()
        if system == "Darwin":
            from .osx.gatt import OSXBLEService
            return OSXBLEService(*args, **kwargs)
        elif system == "Linux":
            pass
        else:
            # windows
            pass


class Profile(object):
    def __new__(cls, *args, **kwargs):
        import platform
        system = platform.system()
        if system == "Darwin":
            from .osx.gatt import OSXBLEService
            return OSXBLEService(*args, **kwargs)
        elif system == "Linux":
            pass
        else:
            # windows
            pass


class Characteristic(object):
    def __new__(cls, *args, **kwargs):
        import platform
        system = platform.system()
        if system == "Darwin":
            from .osx.gatt import OSXBLECharacteristic
            return OSXBLECharacteristic(*args, **kwargs)
        elif system == "Linux":
            pass
        else:
            # windows
            pass


class Descriptor(object):
    def __new__(cls, *args, **kwargs):
        import platform
        system = platform.system()
        if system == "Darwin":
            from .osx.gatt import OSXBLEDescriptor
            return OSXBLEDescriptor(*args, **kwargs)
        elif system == "Linux":
            pass
        else:
            # windows
            pass
