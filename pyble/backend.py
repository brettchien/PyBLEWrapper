from __future__ import absolute_import

# objective-c frameworks
from objc import *
from Foundation import *

from pyble.patterns import Trace, TraceObject
from pyble._roles import Central, Peripheral

# CBCentralManager Bluetooth 4.0 worker
from osx.centralManager import OSXCentralManager, BLETimeoutError

from threading import Thread, Event
import logging

from osx.console import OSXCmd
import os
from osx.util import readDeviceInfo
from pprint import pformat

try:
    from Queue import Queue, Empty
except:
    from queue import Queue, Empty

logger = logging.getLogger(__name__)

import atexit


@Trace
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

        self.rssi = 0

    def preloop(self):
        self.parent.preloop()
        # register callbacks
        self.p.setNotifyRSSI(self._update_rssi)
        self.p.setNotifyState(self._update_state)

    # callbacks
    def _update_rssi(self, rssi):
        self.rssi = rssi
        self.prompt = "P{%s} (RSSI:%d) $ " % (self.p.name, self.rssi)

    def _update_state(self, state):
        if state == Peripheral.DISCONNECTED:
            self.stdout.write("Peripheral disconnected, exit ...\n")
            self.stdout.flush()
            self.endloop()

    def do_debug(self, args):
        """Enable/disable peripheral debugging information
        """
        OSXCmd.do_debug(self, args)
        option = args.strip()
        if option == "":
            pass
        elif option == "True":
            self.p.debug = True
        elif option == "False":
            self.p.debug = False
        else:
            self.stdout.write("Only accept True/False\n")
        ans = "%s is %sin debug mode.\n"
        if self.p.debug:
            ans = ans % (self.p, "")
        else:
            ans = ans % (self.p, "not ")
        self.stdout.write(ans)
        self.stdout.flush()

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
                print " ", c
                print "    Description: ", c.description
                print "    Value      : ", c.value

        elif len(arglist) == 2:
            # read a char in profile
            pUUID = arglist[0]
            cUUID = arglist[1]
            profile = self.p[pUUID]
            char = self.p[pUUID][cUUID]
            print char, ":", char.value
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


@Trace
class OSXCentralManagerApp(OSXCmd):
    def __init__(self, shell=False):
        # init. super class
        try:
            super().__init__()
        except:
            super(OSXCentralManagerApp, self).__init__()
        atexit.register(self.exitApp, self)
        self.prompt = "EcoBLE $ "
        # read host BLE info
        self.dongle = readDeviceInfo()
        self.prompt = "EcoBLE(%s) $ " % self.dongle.MACAddress

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

        self.shell = shell
        self.inq = None
        self.outq = None
        if not self.shell:
            self.inq = Queue()
            self.outq = Queue()

        # init. variables
        self.availablePeripherals = []
        self.connectedPeripherals = []

        self.trace = TraceObject()

    @staticmethod
    def exitApp(instance):
        instance.do_exit("")
        instance.stdout.flush()
        sys.settrace(None)

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
        OSXCmd.preloop()
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
        OSXCmd.postloop()

    def do_EOF(self, line):
        return self.do_exit(line)

    def handleMessage(self, msg):
        self.onecmd(msg)

    def do_exit(self, args):
        """ Exit Program
        """
        if hasattr(self, 'connectedPeripherals') and len(self.connectedPeripherals):
            self.do_disconnectAll("")
        return True

    def do_scan(self, args):
        """Scan available peripherals
        """
        seconds = 3
        num = 1
        args = args.strip()
        args = args.split()
        nargs = len(args)
        if nargs == 1:
            try:
                seconds = int(args[0])
            except:
                pass
        elif nargs == 2:
            try:
                seconds = int(args[0])
                num = int(args[1])
            except:
                pass
        else:
            pass

        try:
            self.centralManager.startScan(timeout=seconds, numOfPeripherals=num)
        except BLETimeoutError as e:
            print e

    def do_stop(self, args):
        """Stop scan command
        """
        self.centralManager.stopScan()

    def do_list(self, args):
        """List available and connected peripherals
        """
        count = 0
        ans = "== Avaialbe Peripherals ==\n"
        if not len(self.availablePeripherals):
            ans += "None\n"
        for p in self.availablePeripherals:
            ans += "%2d : %s\n" % (count, p.name)
            ans += "     RSSI         : %d\n" % p.rssi
            ans += "     TxPowerLevel : %d\n" % p.advTxPowerLevel
            ans += "     Service UUIDs: %s\n" % pformat(p.advServiceUUIDs)
            count += 1
        ans += "\n"
        count = 0
        ans += "== Connected Peripherals ==\n"
        if not len(self.connectedPeripherals):
            ans += "None\n"
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
        if pid is None and len(self.connectedPeripherals):
            p = self.connectedPeripherals[0]
            OSXPeripheralApp(p).cmdloop()
        if pid is not None and pid < len(self.connectedPeripherals):
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
        if pid is None and len(self.availablePeripherals):
            self.centralManager.connectPeripheral(self.availablePeripherals[0])
        if pid is not None and pid < len(self.availablePeripherals):
            self.centralManager.connectPeripheral(self.availablePeripherals[pid])

    def do_disconnect(self, args):
        """Disconnect a connected peripheral
        """
        pid = None
        try:
            pid = int(args.strip())
        except:
            pass
        if pid is None and len(self.connectedPeripherals):
            self.centralManager.disconnectPeripheral(self.connectedPeripherals[0])
        if pid is not None and pid < len(self.connectedPeripherals):
            self.centralManager.disconnectPeripheral(self.connectedPeripherals[pid])

    def do_connectAll(self, args):
        """Connect all available peripherals
        """
        if len(self.availablePeripherals):
            for p in self.availablePeripherals:
                self.centralManager.connectPeripheral(p)

    def do_disconnectAll(self, args):
        """Disconnect all connected peripherals
        """
        if len(self.connectedPeripherals):
            for p in self.connectedPeripherals:
                self.centralManager.disconnectPeripheral(p)

    def do_test(self, args):
        #        self.centralManager.retrieveConnectedPeripherals()
        #        self.centralManager.retrieveConnectedPeripheralsWithServices(["FFF0"])
        pass

    def halt(self):
        self.stop.set()

if __name__ == "__main__":
    app = OSXCentralManagerApp(shell=True)
    try:
        app.cmdloop()
    except Exception as e:
        import traceback
        print traceback.print_exc()
        print e
