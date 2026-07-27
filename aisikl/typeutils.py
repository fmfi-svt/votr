from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable


def ct[T](cls: type[T], value: object) -> T:
    '''Raises if ``value`` is not ``cls`` at runtime. "ct" stands for "check
    type".
    '''
    if isinstance(value, cls):
        return value
    raise TypeError(f'expected {cls.__name__} instead of {type(value).__name__}: {value!r}')


def ct_none[T](cls: type[T], value: object) -> T | None:
    '''Raises if ``value`` is not ``cls`` or None at runtime. "ct" stands for
    "check type".
    '''
    if value is None or isinstance(value, cls):
        return value
    raise TypeError(f'expected {cls.__name__} or None instead of {type(value).__name__}: {value!r}')


def nn[T](value: T | None) -> T:
    '''Raises if value is None. "nn" stands for "not None".'''
    if value is None:
        raise TypeError('value is None')
    return value


#: Converts ``value`` to int. Raises at runtime if ``value`` is not
#: something that can be converted (string-like or number-like).
really_int = cast('Callable[[object], int]', int)
