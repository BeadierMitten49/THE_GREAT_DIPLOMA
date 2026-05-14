from typing import Annotated

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import DeclarativeBase, mapped_column

intpk = Annotated[int, mapped_column(Integer, primary_key=True, autoincrement=True)]
str_nn = Annotated[str, mapped_column(String, nullable=False)]
bool_active = Annotated[bool, mapped_column(Boolean, nullable=False, default=True)]


class Base(DeclarativeBase):
    pass
