class Error(Exception):
    """Base class for other exceptions"""
    pass


class UserNotFoundError(Error):
    """Raised when User was not found"""
    pass


class LocationNotFoundError(Error):
    """Raised when Location was not found"""
    pass


class WodResultNotFoundError(Error):
    """Raised when WOD result was not found"""
    pass


class WodNotFoundError(Error):
    """Raised when WOD was not found"""
    pass


class ValueIsEmptyError(Error):
    """Raised when value is empty"""
    pass
