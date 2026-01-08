class BaseAPIException(Exception):
    """Exception base for all application exceptions."""

    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    @property
    def message(self) -> str:
        return self._message

    @property
    def status_code(self) -> int:
        return self._status_code


class NotFoundError(BaseAPIException):
    """Exception when a resource is not found."""
    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, 404)


class ValidationError(BaseAPIException):
    """Exception when the input is not valid."""
    def __init__(self, message: str = "Invalid input."):
        super().__init__(message, 400)


class InternalServerError(BaseAPIException):
    """Exception para quando ocorre um erro interno."""
    def __init__(self, message: str = "Erro interno do servidor."):
        super().__init__(message, 500)