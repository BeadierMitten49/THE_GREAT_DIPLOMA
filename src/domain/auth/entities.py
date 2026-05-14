from dataclasses import dataclass, field

from src.domain.auth.value_objects import Role
from src.domain.shared.exceptions import InvalidFieldError


@dataclass
class User:
    username: str
    full_name: str
    roles: list[Role] = field(default_factory=list)
    is_active: bool = True
    telegram_username: str | None = None
    telegram_id: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.username or not self.username.strip():
            raise InvalidFieldError("username", "must not be empty")
        if not self.full_name or not self.full_name.strip():
            raise InvalidFieldError("full_name", "must not be empty")

    def has_role(self, role: Role) -> bool:
        return role in self.roles

    def add_role(self, role: Role) -> None:
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: Role) -> None:
        if role in self.roles:
            self.roles.remove(role)

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def set_telegram_username(self, username: str) -> None:
        if not username or not username.strip():
            raise InvalidFieldError("telegram_username", "must not be empty")
        self.telegram_username = username

    def set_telegram_id(self, telegram_id: int) -> None:
        if telegram_id <= 0:
            raise InvalidFieldError("telegram_id", "must be positive")
        self.telegram_id = telegram_id
