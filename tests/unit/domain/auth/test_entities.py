import pytest

from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.domain.shared.exceptions import InvalidFieldError

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------


def test_role_is_str() -> None:
    assert Role.director == "director"
    assert isinstance(Role.production, str)


# ---------------------------------------------------------------------------
# User creation
# ---------------------------------------------------------------------------


def test_user_created_with_defaults(user: User) -> None:
    assert user.is_active is True
    assert user.roles == []
    assert user.telegram_username is None
    assert user.telegram_id is None
    assert user.id is None


@pytest.mark.parametrize("username", ["", "   "])
def test_user_empty_username_raises(username: str) -> None:
    with pytest.raises(InvalidFieldError):
        User(username=username, full_name="Иванов Иван")


@pytest.mark.parametrize("full_name", ["", "   "])
def test_user_empty_full_name_raises(full_name: str) -> None:
    with pytest.raises(InvalidFieldError):
        User(username="ivanov", full_name=full_name)


# ---------------------------------------------------------------------------
# activate / deactivate
# ---------------------------------------------------------------------------


def test_deactivate(user: User) -> None:
    user.deactivate()
    assert user.is_active is False


def test_activate(user: User) -> None:
    user.deactivate()
    user.activate()
    assert user.is_active is True


# ---------------------------------------------------------------------------
# roles
# ---------------------------------------------------------------------------


def test_has_role_false_by_default(user: User) -> None:
    assert user.has_role(Role.director) is False


def test_add_role(user: User) -> None:
    user.add_role(Role.director)
    assert user.has_role(Role.director) is True


def test_add_role_duplicate_ignored(user: User) -> None:
    user.add_role(Role.director)
    user.add_role(Role.director)
    assert user.roles.count(Role.director) == 1


def test_remove_role(user: User) -> None:
    user.add_role(Role.production)
    user.remove_role(Role.production)
    assert user.has_role(Role.production) is False


def test_remove_role_not_present_is_noop(user: User) -> None:
    user.remove_role(Role.warehouse)  # не должно бросать исключение


def test_user_can_have_multiple_roles(user: User) -> None:
    user.add_role(Role.director)
    user.add_role(Role.warehouse)
    assert user.has_role(Role.director) is True
    assert user.has_role(Role.warehouse) is True


def test_has_role_director(director: User) -> None:
    assert director.has_role(Role.director) is True
    assert director.has_role(Role.production) is False


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------


def test_set_telegram_username(user: User) -> None:
    user.set_telegram_username("ivan_tg")
    assert user.telegram_username == "ivan_tg"


@pytest.mark.parametrize("username", ["", "   "])
def test_set_telegram_username_empty_raises(user: User, username: str) -> None:
    with pytest.raises(InvalidFieldError):
        user.set_telegram_username(username)


def test_set_telegram_id(user: User) -> None:
    user.set_telegram_id(123456789)
    assert user.telegram_id == 123456789


@pytest.mark.parametrize("telegram_id", [0, -1, -100])
def test_set_telegram_id_non_positive_raises(user: User, telegram_id: int) -> None:
    with pytest.raises(InvalidFieldError):
        user.set_telegram_id(telegram_id)


def test_telegram_username_without_id(user: User) -> None:
    user.set_telegram_username("ivan_tg")
    assert user.telegram_username == "ivan_tg"
    assert user.telegram_id is None


def test_telegram_id_set_independently(user: User) -> None:
    user.set_telegram_username("ivan_tg")
    user.set_telegram_id(987654321)
    assert user.telegram_username == "ivan_tg"
    assert user.telegram_id == 987654321
