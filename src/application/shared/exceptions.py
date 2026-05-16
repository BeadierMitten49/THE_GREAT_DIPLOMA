class NotFoundError(Exception):
    def __init__(self, entity: str, id: int) -> None:
        self.entity = entity
        self.id = id
        super().__init__(f"{entity} with id={id} not found")
