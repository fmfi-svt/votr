
from collections import namedtuple
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


_keyed_namedtuple_template = '''
def __new__(_cls, {args}=None):
    if key is None: key = ({key_args},)
    return tuple.__new__(_cls, ({args},))
result_class.__new__ = __new__
'''

def keyed_namedtuple(typename, field_names, key_field_names):
    '''A variant of namedtuple with a default value for the ``key`` field.

    The last field of the tuple must be named ``key``. This argument will be
    optional. When not given, it will default to a normal tuple containing the
    values of the tuple's `key fields` (specified in ``key_field_names``). So
    when a namedtuple has the same key as another namedtuple you've seen before,
    that means their key fields also have equal values (unless someone changed
    the key manually).

    Except for the above behavior, ``key`` is a normal field, and will be
    included in JSON dumps, pickles, etc.

    Args:
        typename: The class name, like in namedtuple.
        field_names: The list of fields, like in namedtuple. The last name must
            be ``"key"``.
        key_field_names: The list of key fields, which will be used to compute
            the default value of ``key``.
    Returns:
        A new class, like returned by namedtuple.
    '''
    if field_names[-1] != 'key': raise ValueError(typename)
    if set(key_field_names) - set(field_names): raise ValueError(typename)

    result_class = namedtuple(typename, field_names)

    exec(_keyed_namedtuple_template.format(
        args=', '.join(field_names),
        key_args=', '.join(key_field_names)))

    return result_class
