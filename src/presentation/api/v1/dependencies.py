from fastapi import Depends

from src.domain.auth.value_objects import Role
from src.presentation.api.v1.auth.dependencies import require_role

director_only = Depends(require_role(Role.director))
director_or_warehouse = Depends(require_role(Role.director, Role.warehouse))
director_or_production = Depends(require_role(Role.director, Role.production))
director_or_delivery = Depends(require_role(Role.director, Role.delivery))
