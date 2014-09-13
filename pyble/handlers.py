
class PeripheralHandlerMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'handlers'):
            cls.handlers = []
        else:
            print "register handlers"
            cls.register_handler(cls)

    def register_handler(cls, handler):
        instance = handler()
        cls.handlers.append(instance)
        print cls.handlers

    def on_read(self, data):
        pass

    def haha(self):
        pass

class PeripheralHandler(object):
    __metaclass__ = PeripheralHandlerMount

class ProfileHandlerMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'handlers'):
            cls.handlers = []
        else:
            cls.register_handler(cls)

    def register_handler(cls, handler):
        instance = handler()
        cls.handlers.append(instance)

class ProfileHandler(object):
    __metaclass__ = ProfileHandlerMount
        
