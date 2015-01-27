from pyble.handlers import ProfileHandler
import struct

class GenericAccess(ProfileHandler):
    UUID = "1800"
    _AUTOLOAD = True

    def on_read(self, characteristic, data):
        cUUID = characteristic.UUID
        if cUUID == "2A00":
            return str(data)
        elif cUUID == "2A03":
            address = []
            for b in data:
                address.append("%02X" % ord(b))
            return "-".join(address)
        else:
            ans = []
            for b in data:
                ans.append("%02X" % ord(b))
            ret = "0x" + "".join(ans)
            return ret

class DeviceInformation(ProfileHandler):
    UUID = "180A"
    _AUTOLOAD = True

    def on_read(self, characteristic, data):
        cUUID = characteristic.UUID
        if cUUID == "2A23":
            address = []
            for b in data:
                address.append("%02X" % ord(b))
            return "-".join(address)
        else:
            return str(data)

class GenericAttribute(ProfileHandler):
    UUID = "1801"
    _AUTOLOAD = True

    def on_read(self, characteristic, data):
        cUUID = characteristic.UUID
        if cUUID == "2A05" and len(data) == 2:
            try:
                return struct.unpack(">H", data)
            except:
                pass
        ans = []
        for b in data:
            ans.append("%02X" % ord(b))
        ret = "0x" + "".join(ans)
        return ret
