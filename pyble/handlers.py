import os
import imp


class PeripheralHandlerMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'handlers'):
            cls.handler = {}
        if not hasattr(cls, 'pool'):
            cls.pool = {}
        if name == "PeripheralHandler":
            return
        cls.pool[name] = cls


class PeripheralHandler(object):
    __metaclass__ = PeripheralHandlerMount

    def __init__(self, peripheral, UUID=""):
        self.peripheral = peripheral
        self.UUID = UUID
        # copy over all existing profile handlers
        self.profile_handlers = dict(ProfileHandler.handlers)

    @property
    def handlers(self):
        return self.profile_handlers

    def keys(self):
        return self.profile_handlers.keys()

    def __getitem__(self, key, default=None):
        try:
            handler_cls = self.profile_handlers[key]
            return handler_cls()
        except KeyError:
            if "*" in self.profile_handlers:
                handler_cls = self.profile_handlers["*"]
                return handler_cls()
            else:
                return default

    def addProfileHandlerPath(self, fpath):
        """ Load all profile hanlders in a directory for this peripheral handler
        """
        pass

    def addProfileHandler(self, handler_cls):
        """ Allow peripheral handler object to use customized profile handler
        """
        self.profile_handlers[handler_cls.UUID] = handler_cls

    def initialize(self):
        pass

    def update_rssi(self, value):
        pass

    def update_name(self, value):
        pass

    def update_services(self, value):
        pass

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass


class ProfileHandlerMount(type):
    # Defaults to . and .profile, append with register_profile_dir
    profile_path = ["."]
    _AUTOLOAD = False

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_handlers'):
            cls._handlers = {}
        if name == "ProfileHandler":
            return
        if cls._AUTOLOAD:
            cls.register_handler(cls)

    @property
    def handlers(self):
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
                    handler_cls = self._handlers[key]
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
                        if mod_obj is None:
                            f, filename, desc = imp.find_module(module, [hpath])
                            globals()[module] = mod_obj = imp.load_module(module, f, filename, desc)


class ProfileHandler(object):
    __metaclass__ = ProfileHandlerMount
    names = {}

    def initialize(self):
        raise NotImplementedError

    def on_read(self, characteristic, data):
        pass

    def on_notify(self, characteristic, data):
        pass

    def on_write(self, characteristic, data):
        pass


class DefaultProfileHandler(ProfileHandler):
    UUID = "*"
    _AUTOLOAD = True

    def on_read(self, characteristic, data):
        ans = []
        for b in data:
            ans.append("0x%02X" % ord(b))
        return " ".join(ans)

    def on_notify(self, characteristic, data):
        print self.on_read(characteristic, data)
