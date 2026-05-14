from enum import Enum


class Role(str, Enum):
    director = "director"
    production = "production"
    warehouse = "warehouse"
    delivery = "delivery"
