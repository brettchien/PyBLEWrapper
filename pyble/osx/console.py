from objc import *
from Foundation import *

import cmd
import os
import logging

import time
from pprint import pformat

try:
    from queue import Queue, Empty
except:
    from Queue import Queue, Empty


class OSXCmd(cmd.Cmd, object):
    def __init__(self, history_size=10):
        cmd.Cmd.__init__(self)
        self.logger = logging.getLogger("%s.%s" % (__name__, self.__class__.__name__))
        self.cmdqueue = Queue() 
        self.history_size = history_size

    def registerKeyboardInterrupt(self):
        stdin = NSFileHandle.fileHandleWithStandardInput().retain()

        handle = objc.selector(self.keyboardHandler_, signature='v@:@')
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, handle, NSFileHandleReadCompletionNotification, stdin)

        stdin.readInBackgroundAndNotify()

    def unregisterKeyboardInterrupt(self):
        NSNotificationCenter.defaultCenter().removeObserver_(self)

    def keyboardHandler_(self, notification):
        data = notification.userInfo().objectForKey_(NSFileHandleNotificationDataItem)
        line = NSString.alloc().initWithData_encoding_(data, NSUTF8StringEncoding).autorelease()

        if len(line):
            self.cmdqueue.put(line)
        
        stdin = NSFileHandle.fileHandleWithStandardInput().retain()
        stdin.readInBackgroundAndNotify()

    def cmdloop(self, intro=None):
        # customized for python & OSX co-existence
        # use OSX framework to read input from keyboard interrupt
        self.preloop()
        if intro is not None:
            self.intro = intro
        if self.intro:
            self.stdout.write(str(self.intro) + "\n")
        # the main loop
        stop = None
        showPrompt = True
        while not stop:
            if showPrompt:
                self.stdout.write(self.prompt)
                self.stdout.flush()
                showPrompt = False
            NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantFuture())
            try:
                line = self.cmdqueue.get_nowait()
                if not len(line):
                    line = "EOF"
                else:
                    line = line.strip('\r\n')
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
                self.cmdqueue.task_done()
                showPrompt = True
            except Empty:
                continue
            except Exception as e:
                print e
                break
        # cleanup
        self.postloop()
    
    def preloop(self):
        # cmd history
        self._history = []
        # OSX
        self.osx_pool = NSAutoreleasePool.alloc().init()
        self.registerKeyboardInterrupt()
    
    def postloop(self):
        self.unregisterKeyboardInterrupt()
        del self.osx_pool

    def endloop(self):
        self.cmdqueue.put("exit")


    def precmd(self, line):
        self._history += [ line.strip() ]
        if len(self._history) > self.history_size:
            self._history = self._history[-(self.history_size):]
        self.unregisterKeyboardInterrupt() 
        return line

    def postcmd(self, stop, line):
        self.stdout.flush()
        self.registerKeyboardInterrupt() 
        return stop

    def emptyline(self):
        pass

    def do_shell(self, args):
        """Execute shell command
        """
        os.system(args)

    def default(self, line):
        if len(line.strip()):
            self.do_eval(line)

    def do_eval(self, args):
        """Evaluate python statement
        """
        line = args.strip()
        if len(line) == 0:
            return
        output = ""
        try:
            output = eval(line)
        except Exception as e:
            self.stdout.write(pformat(e) + "\n")
        if output and len(pformat(output)):
            self.stdout.write(pformat(output) + "\n")
        self.stdout.flush()

    def do_hist(self, args):
        """Show last N command history
        """
        length = len(self._history)
        try:
            length = int(args.strip())
        except:
            pass
        self._history.pop()
        for cmd in self._history[-length:]:
            self.stdout.write(cmd)
            self.stdout.write('\n')
        self.stdout.flush()

    def do_exit(self, args):
        """Exit
        """
        return True

     
if __name__ == "__main__":
    app = OSXCmd()
    app.cmdloop()
