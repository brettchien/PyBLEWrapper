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

from pyble.patterns import LoggerObject

class OSXCmd(cmd.Cmd, LoggerObject):
    def __init__(self, history_size=10):
        # both cmd.Cmd, LoggerObject need to be init.
        cmd.Cmd.__init__(self)
        LoggerObject.__init__(self)

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
            try:
                NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.distantPast())
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
            except KeyboardInterrupt:
                break
            except Exception as e:
                import traceback
                print traceback.format_exc()
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
        try:
            self.stdout.flush()
        except:
            pass
        self.registerKeyboardInterrupt() 
        return stop

    def emptyline(self):
        pass

    def do_shell(self, args):
        """Execute shell command
        """
        os.system(args)

    def do_debug(self, args):
        """Enable/disable debugging information
        """
        if not hasattr(self, 'debug'):
            return
        option = args.strip()
        if option == "":
            pass
        elif option == "True":
            self.debug = True
        elif option == "False":
            self.debug = False
        else:
            self.stdout.write("Only accept True/False\n")
        ans = "%s is %sin debug mode.\n"
        cls_name = self.__class__.__name__
        if self.debug:
            ans = ans % (cls_name, "")
        else:
            ans = ans % (cls_name, "not ")
        self.stdout.write(ans)
        self.stdout.flush()

    def default(self, line):
        if len(line.strip()):
            self.do_eval(line)

    def do_eval(self, args):
        """Evaluate a single line python statement
        """
        line = args.strip()
        if len(line) == 0:
            return
        output = ""
        oldstdout = self.stdout
        from StringIO import StringIO
        import ast
        buffer = StringIO()
        self.stdout = buffer
        try:
            code = compile(line, "<string>", "single")
            exec(code)
        except NameError as e:
            self.logger.debug(e)
            cmd, args, line = self.parseline(line)
            self.commandNotFound(cmd)
        except SyntaxError as e:
            self.logger.debug(e)
            cmd, args, line = self.parseline(line)
            self.commandNotFound(cmd)
        except Exception as e:
            self.logger.debug(e)
            self.stdout.write(pformat(e) + "\n")
        finally:
            self.stdout = oldstdout
            self.stdout.write(buffer.getvalue())


    def commandNotFound(self, cmd):
        self.stdout.write("Command: '%s' is not yet support by %s\n" % (cmd, self.__class__.__name__))

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
