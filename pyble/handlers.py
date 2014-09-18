import os
import imp
import inspect

class PeripheralHandlerMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'handlers'):
            cls.pool = {}
            cls.handler = {}
        if name == "PeripheralHandler":
            return
        cls.pool[name] = cls

class PeripheralHandler(object):
    __metaclass__ = PeripheralHandlerMount

    def __init__(self, UUID=""):
        self.UUID = UUID
        self.profile_handlers = {}

    def initialize(self):
        print "user init"

    def setDelegate(self, UUID, cls_name):
        if cls_name in self.pool:
            handler = cls_name()
            self.handler[UUID] = handler
            for pUUID, pHandler in handler.profile_handlers:
                self.profile_handlers[pUUID] = pHandler()

    def update_rssi(self, value):
        pass

    def update_name(self, value):
        pass

    def update_services(self, value):
        pass

    def on_connect(self, error):
        pass

    def on_disconnect(self, error):
        pass

class ProfileHandlerMount(type):
    # Defaults to . and .profile, append with register_profile_dir
    profile_path = ["."]

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_handlers'):
            cls._handlers = {} 
        if name == "ProfileHandler":
            return
        cls.register_handler(cls)

    @property
    def handlers(self):
#        ProfileHandlerMount.find_handlers()
        return self._handlers

    def keys(self):
        return self._handlers.keys()

    def __getitem__(self, key, retry=True, default=None):
        try:
            handler_cls = self._handlers[key]
            return handler_cls()
        except KeyError:
            if retry:
                ProfileHandlerMount.find_handlers()
                handler_cls = self.__getitem__(key, retry=False)
                if handler_cls:
                    return handler_cls()
                else:
                    # if there is a default handler
                    if "*" in self._handlers:
                        handler_cls = self._handlers["*"]
                        return handler_cls()
                    else:
                        return default
            else:
                return default

    def register_handler(cls, handler_cls):
        if hasattr(handler_cls, "UUID"):
            if handler_cls not in cls._handlers:
                cls._handlers[handler_cls.UUID] = handler_cls
        else:
            print "An UUID is needed for a ProfileHandler"

    @staticmethod
    def register_path(profile_path):
        if os.path.isdir(profile_path):
            ProfileHandlerMount.profile_path.append(profile_path)
        else:
            raise EnvironmentError("%s is not a directory" % profile_path)

    @staticmethod
    def find_handlers():
        handler_path = ProfileHandlerMount.profile_path
        for hpath in handler_path:
            hpath = os.path.abspath(hpath)
            if os.path.isdir(hpath):
                for file_ in os.listdir(hpath):
                    if file_.endswith('.py') and file_ not in ["__init__.py", "setup.py"]:
                        module = file_[:-3]
                        mod_obj = globals().get(module)
                        if mod_obj == None:
                            f, filename, desc = imp.find_module(module, [hpath])
                            globals()[module] = mod_obj = imp.load_module(module, f, filename, desc)

class ProfileHandler(object):
    __metaclass__ = ProfileHandlerMount
        
    def initialize(self):
        raise NotImplementedError

    def on_read(self, characteristic, data):
        pass

    def on_write(self, characteristic, data):
        pass

class DefaultProfileHandler(ProfileHandler):
    UUID = "*"

    def on_read(self, characteristic, data):
        ans = []
        for b in data:
            ans.append("0x%02X" % ord(b))
        return " ".join(ans)
