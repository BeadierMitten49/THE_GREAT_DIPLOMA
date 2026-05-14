class AuthenticationError(Exception):
    def __init__(self, reason: str = "invalid credentials") -> None:
        self.reason = reason
        super().__init__(reason)


class RateLimitError(Exception):
    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"too many failed login attempts for '{username}'")


class InvalidTokenError(Exception):
    def __init__(self, reason: str = "invalid or expired token") -> None:
        self.reason = reason
        super().__init__(reason)
