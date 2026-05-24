from datetime import date

import pytest

from src.application.orders.dto import ChangeOrderStatusDTO, CreateOrderDTO, EditOrderDTO
from src.application.orders.exceptions import InsufficientStockError, NotFoundError
from src.application.orders.use_cases import (
    change_order_status,
    create_order,
    delete_order,
    edit_order,
    get_order,
    get_order_items,
    get_orders,
    release_order_reservations,
    release_product_reservation,
    reserve_product_for_order,
)
from src.domain.orders.entities import Order, OrderItem, ProductReservation
from src.domain.orders.value_objects import OrderStatus
from src.domain.shared.exceptions import InvalidFieldError
from src.domain.tasks.entities import ProductionTask
from src.domain.tasks.value_objects import TaskStatus, TaskType
from src.domain.warehouse.entities import ProductStock

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# get_order
# ---------------------------------------------------------------------------


class TestGetOrder:
    async def test_returns_order_when_found(self, order_repo, saved_order):
        result = await get_order(saved_order.id, order_repo)
        assert result.id == saved_order.id
        assert result.customer_id == 1

    async def test_raises_not_found_when_missing(self, order_repo):
        with pytest.raises(NotFoundError):
            await get_order(999, order_repo)


# ---------------------------------------------------------------------------
# get_orders
# ---------------------------------------------------------------------------


class TestGetOrders:
    async def test_returns_all_active(self, order_repo, saved_order):
        result = await get_orders(order_repo)
        assert len(result) == 1

    async def test_filter_by_status(self, order_repo):
        o1 = Order(customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1),
                   number=1, status=OrderStatus.created)
        o2 = Order(customer_id=2, delivery_address="b", delivery_date=date(2026, 6, 1),
                   number=2, status=OrderStatus.production)
        await order_repo.save(o1)
        await order_repo.save(o2)
        result = await get_orders(order_repo, status=OrderStatus.created)
        assert len(result) == 1
        assert result[0].status == OrderStatus.created

    async def test_filter_by_customer(self, order_repo):
        o1 = Order(customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1), number=1)
        o2 = Order(customer_id=2, delivery_address="b", delivery_date=date(2026, 6, 1), number=2)
        await order_repo.save(o1)
        await order_repo.save(o2)
        result = await get_orders(order_repo, customer_id=1)
        assert len(result) == 1
        assert result[0].customer_id == 1

    async def test_excludes_deleted(self, order_repo, saved_order):
        saved_order.delete()
        await order_repo.save(saved_order)
        result = await get_orders(order_repo)
        assert result == []


# ---------------------------------------------------------------------------
# get_order_items
# ---------------------------------------------------------------------------


class TestGetOrderItems:
    async def test_returns_items_for_order(self, order_repo, item_repo, saved_order):
        await item_repo.save(OrderItem(order_id=saved_order.id, product_id=1, quantity=10))
        await item_repo.save(OrderItem(order_id=saved_order.id, product_id=2, quantity=5))
        result = await get_order_items(saved_order.id, item_repo)
        assert len(result) == 2

    async def test_returns_empty_when_no_items(self, item_repo):
        result = await get_order_items(999, item_repo)
        assert result == []


# ---------------------------------------------------------------------------
# create_order
# ---------------------------------------------------------------------------


class TestCreateOrder:
    async def test_creates_order_and_returns_id(self, order_repo, item_repo):
        dto = CreateOrderDTO(
            customer_id=1,
            delivery_address="ул. Пушкина, 1",
            delivery_date=date(2026, 6, 1),
            items=[(1, 100), (2, 50)],
        )
        id_ = await create_order(dto, order_repo, item_repo)
        assert isinstance(id_, int)

    async def test_order_has_status_created(self, order_repo, item_repo):
        dto = CreateOrderDTO(
            customer_id=1,
            delivery_address="ул. Пушкина, 1",
            delivery_date=date(2026, 6, 1),
            items=[(1, 100)],
        )
        id_ = await create_order(dto, order_repo, item_repo)
        order = await order_repo.get_by_id(id_)
        assert order.status == OrderStatus.created

    async def test_order_number_increments(self, order_repo, item_repo):
        dto = CreateOrderDTO(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1), items=[(1, 10)]
        )
        id1 = await create_order(dto, order_repo, item_repo)
        id2 = await create_order(dto, order_repo, item_repo)
        o1 = await order_repo.get_by_id(id1)
        o2 = await order_repo.get_by_id(id2)
        assert o2.number == o1.number + 1

    async def test_items_are_saved(self, order_repo, item_repo):
        dto = CreateOrderDTO(
            customer_id=1,
            delivery_address="ул. Пушкина, 1",
            delivery_date=date(2026, 6, 1),
            items=[(1, 100), (2, 50)],
        )
        id_ = await create_order(dto, order_repo, item_repo)
        items = await item_repo.get_by_order(id_)
        assert len(items) == 2
        quantities = {i.product_id: i.quantity for i in items}
        assert quantities[1] == 100
        assert quantities[2] == 50


# ---------------------------------------------------------------------------
# change_order_status
# ---------------------------------------------------------------------------


class TestChangeOrderStatusSimple:
    async def test_created_to_production(self, order_repo, item_repo, reservation_repo, stock_repo, saved_order):
        dto = ChangeOrderStatusDTO(order_id=saved_order.id, new_status=OrderStatus.production)
        await change_order_status(dto, order_repo, item_repo, reservation_repo, stock_repo)
        order = await order_repo.get_by_id(saved_order.id)
        assert order.status == OrderStatus.production

    async def test_raises_not_found_when_missing(self, order_repo, item_repo, reservation_repo, stock_repo):
        dto = ChangeOrderStatusDTO(order_id=999, new_status=OrderStatus.production)
        with pytest.raises(NotFoundError):
            await change_order_status(dto, order_repo, item_repo, reservation_repo, stock_repo)

    async def test_invalid_transition_raises(self, order_repo, item_repo, reservation_repo, stock_repo, saved_order):
        dto = ChangeOrderStatusDTO(order_id=saved_order.id, new_status=OrderStatus.completed)
        with pytest.raises(InvalidFieldError):
            await change_order_status(dto, order_repo, item_repo, reservation_repo, stock_repo)


class TestChangeOrderStatusToAssembly:
    async def test_created_to_assembly_succeeds_without_tasks(
        self, order_repo, item_repo, reservation_repo, stock_repo
    ):
        order = Order(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1), number=1
        )
        await order_repo.save(order)
        await item_repo.save(OrderItem(order_id=order.id, product_id=1, quantity=100))
        dto = ChangeOrderStatusDTO(order_id=order.id, new_status=OrderStatus.assembly)
        await change_order_status(dto, order_repo, item_repo, reservation_repo, stock_repo)
        updated = await order_repo.get_by_id(order.id)
        assert updated.status == OrderStatus.assembly

    async def test_production_to_assembly_succeeds_when_all_tasks_closed(
        self, order_repo, item_repo, reservation_repo, stock_repo, task_repo
    ):
        order = Order(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1),
            number=1, status=OrderStatus.production
        )
        await order_repo.save(order)
        task = ProductionTask(
            product_id=1, quantity=100, executor_id=1,
            start_date=date(2026, 5, 1), deadline=date(2026, 6, 1),
            task_type=TaskType.order_task, order_id=order.id,
            status=TaskStatus.closed,
        )
        await task_repo.save(task)
        dto = ChangeOrderStatusDTO(order_id=order.id, new_status=OrderStatus.assembly)
        await change_order_status(
            dto, order_repo, item_repo, reservation_repo, stock_repo, task_repo=task_repo
        )
        updated = await order_repo.get_by_id(order.id)
        assert updated.status == OrderStatus.assembly

    async def test_production_to_assembly_raises_when_no_tasks(
        self, order_repo, item_repo, reservation_repo, stock_repo, task_repo
    ):
        order = Order(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1),
            number=1, status=OrderStatus.production
        )
        await order_repo.save(order)
        dto = ChangeOrderStatusDTO(order_id=order.id, new_status=OrderStatus.assembly)
        with pytest.raises(InvalidFieldError):
            await change_order_status(
                dto, order_repo, item_repo, reservation_repo, stock_repo, task_repo=task_repo
            )

    async def test_production_to_assembly_raises_when_task_not_closed(
        self, order_repo, item_repo, reservation_repo, stock_repo, task_repo
    ):
        order = Order(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1),
            number=1, status=OrderStatus.production
        )
        await order_repo.save(order)
        task = ProductionTask(
            product_id=1, quantity=100, executor_id=1,
            start_date=date(2026, 5, 1), deadline=date(2026, 6, 1),
            task_type=TaskType.order_task, order_id=order.id,
            status=TaskStatus.in_progress,
        )
        await task_repo.save(task)
        dto = ChangeOrderStatusDTO(order_id=order.id, new_status=OrderStatus.assembly)
        with pytest.raises(InvalidFieldError):
            await change_order_status(
                dto, order_repo, item_repo, reservation_repo, stock_repo, task_repo=task_repo
            )


class TestChangeOrderStatusToDelivery:
    async def test_writes_off_stock_and_deletes_reservations(
        self, order_repo, item_repo, reservation_repo, stock_repo, saved_stock
    ):
        order = Order(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1),
            number=1, status=OrderStatus.assembly
        )
        await order_repo.save(order)
        await item_repo.save(OrderItem(order_id=order.id, product_id=1, quantity=100, is_assembled=True))
        await reservation_repo.save(
            ProductReservation(order_id=order.id, stock_id=saved_stock.id, quantity=100)
        )

        dto = ChangeOrderStatusDTO(order_id=order.id, new_status=OrderStatus.delivery)
        await change_order_status(dto, order_repo, item_repo, reservation_repo, stock_repo)

        updated_stock = await stock_repo.get_by_id(saved_stock.id)
        assert updated_stock.quantity == 100  # 200 - 100

        reservations = await reservation_repo.get_by_order(order.id)
        assert reservations == []

        updated_order = await order_repo.get_by_id(order.id)
        assert updated_order.status == OrderStatus.delivery

    async def test_raises_insufficient_when_no_reservations(
        self, order_repo, item_repo, reservation_repo, stock_repo
    ):
        order = Order(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1),
            number=1, status=OrderStatus.assembly
        )
        await order_repo.save(order)
        await item_repo.save(OrderItem(order_id=order.id, product_id=1, quantity=100, is_assembled=True))
        dto = ChangeOrderStatusDTO(order_id=order.id, new_status=OrderStatus.delivery)
        with pytest.raises(InsufficientStockError):
            await change_order_status(dto, order_repo, item_repo, reservation_repo, stock_repo)

    async def test_raises_insufficient_when_partial_reservations(
        self, order_repo, item_repo, reservation_repo, stock_repo, saved_stock
    ):
        order = Order(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1),
            number=1, status=OrderStatus.assembly
        )
        await order_repo.save(order)
        await item_repo.save(OrderItem(order_id=order.id, product_id=1, quantity=100, is_assembled=True))
        await reservation_repo.save(
            ProductReservation(order_id=order.id, stock_id=saved_stock.id, quantity=50)
        )
        dto = ChangeOrderStatusDTO(order_id=order.id, new_status=OrderStatus.delivery)
        with pytest.raises(InsufficientStockError):
            await change_order_status(dto, order_repo, item_repo, reservation_repo, stock_repo)


# ---------------------------------------------------------------------------
# edit_order
# ---------------------------------------------------------------------------


class TestEditOrder:
    async def test_updates_fields(self, order_repo, item_repo, saved_order):
        dto = EditOrderDTO(
            order_id=saved_order.id,
            delivery_address="ул. Лермонтова, 5",
            delivery_date=date(2026, 7, 15),
            items=[(1, 200)],
            comment="обновлено",
        )
        await edit_order(dto, order_repo, item_repo)
        order = await order_repo.get_by_id(saved_order.id)
        assert order.delivery_address == "ул. Лермонтова, 5"
        assert order.comment == "обновлено"

    async def test_replaces_items_atomically(self, order_repo, item_repo, saved_order):
        await item_repo.save(OrderItem(order_id=saved_order.id, product_id=1, quantity=100))
        dto = EditOrderDTO(
            order_id=saved_order.id,
            delivery_address="ул. Пушкина, 1",
            delivery_date=date(2026, 6, 1),
            items=[(2, 50), (3, 75)],
        )
        await edit_order(dto, order_repo, item_repo)
        items = await item_repo.get_by_order(saved_order.id)
        assert len(items) == 2
        product_ids = {i.product_id for i in items}
        assert product_ids == {2, 3}

    async def test_raises_not_found_when_missing(self, order_repo, item_repo):
        dto = EditOrderDTO(
            order_id=999, delivery_address="a", delivery_date=date(2026, 6, 1), items=[]
        )
        with pytest.raises(NotFoundError):
            await edit_order(dto, order_repo, item_repo)

    async def test_raises_when_order_in_delivery(self, order_repo, item_repo):
        order = Order(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1),
            number=1, status=OrderStatus.delivery
        )
        await order_repo.save(order)
        dto = EditOrderDTO(
            order_id=order.id, delivery_address="b", delivery_date=date(2026, 6, 1), items=[]
        )
        with pytest.raises(InvalidFieldError):
            await edit_order(dto, order_repo, item_repo)

    async def test_raises_when_order_completed(self, order_repo, item_repo):
        order = Order(
            customer_id=1, delivery_address="a", delivery_date=date(2026, 6, 1),
            number=1, status=OrderStatus.completed
        )
        await order_repo.save(order)
        dto = EditOrderDTO(
            order_id=order.id, delivery_address="b", delivery_date=date(2026, 6, 1), items=[]
        )
        with pytest.raises(InvalidFieldError):
            await edit_order(dto, order_repo, item_repo)


# ---------------------------------------------------------------------------
# delete_order
# ---------------------------------------------------------------------------


class TestDeleteOrder:
    async def test_soft_deletes_order(self, order_repo, reservation_repo, saved_order):
        await delete_order(saved_order.id, order_repo, reservation_repo)
        order = await order_repo.get_by_id(saved_order.id)
        assert order.is_active is False

    async def test_releases_reservations(self, order_repo, reservation_repo, saved_order, saved_stock):
        await reservation_repo.save(
            ProductReservation(order_id=saved_order.id, stock_id=saved_stock.id, quantity=50)
        )
        await delete_order(saved_order.id, order_repo, reservation_repo)
        assert await reservation_repo.get_by_order(saved_order.id) == []

    async def test_raises_not_found_when_missing(self, order_repo, reservation_repo):
        with pytest.raises(NotFoundError):
            await delete_order(999, order_repo, reservation_repo)


# ---------------------------------------------------------------------------
# reserve_product_for_order
# ---------------------------------------------------------------------------


class TestReserveProductForOrder:
    async def test_creates_reservation(
        self, order_repo, reservation_repo, stock_repo, saved_order, saved_stock
    ):
        reservation_id = await reserve_product_for_order(
            saved_order.id, saved_stock.id, 100,
            order_repo, reservation_repo, stock_repo,
        )
        assert isinstance(reservation_id, int)
        reservation = await reservation_repo.get_by_id(reservation_id)
        assert reservation.order_id == saved_order.id
        assert reservation.stock_id == saved_stock.id
        assert reservation.quantity == 100

    async def test_raises_not_found_when_order_missing(
        self, order_repo, reservation_repo, stock_repo, saved_stock
    ):
        with pytest.raises(NotFoundError):
            await reserve_product_for_order(
                999, saved_stock.id, 50, order_repo, reservation_repo, stock_repo
            )

    async def test_raises_not_found_when_stock_missing(
        self, order_repo, reservation_repo, stock_repo, saved_order
    ):
        with pytest.raises(NotFoundError):
            await reserve_product_for_order(
                saved_order.id, 999, 50, order_repo, reservation_repo, stock_repo
            )

    async def test_raises_insufficient_when_over_reserving(
        self, order_repo, reservation_repo, stock_repo, saved_order, saved_stock
    ):
        # saved_stock has quantity=200, already reserve 150
        await reservation_repo.save(
            ProductReservation(order_id=saved_order.id, stock_id=saved_stock.id, quantity=150)
        )
        with pytest.raises(InsufficientStockError):
            await reserve_product_for_order(
                saved_order.id, saved_stock.id, 100,
                order_repo, reservation_repo, stock_repo,
            )


# ---------------------------------------------------------------------------
# release_product_reservation
# ---------------------------------------------------------------------------


class TestReleaseProductReservation:
    async def test_deletes_reservation(
        self, reservation_repo, saved_order, saved_stock
    ):
        r = ProductReservation(order_id=saved_order.id, stock_id=saved_stock.id, quantity=50)
        await reservation_repo.save(r)
        await release_product_reservation(r.id, reservation_repo)
        assert await reservation_repo.get_by_id(r.id) is None

    async def test_raises_not_found_when_missing(self, reservation_repo):
        with pytest.raises(NotFoundError):
            await release_product_reservation(999, reservation_repo)


# ---------------------------------------------------------------------------
# release_order_reservations
# ---------------------------------------------------------------------------


class TestReleaseOrderReservations:
    async def test_deletes_all_reservations(
        self, order_repo, reservation_repo, saved_order, saved_stock
    ):
        await reservation_repo.save(
            ProductReservation(order_id=saved_order.id, stock_id=saved_stock.id, quantity=50)
        )
        await reservation_repo.save(
            ProductReservation(order_id=saved_order.id, stock_id=saved_stock.id, quantity=30)
        )
        await release_order_reservations(saved_order.id, order_repo, reservation_repo)
        assert await reservation_repo.get_by_order(saved_order.id) == []

    async def test_raises_not_found_when_order_missing(self, order_repo, reservation_repo):
        with pytest.raises(NotFoundError):
            await release_order_reservations(999, order_repo, reservation_repo)
