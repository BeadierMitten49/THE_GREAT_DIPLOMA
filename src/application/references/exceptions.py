class NotFoundError(Exception):
    def __init__(self, entity: str, id: int) -> None:
        self.entity = entity
        self.id = id
        super().__init__(f"{entity} with id={id} not found")


class AlreadyExistsError(Exception):
    def __init__(self, entity: str, name: str) -> None:
        self.entity = entity
        self.name = name
        super().__init__(f"{entity} with name='{name}' already exists")
