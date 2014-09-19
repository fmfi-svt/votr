
class AisiklError(Exception):
    '''The base class for AIS, REST-related exceptions.'''


class AISParseError(AisiklError):
    '''We couldn't parse or properly process the response from AIS.

    This isn't just for syntax errors, but also for unknown or unsupported
    attribute values, method names and such. The error can either mean:

    - AIS does something we doesn't support yet, or
    - AIS changes their formats and our parser needs to be updated, or
    - the AIS server returned an error with status 200 (should never happen).
    '''


class AISBehaviorError(AisiklError):
    '''AIS did something we didn't expect.'''


class RESTServerError(AisiklError):
    '''Server returned error after our request.'''


class LoggedOutError(AisiklError):
    '''Request couldn't be completed because we are no longer logged in.'''
