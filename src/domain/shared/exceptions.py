class DomainError(Exception):
    pass


class InvalidFieldError(DomainError):
    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")
