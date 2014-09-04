# singleton decorator
class singleton:
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance == None:
            self.instance = self.klass(*args, **kwargs)
        return self.instance

#deparecated
class deprecated(object):
    def __call__(self, func):
        self.func = func
        self.count = 0
        return self._wrapper

    def _wrapper(self, *args, **kwargs):
        self.count += 1
        if self.count == 1:
            print self.func.__name__, "is deprecated"
        return func(*args, **kwargs)

# debuggable and trace
import logging
import signal
import sys
from datetime import datetime

import linecache
from pprint import pprint
from functools import wraps
import inspect

@singleton
class TraceObject(object):
    def __init__(self):
        self._running = False
        self.TRACE_INTO = []
        self.TRACE_FILES = []
        self._trace = []

    def addFile(self, fname):
        if fname not in self.TRACE_FILES:
            self.TRACE_FILES.append(fname)

    def removeFile(self, fname):
        if fname in self.TRACE_FILES:
            self.TRACE_FILES.remove(fname)

    def add(self, func_name):
        if func_name not in self.TRACE_INTO:
            self.TRACE_INTO.append(func_name)

    def remove(self, func_name):
        if func_name in self.TRACE_INTO:
            self.TRACE_INTO.remove(func_name)

    def append(self, trace):
        if not self._running:
            self._running = True
        self._trace.append(trace)

    @staticmethod
    def trace_lines(frame, event, arg):
        trace = TraceObject()
        co = frame.f_code
        lineno = frame.f_lineno
        filename = co.co_filename
        func_name = co.co_name
        line = linecache.getline(filename, lineno)
        class_name = frame.f_locals['self'].__class__.__name__
        print "TraceIt %s:%s:%3d: %s" % (class_name, func_name, lineno, line.rstrip())

    @staticmethod
    def trace_calls(frame, event, arg):
        trace = TraceObject()
        co = frame.f_code
        lineno = frame.f_lineno
        filename = co.co_filename
        func_name = co.co_name
        line = linecache.getline(filename, lineno)
#        class_name = frame.f_locals['self'].__class__.__name__
        print "TraceIt :%s:%3d: %s" % (func_name, lineno, line.rstrip())

    @staticmethod
    def trace_exceptions(frame, event, arg):
        co = frame.f_code
        lineno = frame.f_lineno
        filename = co.co_filename
        func_name = co.co_name
        line = linecache.getline(filename, lineno)
        class_name = frame.f_locals['self'].__class__.__name__
        if arg:
            exc_type, exc_value, exc_traceback = arg
#        print arg
        print "TraceIt(Exception) %s:%s:%3d: %s" % (class_name, func_name, lineno, line.rstrip())
#        print "TraceIt(Exception) %s:%s" % (exc_type.__name__, exc_value)

    @staticmethod
    def traceIt(frame, event, arg):
        trace = TraceObject()
        filename = frame.f_code.co_filename
        if filename not in trace.TRACE_FILES:
            return
        try:
            events = ['call', 'line', 'return', 'exception', 'c_call', 'c_return', 'c_exception']
            co = frame.f_code
            lineno = frame.f_lineno
#            print filename, lineno, co.co_name, linecache.getline(filename, lineno)
            if event == "line":
                trace.trace_lines(frame, event, arg)
            if event == "call":
                trace.trace_calls(frame, event, arg)
#                if event == "exception":
#                    trace.trace_exceptions(frame, event, arg)
        except Exception as e:
            print filename
            print co.co_name
            print lineno
            import traceback
            print traceback.format_exc()
            print e
            return
        return trace.traceIt


#trace decorator
import types
def _trace():
    def decorator(func):
        if hasattr(func, '_trace_decorator') and func._trace_decorator:
            return func

        @wraps(func)
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)
            return ret

        wrapper._trace_decorator = True
        return wrapper
    return decorator

def Trace(*args, **kwargs):
    def cls_decorator(*cargs, **ckwargs):
        cls = cargs[0]
        for o in cls.__dict__:
            if o.startswith('__') and o not in ['__init__']:
                continue
            a = getattr(cls, o)
            if hasattr(a, '__call__') and type(cls.__dict__[o]) == types.FunctionType:
                # do not decorate static and class methonds
                func_name = "%s.%s" % (cls.__name__, o)
                TraceObject().addFile(inspect.getfile(cls))
                print cls.__name__
                TraceObject().add(cls.__name__)
                TraceObject().add(func_name)
#                da = _trace()(a)
#                setattr(cls, o, da)
        return cls
    return cls_decorator(*args, **kwargs)


class LoggerObject(object):
    def __init__(self, traceit=True):
        # signal
        signal.signal(signal.SIGTERM, self.__class__.signal_handler)
        # tracing
        if traceit:
            print self.__class__.__name__
            sys.settrace(TraceObject().traceIt)
        else:
            sys.settrace(None)
        # logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("%s.%s" % (self.__class__.__module__, self.__class__.__name__))
        self.logger.setLevel(logging.INFO)
        self._debug = False
        self.trace = TraceObject()
#        print self.trace.TRACE_INTO
#        print self.trace.TRACE_FILES

    def enableTrace(self):
        sys.settrace(TraceObject().traceIt)

    def disableTrace(self):
        sys.settrace(None)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        if value:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self._debug = value

    @classmethod
    def signal_handler(klass, signum, frame):
        sys.stdout.flush()
        sys.exit(0)

