from decimal import Decimal

import pytest

from src.domain.references.entities import (
    Customer,
    PackagingCatalog,
    Product,
    RawMaterialCatalog,
    RecipeLine,
)
from src.domain.references.exceptions import InvalidFieldError

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------


class TestCustomerCreation:
    def test_create_with_valid_data(self, customer):
        assert customer.name == "ООО Ромашка"
        assert customer.default_address == "ул. Ленина, 1"
        assert customer.is_active is True
        assert customer.id is None

    @pytest.mark.smoke
    @pytest.mark.parametrize("name", ["", "   "])
    def test_create_with_blank_name_raises(self, name):
        with pytest.raises(InvalidFieldError, match="name"):
            Customer(name=name, default_address="addr")

    @pytest.mark.parametrize("address", ["", "   "])
    def test_create_with_blank_address_raises(self, address):
        with pytest.raises(InvalidFieldError, match="default_address"):
            Customer(name="X", default_address=address)


class TestCustomerUpdate:
    def test_update_with_valid_data(self, customer):
        customer.update("New Name", "New addr")
        assert customer.name == "New Name"
        assert customer.default_address == "New addr"

    def test_update_with_blank_name_raises(self, customer):
        with pytest.raises(InvalidFieldError, match="name"):
            customer.update("", "addr")

    def test_update_with_blank_address_raises(self, customer):
        with pytest.raises(InvalidFieldError, match="default_address"):
            customer.update("X", "")

    def test_update_leaves_fields_unchanged_on_error(self, customer):
        with pytest.raises(InvalidFieldError):
            customer.update("", "addr")
        assert customer.name == "ООО Ромашка"


class TestCustomerActivation:
    def test_deactivate_sets_inactive(self, customer):
        customer.deactivate()
        assert customer.is_active is False

    def test_activate_sets_active(self):
        c = Customer(name="X", default_address="addr", is_active=False)
        c.activate()
        assert c.is_active is True

    def test_deactivate_twice_stays_inactive(self, customer):
        customer.deactivate()
        customer.deactivate()
        assert customer.is_active is False


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------


class TestProductCreation:
    def test_create_with_valid_data(self, product):
        assert product.name == "Сахар фасованный"
        assert product.recipe == []
        assert product.id is None

    @pytest.mark.smoke
    @pytest.mark.parametrize("units_per_box", [0, -1])
    def test_create_with_non_positive_units_per_box_raises(self, units_per_box):
        with pytest.raises(InvalidFieldError, match="units_per_box"):
            Product(name="X", units_per_box=units_per_box, shelf_life_days=1, critical_stock=0)

    @pytest.mark.parametrize("shelf_life_days", [0, -1])
    def test_create_with_non_positive_shelf_life_raises(self, shelf_life_days):
        with pytest.raises(InvalidFieldError, match="shelf_life_days"):
            Product(name="X", units_per_box=1, shelf_life_days=shelf_life_days, critical_stock=0)

    def test_create_with_negative_critical_stock_raises(self):
        with pytest.raises(InvalidFieldError, match="critical_stock"):
            Product(name="X", units_per_box=1, shelf_life_days=1, critical_stock=-1)

    def test_create_with_zero_critical_stock_is_allowed(self):
        p = Product(name="X", units_per_box=1, shelf_life_days=1, critical_stock=0)
        assert p.critical_stock == 0


class TestProductUpdate:
    def test_update_with_valid_data(self, product):
        product.update("New", 24, 730, 50)
        assert product.name == "New"
        assert product.units_per_box == 24
        assert product.shelf_life_days == 730
        assert product.critical_stock == 50

    def test_update_leaves_fields_unchanged_on_error(self, product):
        with pytest.raises(InvalidFieldError):
            product.update("", 1, 1, 0)
        assert product.name == "Сахар фасованный"


class TestProductRecipe:
    def test_set_recipe_replaces_existing(self, product, recipe_line_factory):
        product.set_recipe([recipe_line_factory(1)])
        product.set_recipe([recipe_line_factory(2), recipe_line_factory(3)])
        assert len(product.recipe) == 2
        assert product.recipe[0].raw_material_id == 2

    def test_set_empty_recipe_is_allowed(self, product):
        product.set_recipe([])
        assert product.recipe == []

    @pytest.mark.smoke
    @pytest.mark.parametrize("consumption", ["0", "-1"])
    def test_set_recipe_with_non_positive_consumption_raises(self, product, recipe_line_factory, consumption):
        with pytest.raises(InvalidFieldError, match="consumption_per_unit"):
            product.set_recipe([recipe_line_factory(consumption=consumption)])

    @pytest.mark.parametrize("waste", ["-1", "100.01"])
    def test_set_recipe_with_out_of_range_waste_raises(self, product, recipe_line_factory, waste):
        with pytest.raises(InvalidFieldError, match="waste_percentage"):
            product.set_recipe([recipe_line_factory(waste=waste)])

    @pytest.mark.parametrize("waste", ["0", "100"])
    def test_set_recipe_with_boundary_waste_is_allowed(self, product, recipe_line_factory, waste):
        product.set_recipe([recipe_line_factory(waste=waste)])
        assert len(product.recipe) == 1

    def test_set_recipe_not_mutated_on_error(self, product, recipe_line_factory):
        product.set_recipe([recipe_line_factory(1)])
        with pytest.raises(InvalidFieldError):
            product.set_recipe([recipe_line_factory(2), recipe_line_factory(consumption="0")])
        assert len(product.recipe) == 1


# ---------------------------------------------------------------------------
# RawMaterialCatalog
# ---------------------------------------------------------------------------


class TestRawMaterialCatalogCreation:
    def test_create_with_valid_data(self, raw_material):
        assert raw_material.name == "Сахар-сырец"
        assert raw_material.is_active is True
        assert raw_material.id is None

    @pytest.mark.parametrize("name", ["", "  "])
    def test_create_with_blank_name_raises(self, name):
        with pytest.raises(InvalidFieldError, match="name"):
            RawMaterialCatalog(name=name, unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))

    @pytest.mark.parametrize("unit", ["", "  "])
    def test_create_with_blank_unit_raises(self, unit):
        with pytest.raises(InvalidFieldError, match="unit"):
            RawMaterialCatalog(name="X", unit=unit, shelf_life_days=1, critical_stock=Decimal("0"))

    @pytest.mark.parametrize("days", [0, -1])
    def test_create_with_non_positive_shelf_life_raises(self, days):
        with pytest.raises(InvalidFieldError, match="shelf_life_days"):
            RawMaterialCatalog(name="X", unit="кг", shelf_life_days=days, critical_stock=Decimal("0"))

    def test_create_with_negative_critical_stock_raises(self):
        with pytest.raises(InvalidFieldError, match="critical_stock"):
            RawMaterialCatalog(name="X", unit="кг", shelf_life_days=1, critical_stock=Decimal("-0.1"))

    def test_create_with_zero_critical_stock_is_allowed(self):
        r = RawMaterialCatalog(name="X", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"))
        assert r.critical_stock == Decimal("0")


class TestRawMaterialCatalogUpdate:
    def test_update_with_valid_data(self, raw_material):
        raw_material.update("New", "л", 365, Decimal("10.5"))
        assert raw_material.name == "New"
        assert raw_material.unit == "л"

    def test_update_leaves_fields_unchanged_on_error(self, raw_material):
        with pytest.raises(InvalidFieldError):
            raw_material.update("", "кг", 1, Decimal("0"))
        assert raw_material.name == "Сахар-сырец"


class TestRawMaterialCatalogActivation:
    def test_deactivate_sets_inactive(self, raw_material):
        raw_material.deactivate()
        assert raw_material.is_active is False

    def test_activate_sets_active(self):
        r = RawMaterialCatalog(name="X", unit="кг", shelf_life_days=1, critical_stock=Decimal("0"), is_active=False)
        r.activate()
        assert r.is_active is True


# ---------------------------------------------------------------------------
# PackagingCatalog
# ---------------------------------------------------------------------------


class TestPackagingCatalogCreation:
    def test_create_with_valid_data(self, packaging):
        assert packaging.name == "Пакет 1кг"
        assert packaging.is_active is True
        assert packaging.id is None

    @pytest.mark.parametrize("name", ["", "  "])
    def test_create_with_blank_name_raises(self, name):
        with pytest.raises(InvalidFieldError, match="name"):
            PackagingCatalog(name=name, unit="шт", critical_stock=0)

    @pytest.mark.parametrize("unit", ["", "  "])
    def test_create_with_blank_unit_raises(self, unit):
        with pytest.raises(InvalidFieldError, match="unit"):
            PackagingCatalog(name="X", unit=unit, critical_stock=0)

    def test_create_with_negative_critical_stock_raises(self):
        with pytest.raises(InvalidFieldError, match="critical_stock"):
            PackagingCatalog(name="X", unit="шт", critical_stock=-1)

    def test_create_with_zero_critical_stock_is_allowed(self):
        p = PackagingCatalog(name="X", unit="шт", critical_stock=0)
        assert p.critical_stock == 0


class TestPackagingCatalogUpdate:
    def test_update_with_valid_data(self, packaging):
        packaging.update("New", "уп", 100)
        assert packaging.name == "New"
        assert packaging.unit == "уп"
        assert packaging.critical_stock == 100

    def test_update_leaves_fields_unchanged_on_error(self, packaging):
        with pytest.raises(InvalidFieldError):
            packaging.update("Old", "", 0)
        assert packaging.unit == "шт"


class TestPackagingCatalogActivation:
    def test_deactivate_sets_inactive(self, packaging):
        packaging.deactivate()
        assert packaging.is_active is False

    def test_activate_sets_active(self):
        p = PackagingCatalog(name="X", unit="шт", critical_stock=0, is_active=False)
        p.activate()
        assert p.is_active is True


# ---------------------------------------------------------------------------
# RecipeLine
# ---------------------------------------------------------------------------


class TestRecipeLine:
    def test_create_with_valid_data(self, recipe_line):
        assert recipe_line.raw_material_id == 1
        assert recipe_line.consumption_per_unit == Decimal("1.05")
        assert recipe_line.waste_percentage == Decimal("2.0")
        assert recipe_line.id is None
