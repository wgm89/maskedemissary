
def log(func):
    def wrapper(*args, **kw):
        print 'call %s():' % func.__name__
        return func(*args, **kw)
        print '%s(): excute complete.' % func.__name__
    return wrapper

