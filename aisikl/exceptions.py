
class AISError(Exception):
    '''The base class for AIS-related exceptions.'''


class AISParseError(AISError):
    '''We couldn't parse or properly process the response from AIS.

    This isn't just for syntax errors, but also for unknown or unsupported
    attribute values, method names and such. The error can either mean:

    - AIS does something we doesn't support yet, or
    - AIS changes their formats and our parser needs to be updated, or
    - the AIS server returned an error with status 200 (should never happen).
    '''


class AISBehaviorError(AISError):
    '''AIS did something we didn't expect.'''
