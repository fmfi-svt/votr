
from functools import wraps

def memoized(original_method):
    '''
    TODO bla bla bla bla
    '''
    @wraps(original_method)
    def wrapper(self, *args):
        if not hasattr(self, '_memoized'):
            self._memoized = {}
        my_results = self._memoized.setdefault(original_method.__name__, {})
        if args not in my_results:
            my_results[args] = original_method(self, *args)
        return my_results[args]
    return wrapper
