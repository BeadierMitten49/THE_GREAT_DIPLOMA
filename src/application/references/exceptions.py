from src.application.shared.exceptions import NotFoundError

__all__ = ["NotFoundError"]


class AlreadyExistsError(Exception):
    def __init__(self, entity: str, name: str) -> None:
        self.entity = entity
        self.name = name
        super().__init__(f"{entity} with name='{name}' already exists")
