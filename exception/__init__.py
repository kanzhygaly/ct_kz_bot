class Error(Exception):
    """Base class for other exceptions"""
    pass


class UserNotFoundError(Error):
    """Raised when the input value is too small"""
    pass


class LocationNotFoundError(Error):
    """Raised when the input value is too small"""
    pass
