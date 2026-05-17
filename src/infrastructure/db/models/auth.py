from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models import Base, bool_active, intpk, str_nn


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    full_name: Mapped[str_nn]
    is_active: Mapped[bool_active]
    telegram_username: Mapped[str | None] = mapped_column(String, nullable=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    credential: Mapped["UserCredentialModel"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    roles: Mapped[list["UserRoleModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserCredentialModel(Base):
    __tablename__ = "user_credentials"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    hashed_password: Mapped[str_nn]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["UserModel"] = relationship(back_populates="credential")


class UserRoleModel(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)

    user: Mapped["UserModel"] = relationship(back_populates="roles")


class AuthLogModel(Base):
    __tablename__ = "auth_log"

    id: Mapped[intpk]
    username_attempt: Mapped[str_nn]
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
