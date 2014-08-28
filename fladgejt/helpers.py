
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

def find_row(objects, **conditions):
    '''Searches the list of objects for one that matches all given conditions.

    ``obj['foo'] == bar`` must be true for all ``foo=bar`` keyword arguments
    for ``obj`` to match. The index of the first matching object is returned.
    This is useful for table rows and similar mapping-like objects.

    :param objects: List of objects.
    :param \*\*conditions: The conditions that the object must match.
    Returns:
        The index of the first object that had all the given keys and values.
    Raises:
        KeyError: Raised if no such object is found.
    '''
    for index, obj in enumerate(objects):
        if all(obj[key] == value for key, value in conditions.items()):
            return index
    raise KeyError("Object not found: {!r}".format(conditions))

def find_option(objects, **conditions):
    '''Searches the list of objects for one that matches all given conditions.

    ``obj.foo == bar`` must be true for all ``foo=bar`` keyword arguments for
    ``obj`` to match. The index of the first matching object is returned. This
    is useful for combo box options and similar objects.

    :param objects: List of objects.
    :param \*\*conditions: The conditions that the object must match.
    Returns:
        The index of the first object that had all the given keys and values.
    Raises:
        KeyError: Raised if no such object is found.
    '''
    for index, obj in enumerate(objects):
        if all(getattr(obj, key) == value for key, value in conditions.items()):
            return index
    raise KeyError("Object not found: {!r}".format(conditions))
