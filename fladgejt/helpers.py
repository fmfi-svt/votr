
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
def __new__(_cls, {args_none}):
    {keys}
    return tuple.__new__(_cls, ({args},))
result_class.__new__ = __new__

def _encode(self):
    return self._replace({encode_kwargs})
result_class._encode = _encode
'''

_keyed_namedtuple_key_template = '''
    if {key_name} is None: {key_name} = ({key_args},)
'''


def keyed_namedtuple(typename, field_names, **key_fields):
    '''A variant of namedtuple where "key fields" can have default values.

    If the value of the "key field" is not specified, it will default to a
    normal tuple containing some of the other field values, as specified by the
    kwargs (the ``key_fields`` dict). The name of each keyword argument must be
    a tuple field and the value must be a list of other field names which are
    to be used as the default value.

    Key names have to be at the end of the ``field_names`` list.

    A key field can serve as an unique indetifier when a real ID is not
    available, e.g., from a database.

    The tuple is provided with an ``_encode()`` method which returns a new
    tuple with all key fields encoded into strings using :func:`encode_key`.

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

    # Create assignements of list of field names to their keys
    key_defs = [_keyed_namedtuple_key_template.format(
                    key_name=key_name, key_args=', '.join(key_args))
                for key_name, key_args in key_fields.items()]

    # Create custom __new__ method and _encode method
    exec(_keyed_namedtuple_template.format(
        args_none=', '.join(field_names_none),
        args=', '.join(field_names),
        keys=''.join(key_defs),
        encode_kwargs=', '.join(
            '{}=encode_key(self.{})'.format(key_name, key_name)
            for key_name in key_fields)))

    return result_class


def with_key_args(*spec):
    '''Specify which arguments of this fladgejt method are structure keys.

    Structure keys (see :func:`keyed_namedtuple`) are tuples of strings, but we
    want the client to see plain strings, to simplify client-side code and to
    enforce the keys' opaqueness. When a keyed namedtuple is sent to the client,
    we encode the key as a string, and when the client does an RPC call of some
    client method, we decode the strings back into tuples of strings. Thus, we
    need to know which arguments should be decoded and which shouldn't (they
    really are just strings). That can be specified using this decorator::

        @with_key_args(True, True, False)
        def some_method(self, some_key, another_key, normal_argument):
            ...

    :param \*spec: For each argument of the method except ``self``, specify
        ``True`` if it's a key and should be decoded, and ``False`` otherwise.
    '''
    def decorator(method):
        method.key_args = spec
        return method
    return decorator


def encode_key(tuple):
    '''Reversibly encode a tuple of strings into a single string.

    See :func:`with_key_args` for the rationale.

    Empty tuples may be decoded incorrectly. You shouldn't have structures with
    empty keys anyway.

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

    See :func:`with_key_args` for the rationale.

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
