from src.application.shared.exceptions import NotFoundError

__all__ = ["NotFoundError", "InsufficientStockError"]


class InsufficientStockError(Exception):
    def __init__(self, product_id: int, required: int, available: int) -> None:
        self.product_id = product_id
        self.required = required
        self.available = available
        super().__init__(
            f"Product {product_id}: required {required}, available {available}"
        )
