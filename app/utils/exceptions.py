class MyJDBaseException(Exception):
    """Base exception for MyJDownloader operations."""
    pass


class MyJDConnectionError(MyJDBaseException):
    """Exception raised when connection to MyJDownloader fails."""
    pass


class MyJDOperationError(MyJDBaseException):
    """Exception raised when a MyJDownloader operation fails."""
    pass


class ConfigurationError(MyJDBaseException):
    """Exception raised when configuration is invalid."""
    pass


class ValidationError(MyJDBaseException):
    """Exception raised when input validation fails."""
    pass
