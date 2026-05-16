from src.application.delivery.dto import CreateDeliveryDTO
from src.application.shared.exceptions import AlreadyExistsError, NotFoundError
from src.domain.delivery.entities import Delivery
from src.domain.delivery.interfaces import IDeliveryRepository
from src.domain.delivery.value_objects import DeliveryStatus


async def get_delivery(delivery_id: int, repo: IDeliveryRepository) -> Delivery:
    delivery = await repo.get_by_id(delivery_id)
    if delivery is None:
        raise NotFoundError("Delivery", delivery_id)
    return delivery


async def get_deliveries(
    repo: IDeliveryRepository,
    executor_id: int | None = None,
    status: DeliveryStatus | None = None,
) -> list[Delivery]:
    if executor_id is not None:
        return await repo.get_by_executor(executor_id)
    if status is not None:
        return await repo.get_by_status(status)
    return await repo.get_all()


async def create_delivery(dto: CreateDeliveryDTO, repo: IDeliveryRepository) -> int:
    existing = await repo.get_by_order(dto.order_id)
    if existing is not None:
        raise AlreadyExistsError("Delivery", "order_id", str(dto.order_id))
    delivery = Delivery(
        order_id=dto.order_id,
        executor_id=dto.executor_id,
        planned_date=dto.planned_date,
    )
    return await repo.save(delivery)


async def pick_up_order(delivery_id: int, repo: IDeliveryRepository) -> None:
    delivery = await get_delivery(delivery_id, repo)
    delivery.pick_up()
    await repo.save(delivery)


async def start_delivery(delivery_id: int, repo: IDeliveryRepository) -> None:
    delivery = await get_delivery(delivery_id, repo)
    delivery.start()
    await repo.save(delivery)


async def complete_delivery(delivery_id: int, repo: IDeliveryRepository) -> None:
    delivery = await get_delivery(delivery_id, repo)
    delivery.complete()
    await repo.save(delivery)


async def cancel_delivery(
    delivery_id: int, reason: str, repo: IDeliveryRepository
) -> None:
    delivery = await get_delivery(delivery_id, repo)
    delivery.cancel(reason=reason)
    await repo.save(delivery)
