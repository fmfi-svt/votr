
from functools import wraps

def memoized(original_method):
    '''Decorator to memoize the results of methods.

    The ``original_method`` must accept only self and positional arguments.
    Their values will be used to memoize already computed results. If you call
    the decorated method on the same object with the same arguments, it will
    return the previous result without calling the original method again.

    Args:
        original_method: The method to decorate.
    Returns:
        The decorated method.
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

def find_row(rows, **attributes):
    '''Searches the list of objects for one that has all the given attributes.

    :param rows: List of objects.
    :param \*\*attributes: The attribute values the result must have.
    Returns:
        The index of the first object that had all the given attribute values.
    Raises:
        KeyError: Raised if no such object is found.
    '''
    for index, row in enumerate(rows):
        if all(getattr(row, key) == value for key, value in attributes.items()):
            return index
    raise KeyError("Row not found: {!r}".format(conditions))
