
from collections import namedtuple
from base64 import urlsafe_b64encode, urlsafe_b64decode


class CantOpenApplication(Exception):
    '''AIS didn't open the application we wanted.

    Thrown from ``_open_...`` methods if AIS refuses to open the application
    (e.g. the menu item is disabled for this user). The caller should catch
    this and show a message to the user. This is only used when we know it can
    happen -- unknown AIS behavior will cause an AISBehaviorError.
    '''


def find_row(objects, **conditions):
    r'''Searches the list of objects for one that matches all given conditions.

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


def find_row_insensitive(objects, **conditions):
    '''Same as :func:`find_row` but case insensitive.'''
    for index, obj in enumerate(objects):
        if all(obj[key].lower() == value.lower()
               for key, value in conditions.items()):
            return index
    raise KeyError("Object not found: {!r}".format(conditions))


def find_option(objects, **conditions):
    r'''Searches the list of objects for one that matches all given conditions.

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
def __new__(_cls, {args_none}):
    {keys}
    return tuple.__new__(_cls, ({args},))
result_class.__new__ = __new__
'''

_keyed_namedtuple_key_template = '''
    if {key_name} is None: {key_name} = encode_key(({key_args},))
'''


def keyed_namedtuple(typename, field_names, **key_fields):
    '''A variant of namedtuple where some "key fields" have default values.

    The value of each "key field" is computed from some other fields by
    combining their values into an encoded string. The key field acts as a
    shorthand for the original fields in situations where a single string is
    easier to work with than multiple values. It can be decoded back when
    needed::

        T = keyed_namedtuple('T', ['a', 'b', 'c', 'k'], k=['a', 'c'])
        t = T(a="foo", b="bar", c="baz")
        assert t.k == encode_key((t.a, t.c))
        assert decode_key(t.k) == (t.a, t.c)

    Args:
        typename: The class name, like in namedtuple.
        field_names: The list of fields, like in namedtuple. Key fields have
            to be at the end, after normal fields.
        key_fields: Keyword arguments of key names and their associated lists
            of field names, which will be used to compute its default value.
    Returns:
        A new class, like returned by namedtuple.
    '''
    # Key names have to be in field_names and key args have to exist
    for key_name, key_args in key_fields.items():
        if key_name not in field_names or set(key_args) - set(field_names):
            raise ValueError(typename)

    result_class = namedtuple(typename, field_names)

    # Add '=None' to the keys
    field_names_none = [name + ("=None" if name in key_fields else "")
                        for name in field_names]

    # Create code for computing the default values of key_fields
    key_defs = [_keyed_namedtuple_key_template.format(
                    key_name=key_name, key_args=', '.join(key_fields[key_name]))
                for key_name in field_names if key_name in key_fields]

    # Create custom __new__ method
    exec(_keyed_namedtuple_template.format(
        args_none=', '.join(field_names_none),
        args=', '.join(field_names),
        keys=''.join(key_defs)))

    return result_class


def encode_key(tuple):
    '''Reversibly encode a tuple of strings into a single string.

    See :func:`keyed_namedtuple` for the rationale.

    Empty tuples may be decoded incorrectly. But :func:`keyed_namedtuple`
    doesn't support empty keys anyway.

    The current encoding additionally always outputs URL-safe strings. But its
    reversibility is the more important property.

    Args:
        tuple: A tuple of strings that is to be encoded.
    Returns:
        A string ``s`` such that ``decode_key(s)`` produces the original tuple.
    '''
    result = []
    for part in tuple:
        part = part.encode('utf8')
        part = urlsafe_b64encode(part)
        part = part.rstrip(b'=')
        part = part.decode('ascii')
        result.append(part)
    return '.'.join(result)


def decode_key(string):
    '''Decode the output of :func:`encode_key` back into a tuple of strings.

    See :func:`keyed_namedtuple` for the rationale.

    Args:
        string: A string created with :func:`encode_key`.
    Returns:
        The tuple of strings that was originally given to :func:`encode_key`.
    '''
    result = []
    for part in string.split('.'):
        part = part.encode('ascii')
        part += b'=' * (-len(part) % 4)
        part = urlsafe_b64decode(part)
        part = part.decode('utf8')
        result.append(part)
    return tuple(result)
