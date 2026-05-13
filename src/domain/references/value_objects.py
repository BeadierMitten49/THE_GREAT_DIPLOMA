from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RecipeLine:
    raw_material_id: int
    consumption_per_unit: Decimal
    waste_percentage: Decimal  # 0..100
