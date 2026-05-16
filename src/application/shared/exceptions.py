class NotFoundError(Exception):
    def __init__(self, entity: str, id: int) -> None:
        self.entity = entity
        self.id = id
        super().__init__(f"{entity} with id={id} not found")


class AlreadyExistsError(Exception):
    def __init__(self, entity: str, field: str, value: str) -> None:
        self.entity = entity
        self.field = field
        self.value = value
        super().__init__(f"{entity} with {field}='{value}' already exists")
