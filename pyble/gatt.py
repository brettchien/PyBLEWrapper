#!/usr/bin/env python
import logging
import pkgutil
import profile

logger = logging.getLogger(__name__)

class Service(object):
    def __init__(self):
        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))
        self.name = "UNKNOWN"
        self.UUID = ""
        self.isPrimary = False
        self.characteristics = []

    def __iter__(self):
        return iter(self.characteristics)

    def __eq__(self, other):
        return isinstacne(other, self.__class__) and (other.UUID == self.UUID)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        identifier = ""
        if isinstance(self.UUID, ""):
            identifer = self.UUID
        else:
            identifer = str(self.UUID).upper()
        if self.isPrimary:
            return "*%s <%s>" % (self.name, identifier)
        else:
            return "%s <%s>" % (self.name, identifier)

    def __str__(self):
        return self.__repr__()

class Profile(object):
    def __init__(self):
        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

class Characteristic(object):
    def __init__(self):
        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

class Descriptor(object):
    def __init__(self):
        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

def load_profiles():
    # load default profiles
    package = profile
    for importer, name, isPkg in pkgutil.walk_packages(
        path = package.__path__,
        prefix = package.__name__+".",
        onerror = lambda x: None):
        print(name)
    # load cutomized profiles

