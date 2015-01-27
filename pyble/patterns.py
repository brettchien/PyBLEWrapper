# singleton decorator
class singleton:
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.klass(*args, **kwargs)
        return self.instance


# deparecated
class deprecated(object):
    def __call__(self, func):
        self.func = func
        self.count = 0
        return self._wrapper

    def _wrapper(self, func, *args, **kwargs):
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
        self.TRACE_CLASS = []
        self._trace = []

    def addClass(self, cls):
        if cls not in self.TRACE_CLASS:
            self.TRACE_CLASS.append(cls)

    def removeClass(self, cls):
        if cls in self.TRACE_CLASS:
            self.TRACE_CLASS.remove(cls)

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
    def traceInstance(instance):
        trace = TraceObject()
        cls = instance.__class__
        cls_name = cls.__name__
        filename = inspect.getfile(cls)
        if filename.endswith(".pyc") or filename.endswith(".pyo"):
            filename = filename[:-1]
        trace.addFile(filename)
        trace.addClass(cls_name)
        for o in cls.__dict__:
            if o.startswith('__') and o not in ['__init__']:
                continue
            a = getattr(cls, o)
            if hasattr(a, '__call__') and type(cls.__dict__[o]).__name__ == "python_selector":
                if ":" not in a.__name__:
                    func_name = "%s.%s" % (cls_name, o)
                    trace.add(func_name)

    @staticmethod
    def trace_lines(frame, event, arg):
        trace = TraceObject()
        co = frame.f_code
        lineno = frame.f_lineno
        filename = co.co_filename
        func_name = co.co_name
        line = linecache.getline(filename, lineno)
        cls = frame.f_locals.get('self', None)
        class_name = frame.f_globals['__name__']
        if cls:
            class_name = frame.f_locals['self'].__class__.__name__
        print "TraceIt(Line) %s:%s:%3d: %s" % (class_name, func_name, lineno, line.rstrip())

    @staticmethod
    def trace_calls(frame, event, arg):
        trace = TraceObject()
        co = frame.f_code
        lineno = frame.f_lineno
        filename = co.co_filename
        func_name = co.co_name
        line = linecache.getline(filename, lineno)
        cls = frame.f_locals.get('self', None)
        class_name = frame.f_globals['__name__']
        if cls:
            class_name = frame.f_locals['self'].__class__.__name__
        print "TraceIt(Call) %s:%s:%3d: %s" % (class_name, func_name, lineno, line.rstrip())

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
        try:
            trace = TraceObject()
            co = frame.f_code
            filename = co.co_filename
            func_name = co.co_name
            lineno = frame.f_lineno
            prev_frame = frame.f_back
            module = frame.f_globals['__name__']
            klass = frame.f_locals.get('__self__', None)
            if filename not in trace.TRACE_FILES:
                return
            events = ['call', 'line', 'return', 'exception', 'c_call', 'c_return', 'c_exception']
#            print lineno, filename, module, func_name, klass

            if event == "line":
                trace.trace_lines(frame, event, arg)
            if event == "call":
                trace.trace_calls(frame, event, arg)
#                if event == "exception":
#                    trace.trace_exceptions(frame, event, arg)
#            if event == "return":

        except Exception as e:
            import traceback
            print traceback.format_exc()
            print e
            return
        try:
            sys.stdout.flush()
        except:
            pass
        return trace.traceIt


# trace decorator
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
                TraceObject().addClass(cls.__name__)
                TraceObject().add(func_name)
#                da = _trace()(a)
#                setattr(cls, o, da)
        return cls
    return cls_decorator(*args, **kwargs)


class LoggerObject(object):
    def __init__(self, traceit=False):
        # signal
        signal.signal(signal.SIGTERM, self.__class__.signal_handler)
        # tracing
        if traceit:
            print self.__class__.__name__, "in trace"
            sys.settrace(TraceObject().traceIt)
        else:
            sys.settrace(None)
        # logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("%s.%s" % (self.__class__.__module__, self.__class__.__name__))
        self.logger.setLevel(logging.INFO)
        self._debug = False
        self.trace = TraceObject()

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
