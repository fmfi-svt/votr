from aisikl.typeutils import ct
from base64 import urlsafe_b64encode, urlsafe_b64decode
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from aisikl.components.combobox import Option
    from aisikl.components.table import Row
    from collections.abc import Callable


class CantOpenApplication(Exception):
    '''AIS didn't open the application we wanted.

    Thrown from ``_open_...`` methods if AIS refuses to open the application
    (e.g. the menu item is disabled for this user). The caller should catch
    this and show a message to the user. This is only used when we know it can
    happen -- unknown AIS behavior will cause an AISBehaviorError.
    '''


def find_row(objects: list[Row], **conditions: str | bool) -> int:
    r'''Searches the list of objects for one that matches all given conditions.

    ``obj.cell('foo').value == bar`` must be true for all ``foo=bar`` keyword arguments
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
        if all(obj.cell(key).value == value
                for key, value in conditions.items()):
            return index
    raise KeyError("Object not found: {!r}".format(conditions))


def find_row_insensitive(objects: list[Row], **conditions: str) -> int:
    '''Same as :func:`find_row` but case insensitive.'''
    for index, obj in enumerate(objects):
        if all(ct(str, obj.cell(key).value).lower() == value.lower()
               for key, value in conditions.items()):
            return index
    raise KeyError("Object not found: {!r}".format(conditions))


def find_option(objects: list[Option], **conditions: object) -> int:
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


def with_key_fields[T](**key_fields: list[str]) -> Callable[[T], T]:
    '''Adds special "key fields" to a TypedDict.

    "Key fields" are additional fields automatically added to the dict. Their
    value is automatically computed using :func:`encode_key` from other fields,
    combining their values into an encoded string. The key field acts as a
    shorthand for the original fields in situations where a single string is
    easier to work with than multiple values -- notably, to persistently
    identify a row, and roundtrip this identifier between client and server. It
    can be decoded back when needed::

        @with_key_fields(k=['a', 'c'])
        class MyDict(TypedDict):
            a: str
            b: str
            c: str

        my_dict = MyDict(a='Aaaa', b='Bbbb', c='Cccc')
        assert my_dict['k'] == encode_key(('Aaaa', 'Cccc'))
        assert decode_key(my_dict['k']) == ('Aaaa', 'Cccc')

    Limitations:

    - Static type checkers don't know about key fields. Accessing them on a dict
      instance is a static type error.
    - Similarly to normal TypedDict classes and unlike e.g. NamedTuple, argument
      names are not runtime checked. So be very careful if constructing it from
      untyped code.
    - The decorated result is actually implemented as a plain function, not a
      class. You can't use it in any way except calling (constructing) it. It's
      even more fake than normal TypedDict classes, whose instances at runtime
      are plain dicts, but they can at least inherit from each other as classes.
    '''
    def decorator(original_class: T) -> T:
        def dict_maker(**kwargs: str) -> dict[str, str]:
            for output_name, input_names in key_fields.items():
                input_values = tuple(kwargs[name] for name in input_names)
                kwargs[output_name] = encode_key(input_values)

            return kwargs

        return cast(T, dict_maker)

    return decorator


def encode_key(tuple: tuple[str, ...]) -> str:
    '''Reversibly encode a tuple of strings into a single string.

    See :func:`with_key_fields` for the rationale.

    Empty tuples may be decoded incorrectly. Do not use them.

    The current encoding additionally always outputs URL-safe strings. But its
    reversibility is the more important property.

    Args:
        tuple: A tuple of strings that is to be encoded.
    Returns:
        A string ``s`` such that ``decode_key(s)`` produces the original tuple.
    '''
    result: list[str] = []
    for part in tuple:
        part = part.encode('utf8')
        part = urlsafe_b64encode(part)
        part = part.rstrip(b'=')
        part = part.decode('ascii')
        result.append(part)
    return '.'.join(result)


def decode_key(string: str) -> tuple[str, ...]:
    '''Decode the output of :func:`encode_key` back into a tuple of strings.

    See :func:`with_key_fields` for the rationale.

    Args:
        string: A string created with :func:`encode_key`.
    Returns:
        The tuple of strings that was originally given to :func:`encode_key`.
    '''
    result: list[str] = []
    for part in string.split('.'):
        part = part.encode('ascii')
        part += b'=' * (-len(part) % 4)
        part = urlsafe_b64decode(part)
        part = part.decode('utf8')
        result.append(part)
    return tuple(result)
