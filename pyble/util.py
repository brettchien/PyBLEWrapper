import const

import pkgutil
import re

def load():
    ret = {}
    for importer, name, isPkg in pkgutil.walk_packages(path=const.__path__, prefix=const.__name__+"."):
        if not isPkg:
            _pkg = __import__(name, fromlist=["*"])
            if "UUID" in _pkg.__dict__:
                ret[_pkg.NAME] = (name, _pkg.UUID)
            else:
                ret[_pkg.NAME] = (name, 0)
    return ret

def loadBy(category):
    if category not in ["service", "profie", "characteristc"]:
        print("Only service, profile, characteristic are valid categories")
        return None
    ret = {}
    for importer, name, isPkg in pkgutil.walk_packages(path=const.__path__, prefix=const.__name__+"."):
        if not isPkg:
            if re.search("\."+category+"\.", name):
                _pkg = __import__(name, fromlist=["*"])
                if "UUID" in _pkg.__dict__:
                    ret[_pkg.NAME] = (name, _pkg.UUID)
                else:
                    ret[_pkg.NAME] = (name, 0)
    return ret

def resolveUUIDFromName(uuids, name):
    if name in uuids:
        return uuids[name]
    else:
        return None

def resolveNameFromUUID(uuids, uuid):
    for k, v in uuids.items():
        if v[1] == uuid:
            return k
    return None

if __name__ == "__main__":
    from pprint import pprint
    d = load()
    print(resolveNameFromUUID(d, 0x180D))
    print(resolveUUIDFromName(d, "Tx Power"))
    d = loadBy("characteristic")
    pprint(d)
    d = loadBy("test")
