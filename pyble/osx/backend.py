# objective-c frameworks
from objc import *
from Foundation import *

# CBCentralManager Bluetooth 4.0 worker
from centralManager import OSXCentralManager

# HCI command
from hci import OSXHCICommand
#from gatt import Service, Profile, Characteristic

from threading import Thread, Event
import logging

from console import OSXCmd
import os
from pprint import pformat

try:
    from Queue import Queue, Empty
except:
    from queue import Queue, Empty

logger = logging.getLogger(__name__)

from pyble.roles import Peripheral

class OSXPeripheralApp(OSXCmd):
    def __init__(self, p):
        # init. super class
        try:
            self.parent = super()
        except:
            self.parent = super(OSXPeripheralApp, self)
        self.parent.__init__()
        self.p = p
        self.prompt = "P{%s}$ " % (p.name)

        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))

        self.services = []
        self.rssi = 0

    def preloop(self):
        self.parent.preloop()
        # register callbacks
        self.p.setNotifyRSSI(self._update_rssi)
        self.p.setNotifyState(self._update_state)

    # callbacks
    def _update_rssi(self, rssi):
        self.stdout.write("Peripheral RSSI: %d\n" % rssi)
        self.rssi = rssi

    def _update_state(self, state):
        if state == Peripheral.DISCONNECTED:
            self.stdout.write("Peripheral disconnected, exit ...")
            self.stdout.flush()
            self.endloop()

    def do_show(self, args):
        """Show the Profile structure
        """
        pass

    def do_list(self, args):
        """Show peripheral supported services
        """
        for service in self.p.services:
            print service

    def do_read(self, args):
        arglist = args.split()
        if len(arglist) == 1:
            # read whole profile
            pUUID = arglist[0]
            try:
                pUUID = pUUID.lstrip("0x").upper()
            except:
                return
            profile = self.p[pUUID]
            print profile
            for c in profile:
                print c
                print c.value
            
        elif len(arglist) == 2:
            # read a char in profile
            profile = arglist[0]
            char = arglist[1]
        else:
            self.help_read()


    def help_read(self):
        self.stdout.write("Read Profile\n")
        self.stdout.write("Usage: read <Profile UUID> [characteristic UUID]\n")
        self.stdout.write("Example: read 180A\n")
        self.stdout.write("         read 180A 2905\n")
        self.stdout.flush()

    def do_write(self, args):
        pass

    def do_state(self, args):
        """Show Peripheral state
        """
        print self.p
        print self.p.rssi

    def do_discover(self, args):
        """Discover Peripheral provided services
        """
        self.p.discoverServices()

 
class OSXCentralManagerApp(OSXCmd):
    def __init__(self, shell=False):
        # init. super class
        try:
            self.parent = super()
        except:
            self.parent = super(OSXCentralManagerApp, self)
        self.parent.__init__()
        self.prompt = "EcoBLE $ "

        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))
        # init. CoreBluetooth Central Manager
        self.centralManager = OSXCentralManager.alloc().init()
        # register callbacks
        self.centralManager.setBLEReadyCallback(self._setReady)
        self.centralManager.setBLEAvailableListCallback(self._updateAvailableList)
        self.centralManager.setBLEConnectedListCallback(self._updateConnectedList)

        # process control
        self.stop = Event()
        self.stop.clear()
        self.ready = False

        self.hciTool = OSXHCICommand(self.centralManager)

        self.shell = shell
        self.inq = None
        self.outq = None
        if not self.shell:
            self.inq = Queue()
            self.outq = Queue()

        # init. variables
        self.availablePeripherals = []
        self.connectedPeripherals = []

    # callbacks
    def _setReady(self):
        self.ready = True

    def _updateConnectedList(self, connectedList):
        self.logger.debug("Connected List updated!")
        self.connectedPeripherals = connectedList

    def _updateAvailableList(self, availableList):
        self.logger.debug("Available List updated!")
        self.availablePeripherals = availableList

    def getTunnels(self):
        return (self.inq, self.outq)

    def isReady(self):
        return self.ready

    def start(self):
        self.parent.preloop()
        # python process and osx process co-existence
        while (not self.stop.is_set()):
            self.osx_runloop.runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantPast())
            
            try:
                msg = self.inq.get_nowait()
                self.handleMessage(msg)
                self.inq.task_done()
            except Empty:
                pass
            except Exception as e:
                self.logger.error(str(e))
                self.halt()

        # termination
        self.parent.postloop()

    def do_EOF(self, line):
        return self.do_exit(line)

    def default(self, line):
        cmd, arg, line = self.parseline(line)
        self.commandNotFound(cmd)

    def handleMessage(self, msg):
        self.onecmd(msg)

    def commandNotFound(self, cmd):
        print "Command: %s is not yet support by %s" % (cmd, self.__class__.__name__)

    def do_exit(self, args):
        """ Exit Program
        """
        if len(self.connectedPeripherals):
            self.hciTool.disconnectAll()
        self.halt()
        return True

    def do_scan(self, args):
        """Scan available peripherals 
        """
        self.hciTool.startScan()

    def do_stop(self, args):
        """Stop scan command
        """
        self.hciTool.stopScan()

    def do_list(self, args):
        """List available peripherals
        """
        count = 0
        ans = ""
        for p in self.availablePeripherals:
            ans += "%2d : %s\n" % (count, p.name)
            ans += "     RSSI         : %d\n" % p.rssi
            ans += "     TxPowerLevel : %d\n" % p.advTxPowerLevel
            ans += "     Service UUIDs: %s\n" % pformat(p.advServiceUUIDs)
            count += 1
        self.stdout.write(ans)
        self.stdout.flush()

    def do_con(self, args):
        """List connected peripherals
        """
        count = 0
        ans = ""
        for p in self.connectedPeripherals:
            ans += "%2d : %s\n" % (count, p.name)
            ans += "     RSSI         : %d\n" % p.rssi
            ans += "     TxPowerLevel : %d\n" % p.advTxPowerLevel
            ans += "     Service UUIDs: %s\n" % pformat(p.advServiceUUIDs)
            count += 1
        self.stdout.write(ans)
        self.stdout.flush()

    def do_execute(self, args):
        """Enter shell of connected peripheral N
        """
        pid = None
        try:
            pid = int(args.strip())
        except:
            pass
        if pid == None and len(self.connectedPeripherals):
             p = self.connectedPeripherals[0]
             OSXPeripheralApp(p).cmdloop()
        if pid != None and pid < len(self.connectedPeripherals):
             p = self.connectedPeripherals[pid]
             OSXPeripheralApp(p).cmdloop()

    def do_connect(self, args):
        """Connect to a specific peripheral
        """
        pid = None
        try:
            pid = int(args.strip())
        except:
            pass
        if pid == None and len(self.availablePeripherals):
            self.hciTool.connect(self.availablePeripherals[0])
        if pid != None and pid < len(self.availablePeripherals):
            self.hciTool.connect(self.availablePeripherals[pid])

    def do_disconnect(self, args):
        """Disconnect a connected peripheral
        """
        pid = None
        try:
            pid = int(args.strip())
        except:
            pass
        if pid == None and len(self.connectedPeripherals):
            self.hciTool.disconnect(self.connectedPeripherals[0])
        if pid != None and pid < len(self.connectedPeripherals):
            self.hciTool.disconnect(self.connectedPeripherals[pid])

    def do_connectAll(self, args):
        """Connect all available peripherals
        """
        if len(self.availablePeripherals):
            for p in self.availablePeripherals:
                self.hciTool.connect(p)

    def do_disconnectAll(self, args):
        """Disconnect all connected peripherals
        """
        self.hciTool.disconnectAll()

    def halt(self):
        self.stop.set()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = OSXCentralManagerApp(shell=True)
    print app
    try:
        app.cmdloop()
    except Exception as e:
        print e

