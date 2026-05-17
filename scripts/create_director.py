"""Bootstrap script: create a director user."""
import asyncio
import sys

sys.path.insert(0, ".")

from src.application.auth.dto import CreateUserDTO, SetUserRolesDTO
from src.application.auth.use_cases import create_user, set_user_roles
from src.domain.auth.value_objects import Role
from src.infrastructure.db.repositories.auth import UserRepository, UserCredentialRepository
from src.infrastructure.db.session import AsyncSessionFactory
from src.infrastructure.security.password_hasher import BcryptPasswordHasher

FULL_NAME = "Директор"
PASSWORD = "director123"


async def main() -> None:
    hasher = BcryptPasswordHasher()
    async with AsyncSessionFactory() as session:
        user_repo = UserRepository(session)
        cred_repo = UserCredentialRepository(session)

        user_id = await create_user(
            CreateUserDTO(full_name=FULL_NAME, password=PASSWORD),
            user_repo,
            cred_repo,
            hasher,
        )
        await set_user_roles(
            user_id,
            SetUserRolesDTO(roles=[Role.director]),
            user_repo,
        )
        await session.commit()

        user = await user_repo.get_by_id(user_id)
        print(f"Created director user:")
        print(f"  Login:    {user.username}")
        print(f"  Password: {PASSWORD}")


asyncio.run(main())
