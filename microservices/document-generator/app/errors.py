class BaseAPIException(Exception):
    """Exception base for all application exceptions."""

    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(BaseAPIException):
    """Exception when a resource is not found."""

    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, 404)


class ValidationError(BaseAPIException):
    """Exception when the input is not valid."""

    def __init__(self, message: str = "Invalid input."):
        super().__init__(message, 400)


class UnauthorizedError(BaseAPIException):
    """Exception when the service JWT is missing, invalid, expired, or signed with an unknown kid."""

    def __init__(self, message: str = "Missing or invalid service credentials."):
        super().__init__(message, 401)


class InternalServerError(BaseAPIException):
    """Exception when an internal server error occurs."""

    def __init__(self, message: str = "Internal server error."):
        super().__init__(message, 500)
