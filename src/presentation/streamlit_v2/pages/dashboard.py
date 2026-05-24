import datetime
from decimal import Decimal

import streamlit as st

from api_client import APIError, get_client

client = get_client()

TODAY = datetime.date.today()

TASK_STATUS_LABELS = {
    "created": "Создана",
    "in_progress": "В работе",
    "stopped": "Остановлена",
    "completed": "Завершена",
    "closed": "Закрыта",
}

DELIVERY_STATUS_LABELS = {
    "pending": "Ожидает",
    "picked_up": "У водителя",
    "in_transit": "В пути",
    "completed": "Доставлено",
    "cancelled": "Отменена",
}

DELIVERY_STATUS_ICONS = {
    "pending": "⏳",
    "picked_up": "🔵",
    "in_transit": "🚛",
    "completed": "✅",
    "cancelled": "❌",
}


def _err(e: APIError) -> None:
    st.error(f"Ошибка {e.status_code}: {e.detail}")


# ── Load data ────────────────────────────────────────────────────────────────

try:
    raw_materials = client.get("/references/raw-materials", include_inactive=False)
    products = client.get("/references/products", include_inactive=False)
    packaging = client.get("/references/packaging", include_inactive=False)
except APIError as e:
    _err(e)
    raw_materials, products, packaging = [], [], []

rm_map = {r["id"]: r for r in raw_materials}
product_map = {p["id"]: p for p in products}
pkg_map = {p["id"]: p for p in packaging}


# ── Critical stock ───────────────────────────────────────────────────────────

def _get_critical_stock() -> list[dict]:
    items = []
    try:
        raw_stocks = client.get("/warehouse/raw-material-stock")
        totals_rm: dict[int, Decimal] = {}
        for s in raw_stocks:
            rm_id = s["raw_material_id"]
            totals_rm[rm_id] = totals_rm.get(rm_id, Decimal("0")) + Decimal(str(s["quantity"]))
        for rm_id, total in totals_rm.items():
            rm = rm_map.get(rm_id)
            if rm and total < Decimal(str(rm["critical_stock"])):
                severity = "danger" if total < Decimal(str(rm["critical_stock"])) / 2 else "warn"
                items.append({
                    "type": "Сырьё",
                    "name": rm["name"],
                    "quantity": f"{total} {rm['unit']}",
                    "threshold": rm["critical_stock"],
                    "severity": severity,
                })
    except APIError:
        pass

    try:
        prod_stocks = client.get("/warehouse/product-stock")
        totals_prod: dict[int, int] = {}
        for s in prod_stocks:
            pid = s["product_id"]
            totals_prod[pid] = totals_prod.get(pid, 0) + s["quantity"]
        for pid, total in totals_prod.items():
            p = product_map.get(pid)
            if p and total < p["critical_stock"]:
                severity = "danger" if total < p["critical_stock"] // 2 else "warn"
                items.append({
                    "type": "Продукция",
                    "name": p["name"],
                    "quantity": f"{total} шт",
                    "threshold": p["critical_stock"],
                    "severity": severity,
                })
    except APIError:
        pass

    try:
        pkg_stocks = client.get("/warehouse/packaging-stock")
        totals_pkg: dict[int, int] = {}
        for s in pkg_stocks:
            pid = s["packaging_id"]
            totals_pkg[pid] = totals_pkg.get(pid, 0) + s["quantity"]
        for pid, total in totals_pkg.items():
            p = pkg_map.get(pid)
            if p and total < p["critical_stock"]:
                severity = "danger" if total < p["critical_stock"] // 2 else "warn"
                items.append({
                    "type": "Упаковка",
                    "name": p["name"],
                    "quantity": f"{total} {p['unit']}",
                    "threshold": p["critical_stock"],
                    "severity": severity,
                })
    except APIError:
        pass

    return items


# ── Active reserves ──────────────────────────────────────────────────────────

def _get_active_reserves() -> list[dict]:
    reserves = []
    try:
        orders = client.get("/orders", status="assembly")
        for order in orders[:5]:
            items = client.get(f"/orders/{order['id']}/items")
            reservations = client.get(f"/orders/{order['id']}/reservations")
            for res in reservations:
                stock_id = res["stock_id"]
                try:
                    stock = client.get(f"/warehouse/product-stock/{stock_id}")
                    p = product_map.get(stock.get("product_id", 0))
                    batch = f"П-{stock.get('batch_year', '?')}-{stock.get('batch_number', 0):03d}"
                    reserves.append({
                        "product": p["name"] if p else "?",
                        "batch": batch,
                        "order": f"№{order['number']}",
                        "qty": res["quantity"],
                        "date": order["delivery_date"],
                    })
                except APIError:
                    pass
    except APIError:
        pass
    return reserves


# ── Overdue tasks ────────────────────────────────────────────────────────────

def _get_overdue_tasks() -> list[dict]:
    overdue = []
    try:
        tasks = client.get("/tasks")
        for t in tasks:
            if t["status"] in ("created", "in_progress", "stopped"):
                deadline = datetime.date.fromisoformat(t["deadline"])
                if deadline < TODAY:
                    days = (TODAY - deadline).days
                    p = product_map.get(t["product_id"])
                    overdue.append({
                        "product": p["name"] if p else f"Продукт #{t['product_id']}",
                        "quantity": f"{t['quantity']} шт",
                        "status": TASK_STATUS_LABELS.get(t["status"], t["status"]),
                        "executor": t.get("executor_name", f"#{t['executor_id']}"),
                        "code": f"T-{t['id']:04d}",
                        "overdue_days": days,
                    })
    except APIError:
        pass
    return overdue


# ── Upcoming deliveries ──────────────────────────────────────────────────────

def _get_upcoming_deliveries() -> list[dict]:
    upcoming = []
    try:
        deliveries = client.get("/deliveries")
        deliveries = [
            d for d in deliveries
            if d["status"] not in ("completed", "cancelled")
        ]
        users = client.get("/users")
        user_map = {u["id"]: u["full_name"] for u in users}

        for d in deliveries[:5]:
            try:
                order = client.get(f"/orders/{d['order_id']}")
                customer = order.get("customer_name", f"Заказ #{d['order_id']}")
            except APIError:
                customer = f"Заказ #{d['order_id']}"
            label = DELIVERY_STATUS_LABELS.get(d["status"], d["status"])
            icon = DELIVERY_STATUS_ICONS.get(d["status"], "")
            upcoming.append({
                "customer": customer,
                "date": d["planned_date"],
                "courier": user_map.get(d["executor_id"], f"#{d['executor_id']}"),
                "status": label,
                "icon": icon,
            })
    except APIError:
        pass
    return upcoming


# ── Tasks for review (completed, awaiting close) ─────────────────────────────

def _get_tasks_for_review() -> list[dict]:
    review = []
    try:
        tasks = client.get("/tasks", status="completed")
        for t in tasks[:5]:
            p = product_map.get(t["product_id"])
            review.append({
                "product": p["name"] if p else f"Продукт #{t['product_id']}",
                "quantity": f"{t['quantity']} шт",
                "executor": t.get("executor_name", f"#{t['executor_id']}"),
                "code": f"T-{t['id']:04d}",
            })
    except APIError:
        pass
    return review


# ── Notifications ────────────────────────────────────────────────────────────

def _get_notifications() -> list[dict]:
    try:
        notifications = client.get("/notifications", unread_only=True)
        return notifications[:10]
    except APIError:
        return []


# ── Render ───────────────────────────────────────────────────────────────────

st.title("Дашборд")
st.caption(f"Сегодня, {TODAY.strftime('%d.%m.%Y')}")

critical_stock = _get_critical_stock()
active_reserves = _get_active_reserves()
overdue_tasks = _get_overdue_tasks()
upcoming_deliveries = _get_upcoming_deliveries()
tasks_for_review = _get_tasks_for_review()
notifications = _get_notifications()

# ── Row 1 ────────────────────────────────────────────────────────────────────

c1, c2 = st.columns(2)

with c1:
    st.markdown("**Критические остатки**")
    if not critical_stock:
        st.success("Все остатки в норме")
    else:
        st.caption(f"{len(critical_stock)} позиций")
        for item in critical_stock:
            icon = "🔴" if item["severity"] == "danger" else "🟡"
            st.markdown(
                f"{icon} **{item['name']}** — {item['quantity']} "
                f"*(порог {item['threshold']}, {item['type'].lower()})*"
            )

with c2:
    st.markdown("**Активные резервы**")
    if not active_reserves:
        st.success("Активных резервов нет")
    else:
        for r in active_reserves[:3]:
            st.markdown(
                f"- **{r['product']}** — {r['qty']} шт "
                f"*(партия {r['batch']}, заказ {r['order']}, {r['date']})*"
            )
        if len(active_reserves) > 3:
            st.caption(f"+ {len(active_reserves) - 3} ещё")

# ── Row 2 ────────────────────────────────────────────────────────────────────

st.divider()
c3, c4 = st.columns(2)

with c3:
    st.markdown("**Просроченные задачи**")
    if not overdue_tasks:
        st.success("Все задачи в сроки")
    else:
        st.caption(f"{len(overdue_tasks)} задач")
        for t in overdue_tasks[:3]:
            with st.container(border=True):
                st.markdown(f"**{t['product']}** · {t['quantity']}")
                st.caption(
                    f"{t['executor']} · {t['code']} · "
                    f"*{t['status']}* · "
                    f"🔴 Просрочена на {t['overdue_days']} дн."
                )
        if len(overdue_tasks) > 3:
            st.caption(f"+ {len(overdue_tasks) - 3} ещё")

with c4:
    st.markdown("**Ближайшие доставки**")
    if not upcoming_deliveries:
        st.success("Ближайших доставок нет")
    else:
        st.caption(f"{len(upcoming_deliveries)} доставок")
        for d in upcoming_deliveries[:3]:
            st.markdown(
                f"- {d['icon']} **{d['customer']}** — {d['date']} · {d['courier']} · *{d['status']}*"
            )
        if len(upcoming_deliveries) > 3:
            st.caption(f"+ {len(upcoming_deliveries) - 3} ещё")

# ── Row 3 ────────────────────────────────────────────────────────────────────

st.divider()
c5, c6 = st.columns(2)

with c5:
    st.markdown("**Задачи на проверку**")
    if not tasks_for_review:
        st.success("Все задачи закрыты")
    else:
        st.caption(f"{len(tasks_for_review)} задач · ждут закрытия")
        for t in tasks_for_review[:3]:
            with st.container(border=True):
                st.markdown(f"**{t['product']}** · {t['quantity']}")
                st.caption(f"{t['executor']} · {t['code']}")
        if len(tasks_for_review) > 3:
            st.caption(f"+ {len(tasks_for_review) - 3} ещё")

with c6:
    st.markdown("**Уведомления**")
    if not notifications:
        st.info("Новых уведомлений нет")
    else:
        st.caption(f"{len(notifications)} новых")
        for n in notifications[:5]:
            created = n.get("created_at", "")[:16].replace("T", " · ")
            st.markdown(f"**{created}** — {n['title']}")
        if len(notifications) > 5:
            st.caption(f"+ {len(notifications) - 5} ещё")
        if st.button("Отметить все прочитанными", key="mark_all_read"):
            try:
                client.post("/notifications/read-all")
                st.rerun()
            except APIError as e:
                _err(e)
