
class AisiklError(Exception):
    '''The base class for AIS, REST-related exceptions.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        for key, value in kwargs.items():
            setattr(self, key, value)


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


class AISApplicationClosedError(AisiklError):
    '''The application we were using has already closed.'''


class RESTServerError(AisiklError):
    '''Server returned error after our request.'''


class LoggedOutError(AisiklError):
    '''Request couldn't be completed because we are no longer logged in.'''


class NotFoundError(AisiklError):
    '''The searched item (e.g. table row, combo box option) was not found.'''


class AmbiguousItemError(AisiklError):
    '''There were multiple matching items (e.g. table rows, combo box options),
    but we expected only one, so we don't know what's the right one to pick.'''
