from pyble.handlers import ProfileHandler

class BatteryService(ProfileHandler):
    UUID = "180F"
    _AUTOLOAD = True

    def on_read(self, characteristic, data):
        cUUID = characteristic.UUID
        if cUUID == "2A19":
            ret = str(ord(data)) + '%'
            return ret
        else:
            ans = []
            for b in data:
                ans.append("%02X" % ord(b))
            ret = "0x" + "".join(ans)
            return ret

