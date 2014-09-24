
from collections import namedtuple
from base64 import urlsafe_b64encode, urlsafe_b64decode
from datetime import datetime


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


def get_aktualny_akademicky_rok():
    rok = datetime.today().year
    mesiac = datetime.today().month

    if mesiac < 8:
        rok = rok - 1

    return '{}/{}'.format(rok, rok+1)
