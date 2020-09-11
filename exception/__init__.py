class Error(Exception):
    """Base class for other exceptions"""
    pass


class UserNotFoundError(Error):
    """Raised when user was not found"""
    pass


class LocationNotFoundError(Error):
    """Raised when location was not found"""
    pass


class WodResultNotFoundError(Error):
    """Raised when wod result was not found"""
    pass
