# singleton
class SingletonDecorator:
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
