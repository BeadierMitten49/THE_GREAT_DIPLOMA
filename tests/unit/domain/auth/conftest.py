import pytest

from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role


@pytest.fixture
def user() -> User:
    return User(username="ivanov_ivan", full_name="Иванов Иван Иванович")


@pytest.fixture
def director() -> User:
    return User(
        username="director",
        full_name="Директор Директорович",
        roles=[Role.director],
    )
