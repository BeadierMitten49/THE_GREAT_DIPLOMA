import { useState, useEffect, useCallback, useMemo, Fragment } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import api from '../api/client'

// ── helpers ───────────────────────────────────────────────────────────────────

const STATUS_LABELS = {
  created:    'Создан',
  production: 'Производство',
  assembly:   'Сборка',
  delivery:   'Доставка',
  completed:  'Завершён',
  cancelled:  'Отменён',
}

function fmtDate(iso) {
  if (!iso) return '—'
  try { return format(new Date(String(iso).slice(0, 10)), 'dd.MM.yyyy') } catch { return String(iso) }
}

function fmtOrderNum(number) {
  const year = new Date().getFullYear() % 100
  return `${year}-${String(number).padStart(4, '0')}`
}

function itemQtyLabel(item) {
  const upb = item.units_per_box ?? 1
  const qty = item.quantity
  if (upb > 1) {
    const boxes = Math.floor(qty / upb)
    const loose = qty % upb
    if (loose) return `${boxes} кор. / ${loose} шт`
    return `${boxes} кор.`
  }
  return `${qty} шт`
}

const canEdit   = (s) => ['created', 'production', 'assembly'].includes(s)
const canDelete = (s) => ['created', 'production', 'assembly'].includes(s)

// ── API fetchers ──────────────────────────────────────────────────────────────

async function fetchOrders(status, dateFrom, dateTo) {
  const params = {}
  if (status && status !== 'all') params.status = status
  if (dateFrom) params.delivery_date_from = dateFrom
  if (dateTo)   params.delivery_date_to   = dateTo
  const { data } = await api.get('/orders', { params })
  return data
}

async function fetchDrawer(id) {
  const { data } = await api.get(`/orders/${id}/drawer`)
  return data
}

async function fetchCustomers() {
  try {
    const { data } = await api.get('/references/customers')
    return data
  } catch { return [] }
}

async function fetchProducts() {
  try {
    const { data } = await api.get('/references/products')
    return data
  } catch { return [] }
}

async function fetchAllUsers() {
  try {
    const { data } = await api.get('/users')
    return data
  } catch { return [] }
}

async function fetchProductStock(productId) {
  try {
    const { data } = await api.get('/warehouse/product-stock', { params: { product_id: productId } })
    return data
  } catch { return [] }
}

// ── page component ────────────────────────────────────────────────────────────

export default function Orders() {
  const qc = useQueryClient()
  const [selectedId, setSelectedId]             = useState(null)
  const [filterStatus, setFilterStatus]         = useState('all')
  const [filterDateFrom, setFilterDateFrom]     = useState('')
  const [filterDateTo, setFilterDateTo]         = useState('')
  const [createOpen, setCreateOpen]             = useState(false)
  const [editOpen, setEditOpen]                 = useState(false)
  const [toProductionOpen, setToProductionOpen] = useState(false)
  const [toAssemblyOpen, setToAssemblyOpen]     = useState(false)
  const [toDeliveryOpen, setToDeliveryOpen]     = useState(false)
  const [reserveOpen, setReserveOpen]           = useState(false)
  const [releaseOpen, setReleaseOpen]           = useState(false)

  const { data: orders = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['orders', filterStatus, filterDateFrom, filterDateTo],
    queryFn:  () => fetchOrders(filterStatus, filterDateFrom, filterDateTo),
  })

  const { data: drawer } = useQuery({
    queryKey: ['order-drawer', selectedId],
    queryFn:  () => fetchDrawer(selectedId),
    enabled:  !!selectedId,
  })

  const { data: allUsers = [] } = useQuery({ queryKey: ['all-users'], queryFn: fetchAllUsers })

  const deliveryUsers   = useMemo(() =>
    allUsers.filter(u => u.is_active && u.roles?.includes('delivery')), [allUsers])
  const productionUsers = useMemo(() =>
    allUsers.filter(u => u.is_active && (u.roles?.includes('production') || u.roles?.includes('director'))), [allUsers])

  const filtersActive = filterStatus !== 'all' || filterDateFrom || filterDateTo
  const resetFilters  = () => { setFilterStatus('all'); setFilterDateFrom(''); setFilterDateTo('') }

  const handleRowClick = (id) => setSelectedId((prev) => prev === id ? null : id)
  const closeDrawer    = () => setSelectedId(null)

  const invalidateOrder = useCallback(() => {
    qc.invalidateQueries({ queryKey: ['orders'] })
    if (selectedId) qc.invalidateQueries({ queryKey: ['order-drawer', selectedId] })
  }, [qc, selectedId])

  const handleDelete = async (orderId) => {
    if (!window.confirm('Удалить заказ?')) return
    try { await api.delete(`/orders/${orderId}`) } catch { /* ignore */ }
    qc.invalidateQueries({ queryKey: ['orders'] })
    closeDrawer()
  }

  const selectedOrder = drawer?.order ?? orders.find((o) => o.id === selectedId) ?? null

  const allTasksClosed = useMemo(() => {
    const tasks = drawer?.tasks ?? []
    return tasks.length > 0 && tasks.every(t => t.status === 'closed')
  }, [drawer])

  const hasReservations = useMemo(() => {
    const resMap = drawer?.reservations_by_item ?? {}
    return Object.values(resMap).some(list => list.length > 0)
  }, [drawer])

  return (
    <div style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>

        <div style={{ padding: '24px 32px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexShrink: 0 }}>
          <div style={{ fontSize: 24, fontWeight: 500, color: '#0F172A' }}>Заказы</div>
          <button onClick={() => setCreateOpen(true)} style={btnPrimary}>
            <PlusIcon /> Создать заказ
          </button>
        </div>

        <div style={{ padding: '16px 32px 0', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', flexShrink: 0 }}>
          <FilterChip label="Статус" value={filterStatus === 'all' ? 'Все' : STATUS_LABELS[filterStatus]}>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%', height: '100%' }}
            >
              <option value="all">Все</option>
              {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </FilterChip>

          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, height: 34, padding: '0 12px', border: '1px solid #CBD5E1', borderRadius: 8, background: '#FFF', fontSize: 13, color: '#334155' }}>
            <span>Доставка:</span>
            <input
              type="date" value={filterDateFrom}
              onChange={e => setFilterDateFrom(e.target.value)}
              style={{ border: 'none', outline: 'none', fontSize: 13, fontFamily: 'inherit', background: 'transparent', color: filterDateFrom ? '#0F172A' : '#94A3B8' }}
            />
            <span style={{ color: '#94A3B8' }}>—</span>
            <input
              type="date" value={filterDateTo}
              onChange={e => setFilterDateTo(e.target.value)}
              style={{ border: 'none', outline: 'none', fontSize: 13, fontFamily: 'inherit', background: 'transparent', color: filterDateTo ? '#0F172A' : '#94A3B8' }}
            />
          </div>

          {filtersActive && (
            <button onClick={resetFilters} style={{ fontSize: 13, color: '#475569', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              Сброс
            </button>
          )}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 32px 0' }}>
          {isLoading ? (
            <SkeletonTable />
          ) : isError ? (
            <ErrorBlock onRetry={refetch} />
          ) : orders.length === 0 ? (
            <EmptyState onCreate={() => setCreateOpen(true)} />
          ) : (
            <OrderTable orders={orders} selectedId={selectedId} onRowClick={handleRowClick} />
          )}
        </div>
      </div>

      {selectedId && selectedOrder && (
        <aside style={{
          position: 'absolute', right: 0, top: 0, bottom: 0, width: 480,
          background: '#FFFFFF', borderLeft: '1px solid #E2E8F0',
          display: 'flex', flexDirection: 'column', overflow: 'hidden', zIndex: 10,
        }}>
          <DrawerContent
            order={selectedOrder}
            drawerData={drawer}
            allTasksClosed={allTasksClosed}
            hasReservations={hasReservations}
            onClose={closeDrawer}
            onEdit={() => setEditOpen(true)}
            onDelete={() => handleDelete(selectedOrder.id)}
            onToProduction={() => setToProductionOpen(true)}
            onToAssembly={() => setToAssemblyOpen(true)}
            onToDelivery={() => setToDeliveryOpen(true)}
            onManageReserve={() => setReserveOpen(true)}
            onReleaseReserve={() => setReleaseOpen(true)}
          />
        </aside>
      )}

      <CreateOrderModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreate={() => { qc.invalidateQueries({ queryKey: ['orders'] }); setCreateOpen(false) }}
      />

      {selectedOrder && (
        <>
          <EditOrderModal
            open={editOpen && canEdit(selectedOrder.status)}
            order={selectedOrder}
            drawerData={drawer}
            onClose={() => setEditOpen(false)}
            onSave={() => { invalidateOrder(); setEditOpen(false) }}
          />

          <ToProductionModal
            open={toProductionOpen}
            onClose={() => setToProductionOpen(false)}
            order={selectedOrder}
            items={drawer?.items ?? []}
            productionUsers={productionUsers}
            onConfirm={() => { invalidateOrder(); setToProductionOpen(false) }}
          />

          <ReservationModal
            open={toAssemblyOpen}
            onClose={() => setToAssemblyOpen(false)}
            order={selectedOrder}
            items={drawer?.items ?? []}
            drawerData={drawer}
            mode="to_assembly"
            onConfirm={() => { invalidateOrder(); setToAssemblyOpen(false) }}
          />

          <ReservationModal
            open={reserveOpen}
            onClose={() => setReserveOpen(false)}
            order={selectedOrder}
            items={drawer?.items ?? []}
            drawerData={drawer}
            mode="manage"
            onConfirm={() => { invalidateOrder(); setReserveOpen(false) }}
          />

          <ToDeliveryModal
            open={toDeliveryOpen}
            onClose={() => setToDeliveryOpen(false)}
            order={selectedOrder}
            deliveryUsers={deliveryUsers}
            onConfirm={() => { invalidateOrder(); setToDeliveryOpen(false) }}
          />

          <ReleaseReservationsModal
            open={releaseOpen}
            onClose={() => setReleaseOpen(false)}
            orderId={selectedOrder.id}
            orderNum={fmtOrderNum(selectedOrder.number)}
            onConfirm={() => { invalidateOrder(); setReleaseOpen(false) }}
          />
        </>
      )}
    </div>
  )
}

// ── OrderTable ────────────────────────────────────────────────────────────────

function OrderTable({ orders, selectedId, onRowClick }) {
  return (
    <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden', marginBottom: 16 }}>
      <div style={gridRow}>
        {['№', 'Заказчик', 'Дата доставки', 'Статус', ''].map((h, i) => (
          <div key={i} style={thStyle}>{h}</div>
        ))}
      </div>
      {orders.map((order, idx) => (
        <div
          key={order.id}
          onClick={() => onRowClick(order.id)}
          style={{
            ...gridRow,
            cursor: 'pointer',
            background: selectedId === order.id ? '#F1F5F9' : 'transparent',
            borderBottom: idx < orders.length - 1 ? '1px solid #F1F5F9' : 'none',
          }}
          onMouseEnter={(e) => { if (selectedId !== order.id) e.currentTarget.style.background = '#FAFBFC' }}
          onMouseLeave={(e) => { e.currentTarget.style.background = selectedId === order.id ? '#F1F5F9' : 'transparent' }}
        >
          <div style={tdStyle}>{fmtOrderNum(order.number)}</div>
          <div style={tdStyle}>{order.customer_name}</div>
          <div style={tdStyle}>{fmtDate(order.delivery_date)}</div>
          <div style={tdStyle}><StatusBadge label={STATUS_LABELS[order.status] ?? order.status} /></div>
          <div style={tdStyle} />
        </div>
      ))}
    </div>
  )
}

const gridRow = {
  display: 'grid',
  gridTemplateColumns: '130px 1fr 160px 150px 60px',
  alignItems: 'center',
}
const thStyle = {
  fontSize: 12, fontWeight: 500, color: '#64748B', textTransform: 'uppercase',
  letterSpacing: '0.06em', padding: '12px 16px',
  background: '#F8FAFC', borderBottom: '1px solid #E2E8F0',
}
const tdStyle = { padding: '14px 16px', fontSize: 14, color: '#0F172A' }

// ── StatusBadge ───────────────────────────────────────────────────────────────

function StatusBadge({ label }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', padding: '3px 10px',
      borderRadius: 999, fontSize: 12, fontWeight: 500,
      border: '1px solid #CBD5E1', background: '#F1F5F9', color: '#475569',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#94A3B8', marginRight: 6, flexShrink: 0 }} />
      {label}
    </span>
  )
}

// ── FilterChip ────────────────────────────────────────────────────────────────

function FilterChip({ label, value, children }) {
  return (
    <div style={{ position: 'relative' }}>
      <button style={{
        display: 'inline-flex', alignItems: 'center', gap: 8,
        height: 34, padding: '0 12px', border: '1px solid #CBD5E1', borderRadius: 8,
        background: '#FFFFFF', fontSize: 13, color: '#334155', cursor: 'pointer', fontFamily: 'inherit',
      }}>
        {label}: <strong style={{ fontWeight: 500, color: '#0F172A' }}>{value}</strong>
        <ChevronDownIcon />
      </button>
      {children}
    </div>
  )
}

// ── DrawerContent ─────────────────────────────────────────────────────────────

function DrawerContent({ order, drawerData, allTasksClosed, hasReservations, onClose, onEdit, onDelete, onToProduction, onToAssembly, onToDelivery, onManageReserve, onReleaseReserve }) {
  const { status } = order
  const isCreated    = status === 'created'
  const isProduction = status === 'production'
  const isAssembly   = status === 'assembly'
  const showActions  = !['delivery', 'completed', 'cancelled'].includes(status)

  return (
    <>
      <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid #F1F5F9', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A' }}>
            {order.customer_name?.split(',')[0] ?? 'Заказ'}
          </div>
          <StatusBadge label={STATUS_LABELS[status] ?? status} />
          <button onClick={onClose} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#64748B', display: 'flex', alignItems: 'center', width: 28, height: 28, justifyContent: 'center' }}>
            <CloseIcon />
          </button>
        </div>
        <div style={{ fontSize: 12, color: '#64748B', marginTop: 6, letterSpacing: '0.02em' }}>
          № {fmtOrderNum(order.number)} · Создан {fmtDate(order.created_at)} · Доставка {fmtDate(order.delivery_date)}
        </div>
      </div>

      {showActions && (
        <div style={{ padding: '12px 24px', display: 'flex', gap: 8, flexWrap: 'wrap', borderBottom: '1px solid #F1F5F9', flexShrink: 0, alignItems: 'center' }}>
          {isCreated && (
            <>
              <button onClick={onEdit} style={btnSecondary}><EditIcon /> Редактировать</button>
              <button onClick={onToProduction} style={btnSecondary}><ArrowRightIcon /> В производство</button>
              <button onClick={onToAssembly} style={btnPrimary}><ArrowRightIcon /> В сборку</button>
              <button onClick={onDelete} style={{ ...btnDanger, padding: '0 10px' }}><TrashIcon /></button>
            </>
          )}
          {isProduction && (
            <>
              <button onClick={onEdit} style={btnSecondary}><EditIcon /> Редактировать</button>
              <button
                onClick={allTasksClosed ? onToAssembly : undefined}
                disabled={!allTasksClosed}
                title={!allTasksClosed ? 'Дождитесь закрытия всех задач' : undefined}
                style={{ ...btnPrimary, opacity: allTasksClosed ? 1 : 0.5, cursor: allTasksClosed ? 'pointer' : 'not-allowed' }}
              >
                <ArrowRightIcon /> В сборку
              </button>
              <button onClick={onDelete} style={{ ...btnDanger, padding: '0 10px' }}><TrashIcon /></button>
            </>
          )}
          {isAssembly && (
            <>
              <button onClick={onEdit} style={btnSecondary}><EditIcon /> Редактировать</button>
              <button onClick={onToDelivery} style={btnPrimary}><ArrowRightIcon /> В доставку</button>
              <button onClick={onDelete} style={{ ...btnDanger, padding: '0 10px' }}><TrashIcon /></button>
            </>
          )}
        </div>
      )}

      {isProduction && !allTasksClosed && (
        <div style={{ padding: '8px 24px', background: '#FFFBEB', borderBottom: '1px solid #FCD34D', flexShrink: 0 }}>
          <div style={{ fontSize: 12, color: '#B45309' }}>
            Переход в «Сборку» доступен после закрытия всех задач
          </div>
        </div>
      )}

      {isAssembly && (
        <div style={{ padding: '8px 24px 10px', display: 'flex', gap: 8, borderBottom: '1px solid #F1F5F9', flexShrink: 0 }}>
          <button onClick={onManageReserve} style={btnSecondary}>
            <PackageIcon size={16} /> Зарезервировать
          </button>
          {hasReservations && (
            <button onClick={onReleaseReserve} style={btnDanger}>
              ✕ Снять резервы
            </button>
          )}
        </div>
      )}

      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 24px 24px' }}>
        <DrSection title="Заказчик">
          <DrRow label="Наименование" value={order.customer_name} />
          <DrRow label="Адрес" value={order.delivery_address} />
          {order.comment && <DrRow label="Комментарий" value={order.comment} />}
        </DrSection>

        {drawerData?.items?.length > 0 && (
          <DrSection title="Состав заказа">
            <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
              <tbody>
                {drawerData.items.map((item) => {
                  const reservations = drawerData.reservations_by_item?.[String(item.product_id)] ?? []
                  return (
                    <Fragment key={item.id}>
                      <tr>
                        <td style={{ padding: '6px 0', borderBottom: '1px solid #F8FAFC' }}>{item.product_name}</td>
                        <td style={{ padding: '6px 0', borderBottom: '1px solid #F8FAFC', textAlign: 'right' }}>
                          {itemQtyLabel(item)}
                        </td>
                      </tr>
                      {reservations.map((r) => (
                        <tr key={r.reservation_id}>
                          <td colSpan={2} style={{ paddingBottom: 4, color: '#64748B', fontSize: 11 }}>
                            └ {r.batch_label} · {r.quantity} шт зарезервировано
                          </td>
                        </tr>
                      ))}
                      {reservations.length === 0 && isProduction && (
                        <tr>
                          <td colSpan={2} style={{ paddingBottom: 4, color: '#B45309', fontSize: 11 }}>
                            └ Резерв ещё не создан
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })}
              </tbody>
            </table>
          </DrSection>
        )}

        {drawerData?.tasks?.length > 0 && (
          <DrSection title="Производственные задачи">
            {drawerData.tasks.map((task) => (
              <div key={task.task_id} style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: '10px 12px', margin: '6px 0', fontSize: 13 }}>
                <div><strong style={{ fontWeight: 500 }}>{task.product_name}</strong> · {task.quantity} шт · #{task.task_id}</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
                  <span style={{ color: '#64748B', fontSize: 12 }}>{task.executor_name} · до {fmtDate(task.deadline)}</span>
                  <StatusBadge label={task.status} />
                </div>
              </div>
            ))}
          </DrSection>
        )}

        <DrSection title="Доставка">
          <DrRow label="Курьер" value={order.delivery_user_name ?? 'не назначен'} />
          <DrRow label="Дата плановая" value={fmtDate(order.delivery_date)} />
        </DrSection>
      </div>
    </>
  )
}

function DrSection({ title, children }) {
  return (
    <div style={{ padding: '16px 0', borderBottom: '1px solid #F1F5F9' }}>
      <div style={{ fontSize: 12, fontWeight: 500, color: '#0F172A', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{title}</div>
      {children}
    </div>
  )
}
function DrRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13 }}>
      <span style={{ color: '#64748B' }}>{label}</span>
      <span style={{ color: '#0F172A', fontWeight: 500, textAlign: 'right', maxWidth: '60%' }}>{value ?? '—'}</span>
    </div>
  )
}

// ── States ────────────────────────────────────────────────────────────────────

function SkeletonTable() {
  return (
    <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden' }}>
      <div style={gridRow}>
        {['№', 'Заказчик', 'Дата доставки', 'Статус', ''].map((h, i) => <div key={i} style={thStyle}>{h}</div>)}
      </div>
      {[80, 65, 75, 60, 70].map((w, i) => (
        <div key={i} style={{ ...gridRow, borderBottom: '1px solid #F1F5F9' }}>
          <div style={tdStyle}><Skel w={70} /></div>
          <div style={tdStyle}><Skel w={`${w}%`} /></div>
          <div style={tdStyle}><Skel w={90} /></div>
          <div style={tdStyle}><Skel w={80} h={20} rounded /></div>
          <div style={tdStyle} />
        </div>
      ))}
    </div>
  )
}

function Skel({ w, h = 14, rounded = false }) {
  return (
    <div style={{
      width: typeof w === 'number' ? w : w, height: h,
      borderRadius: rounded ? 999 : 4,
      background: 'linear-gradient(90deg, #F1F5F9 0%, #E2E8F0 50%, #F1F5F9 100%)',
      backgroundSize: '200% 100%',
    }} />
  )
}

function ErrorBlock({ onRetry }) {
  return (
    <div style={{ padding: '14px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 10, display: 'flex', alignItems: 'flex-start', gap: 12 }}>
      <AlertIcon />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: '#B91C1C' }}>Не удалось загрузить заказы</div>
        <div style={{ fontSize: 13, color: '#B91C1C', marginTop: 2 }}>Проверьте соединение с сервером.</div>
      </div>
      <button onClick={onRetry} style={btnSecondary}><RefreshIcon /> Повторить</button>
    </div>
  )
}

function EmptyState({ onCreate }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '80px 40px', textAlign: 'center', color: '#64748B' }}>
      <div style={{ width: 96, height: 96, borderRadius: '50%', background: '#F1F5F9', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20, color: '#94A3B8' }}>
        <PackageIcon size={40} />
      </div>
      <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A', marginBottom: 6 }}>Заказов пока нет</div>
      <div style={{ fontSize: 14, color: '#64748B', marginBottom: 18, maxWidth: 360 }}>
        Создайте первый заказ — кнопка справа сверху.
      </div>
      <button onClick={onCreate} style={btnPrimary}><PlusIcon /> Создать первый заказ</button>
    </div>
  )
}

// ── InlineModal ───────────────────────────────────────────────────────────────

function InlineModal({ open, onClose, title, subtitle, size = 640, children, footer }) {
  useEffect(() => {
    if (!open) return
    const h = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [open, onClose])

  if (!open) return null
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(15,23,42,0.45)' }} onClick={onClose} />
      <div style={{ position: 'relative', background: '#FFF', borderRadius: 12, boxShadow: '0 20px 60px rgba(15,23,42,0.3)', width: size, maxWidth: 'calc(100vw - 32px)', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #F1F5F9', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A' }}>{title}</div>
            {subtitle && <div style={{ fontSize: 12, color: '#64748B', marginTop: 2 }}>{subtitle}</div>}
          </div>
          <button onClick={onClose} style={{ width: 30, height: 30, borderRadius: 6, border: '1px solid #E2E8F0', background: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748B', cursor: 'pointer' }}>
            <CloseIcon />
          </button>
        </div>
        <div style={{ padding: 24, overflow: 'auto', flex: 1 }}>{children}</div>
        {footer && (
          <div style={{ padding: '16px 24px', borderTop: '1px solid #F1F5F9', display: 'flex', justifyContent: 'flex-end', gap: 10, flexShrink: 0 }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Form helpers ──────────────────────────────────────────────────────────────

function MField({ label, required, opt, error, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ fontSize: 13, fontWeight: 500, color: '#334155', marginBottom: 6, display: 'block' }}>
        {label}
        {required && <span style={{ color: '#DC2626', marginLeft: 2 }}>*</span>}
        {opt && <span style={{ color: '#94A3B8', fontWeight: 400, fontSize: 12, marginLeft: 4 }}>— {opt}</span>}
      </label>
      {children}
      {error && (
        <div style={{ fontSize: 12, color: '#B91C1C', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
          <AlertIcon size={12} /> {error}
        </div>
      )}
    </div>
  )
}

const mInputStyle = {
  height: 40, border: '1px solid #CBD5E1', borderRadius: 8, padding: '0 12px',
  fontSize: 14, color: '#0F172A', background: '#FFF', width: '100%', fontFamily: 'inherit',
  outline: 'none', boxSizing: 'border-box',
}
const mInputErr = { ...mInputStyle, borderColor: '#DC2626' }
const mInputRo  = { ...mInputStyle, background: '#F8FAFC', color: '#475569' }

function MInput({ error, readOnly, ...props }) {
  return <input style={readOnly ? mInputRo : error ? mInputErr : mInputStyle} readOnly={readOnly} {...props} />
}
function MSelect({ error, children, ...props }) {
  return <select style={error ? { ...mInputStyle, ...mInputErr } : mInputStyle} {...props}>{children}</select>
}
function MTextarea({ ...props }) {
  return <textarea style={{ border: '1px solid #CBD5E1', borderRadius: 8, padding: '10px 12px', fontSize: 14, color: '#0F172A', background: '#FFF', width: '100%', fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box', resize: 'none', minHeight: 72 }} {...props} />
}

// ── ComposeTable (pieces input — matches Streamlit) ───────────────────────────

function ComposeTable({ items, setItems, products, error }) {
  const addItem    = () => setItems(prev => [...prev, { product_id: '', quantity: '' }])
  const delItem    = (idx) => setItems(prev => prev.filter((_, i) => i !== idx))
  const setField   = (idx, field, val) => setItems(prev => prev.map((it, i) => i === idx ? { ...it, [field]: val } : it))

  return (
    <div style={{ border: `1px solid ${error ? '#DC2626' : '#E2E8F0'}`, borderRadius: 8, padding: 12, background: '#F8FAFC' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 150px 32px', gap: 10, fontSize: 11, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>
        <span>Продукт</span><span>Кол-во (шт)</span><span />
      </div>
      {items.map((item, idx) => (
        <div key={idx} style={{ display: 'grid', gridTemplateColumns: '1fr 150px 32px', gap: 10, alignItems: 'center', marginBottom: 8 }}>
          <select
            value={item.product_id}
            onChange={e => setField(idx, 'product_id', e.target.value)}
            style={{ height: 36, border: '1px solid #CBD5E1', borderRadius: 6, padding: '0 8px', fontSize: 13, background: '#FFF', fontFamily: 'inherit', outline: 'none' }}
          >
            <option value="">Выберите продукт</option>
            {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <input
            type="number" min="1"
            value={item.quantity}
            onChange={e => setField(idx, 'quantity', e.target.value)}
            placeholder="0"
            style={{ height: 36, border: '1px solid #CBD5E1', borderRadius: 6, padding: '0 8px', fontSize: 13, background: '#FFF', fontFamily: 'inherit', outline: 'none', width: '100%' }}
          />
          <button type="button" onClick={() => delItem(idx)} style={{ width: 32, height: 36, border: '1px solid #E2E8F0', borderRadius: 6, background: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94A3B8', cursor: 'pointer' }}>
            <TrashIcon />
          </button>
        </div>
      ))}
      <button type="button" onClick={addItem} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, height: 32, padding: '0 12px', border: '1px solid #E2E8F0', borderRadius: 6, background: 'transparent', color: '#475569', fontSize: 13, cursor: 'pointer', fontFamily: 'inherit', marginTop: 2 }}>
        <PlusIcon /> Добавить позицию
      </button>
    </div>
  )
}

// ── CreateOrderModal (MOD-01) ─────────────────────────────────────────────────

function CreateOrderModal({ open, onClose, onCreate }) {
  const [form, setForm] = useState({ customer_id: '', delivery_address: '', delivery_date: '', delivery_user_id: '', comment: '' })
  const [items, setItems] = useState([{ product_id: '', quantity: '' }])
  const [submitted, setSubmitted] = useState(false)
  const [saving, setSaving] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const { data: customers = [] } = useQuery({ queryKey: ['customers'], queryFn: fetchCustomers, enabled: open })
  const { data: products = [] }  = useQuery({ queryKey: ['products'], queryFn: fetchProducts, enabled: open })
  const { data: allUsers = [] }  = useQuery({ queryKey: ['all-users'], queryFn: fetchAllUsers, enabled: open })
  const deliveryUsers = useMemo(() => allUsers.filter(u => u.is_active && u.roles?.includes('delivery')), [allUsers])

  useEffect(() => {
    if (open) {
      setForm({ customer_id: '', delivery_address: '', delivery_date: '', delivery_user_id: '', comment: '' })
      setItems([{ product_id: '', quantity: '' }])
      setSubmitted(false)
    }
  }, [open])

  const handleCustomerChange = (custId) => {
    const customer = customers.find(c => String(c.id) === String(custId))
    set('customer_id', custId)
    if (customer?.default_address) set('delivery_address', customer.default_address)
  }

  const validItems = items.filter(i => i.product_id && Number(i.quantity) > 0)
  const errCustomer = submitted && !form.customer_id
  const errItems    = submitted && validItems.length === 0
  const errDate     = submitted && !form.delivery_date

  const handleSave = async () => {
    setSubmitted(true)
    if (!form.customer_id || validItems.length === 0 || !form.delivery_date) return
    setSaving(true)
    try {
      await api.post('/orders', {
        customer_id:      Number(form.customer_id),
        delivery_address: form.delivery_address,
        delivery_date:    form.delivery_date,
        items:            validItems.map(i => ({ product_id: Number(i.product_id), quantity: Number(i.quantity) })),
        delivery_user_id: form.delivery_user_id ? Number(form.delivery_user_id) : null,
        comment:          form.comment || null,
      })
    } catch { /* dev mode */ }
    setSaving(false)
    onCreate()
  }

  return (
    <InlineModal open={open} onClose={onClose} title="Новый заказ" size={640}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving} style={{ ...btnPrimary, opacity: saving ? 0.7 : 1 }}>
          {saving ? 'Создание…' : 'Создать заказ'}
        </button>
      </>}
    >
      <MField label="Заказчик" required error={errCustomer ? 'Обязательное поле' : null}>
        <MSelect value={form.customer_id} onChange={e => handleCustomerChange(e.target.value)} error={errCustomer}>
          <option value="">Выберите заказчика</option>
          {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </MSelect>
      </MField>

      <MField label="Адрес доставки">
        <MInput
          value={form.delivery_address}
          onChange={e => set('delivery_address', e.target.value)}
          placeholder={form.customer_id ? 'г. Красноярск, ул. …' : 'Заполнится после выбора заказчика'}
        />
      </MField>

      <MField label="Состав заказа" required error={errItems ? 'Добавьте хотя бы одну позицию' : null}>
        <ComposeTable items={items} setItems={setItems} products={products} error={errItems} />
      </MField>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <MField label="Дата доставки" required error={errDate ? 'Обязательное поле' : null}>
          <MInput type="date" value={form.delivery_date} onChange={e => set('delivery_date', e.target.value)} error={errDate} />
        </MField>
        <MField label="Исполнитель доставки" opt="опц.">
          <MSelect value={form.delivery_user_id} onChange={e => set('delivery_user_id', e.target.value)}>
            <option value="">Не назначен</option>
            {deliveryUsers.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}
          </MSelect>
        </MField>
      </div>

      <MField label="Комментарий" opt="опц.">
        <MTextarea rows={2} value={form.comment} onChange={e => set('comment', e.target.value)} placeholder="Например: звонить за час до доставки" />
      </MField>
    </InlineModal>
  )
}

// ── EditOrderModal (MOD-02) ───────────────────────────────────────────────────

function EditOrderModal({ open, order, drawerData, onClose, onSave }) {
  const initItems = useCallback(() =>
    drawerData?.items?.map(i => ({ product_id: String(i.product_id), quantity: String(i.quantity) })) ?? [],
    [drawerData]
  )

  const [form, setForm] = useState({
    delivery_address: order.delivery_address ?? '',
    delivery_date:    order.delivery_date ?? '',
    delivery_user_id: order.delivery_user_id ? String(order.delivery_user_id) : '',
    comment:          order.comment ?? '',
  })
  const [items, setItems]       = useState(initItems)
  const [submitted, setSubmitted] = useState(false)
  const [saving, setSaving]     = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const { data: products = [] }  = useQuery({ queryKey: ['products'], queryFn: fetchProducts, enabled: open })
  const { data: allUsers = [] }  = useQuery({ queryKey: ['all-users'], queryFn: fetchAllUsers, enabled: open })
  const deliveryUsers = useMemo(() => allUsers.filter(u => u.is_active && u.roles?.includes('delivery')), [allUsers])

  useEffect(() => {
    if (open) {
      setForm({
        delivery_address: order.delivery_address ?? '',
        delivery_date:    order.delivery_date ?? '',
        delivery_user_id: order.delivery_user_id ? String(order.delivery_user_id) : '',
        comment:          order.comment ?? '',
      })
      setItems(initItems())
      setSubmitted(false)
    }
  }, [open, order, initItems])

  const validItems = items.filter(i => i.product_id && Number(i.quantity) > 0)
  const errItems   = submitted && validItems.length === 0
  const errDate    = submitted && !form.delivery_date

  const handleSave = async () => {
    setSubmitted(true)
    if (validItems.length === 0 || !form.delivery_date) return
    setSaving(true)
    try {
      await api.put(`/orders/${order.id}`, {
        delivery_address: form.delivery_address,
        delivery_date:    form.delivery_date,
        items:            validItems.map(i => ({ product_id: Number(i.product_id), quantity: Number(i.quantity) })),
        delivery_user_id: form.delivery_user_id ? Number(form.delivery_user_id) : null,
        comment:          form.comment || null,
      })
    } catch { /* dev mode */ }
    setSaving(false)
    onSave()
  }

  return (
    <InlineModal open={open} onClose={onClose} title={`Редактирование заказа № ${fmtOrderNum(order.number)}`} size={640}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving} style={{ ...btnPrimary, opacity: saving ? 0.7 : 1 }}>
          {saving ? 'Сохранение…' : 'Сохранить изменения'}
        </button>
      </>}
    >
      <MField label="Заказчик" opt="нельзя изменить после создания">
        <MInput value={order.customer_name} readOnly />
      </MField>

      <MField label="Адрес доставки">
        <MInput value={form.delivery_address} onChange={e => set('delivery_address', e.target.value)} />
      </MField>

      <MField label="Состав заказа" required error={errItems ? 'Добавьте хотя бы одну позицию' : null}>
        <ComposeTable items={items} setItems={setItems} products={products} error={errItems} />
      </MField>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <MField label="Дата доставки" required error={errDate ? 'Обязательное поле' : null}>
          <MInput type="date" value={form.delivery_date} onChange={e => set('delivery_date', e.target.value)} error={errDate} />
        </MField>
        <MField label="Исполнитель доставки" opt="опц.">
          <MSelect value={form.delivery_user_id} onChange={e => set('delivery_user_id', e.target.value)}>
            <option value="">Не назначен</option>
            {deliveryUsers.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}
          </MSelect>
        </MField>
      </div>

      <MField label="Комментарий" opt="опц.">
        <MTextarea rows={2} value={form.comment} onChange={e => set('comment', e.target.value)} />
      </MField>
    </InlineModal>
  )
}

// ── ToProductionModal ─────────────────────────────────────────────────────────

function ToProductionModal({ open, onClose, order, items, productionUsers, onConfirm }) {
  const today = new Date().toISOString().slice(0, 10)
  const [form, setForm] = useState({ executor_id: '', start_date: today, deadline: '', comment: '' })
  const [saving, setSaving] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => {
    if (open) {
      setForm({ executor_id: '', start_date: today, deadline: order?.delivery_date ?? '', comment: '' })
      setSubmitted(false)
    }
  }, [open, order])

  const errExecutor = submitted && !form.executor_id
  const errDeadline = submitted && !form.deadline

  const handleSave = async () => {
    setSubmitted(true)
    if (!form.executor_id || !form.deadline) return
    setSaving(true)
    try {
      for (const item of items) {
        await api.post('/tasks', {
          product_id:  item.product_id,
          quantity:    item.quantity,
          executor_id: Number(form.executor_id),
          start_date:  form.start_date,
          deadline:    form.deadline,
          task_type:   'order_task',
          order_id:    order.id,
          comment:     form.comment || null,
        })
      }
      await api.patch(`/orders/${order.id}/status`, { new_status: 'production' })
    } catch { /* ignore */ }
    setSaving(false)
    onConfirm()
  }

  if (!order) return null
  return (
    <InlineModal
      open={open} onClose={onClose}
      title="Отправить в производство"
      subtitle={`Заказ № ${fmtOrderNum(order.number)} · ${items.length} позиций`}
      size={560}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving} style={{ ...btnPrimary, opacity: saving ? 0.7 : 1 }}>
          {saving ? 'Создаём задачи…' : 'Создать задачи и перевести'}
        </button>
      </>}
    >
      <div style={{ marginBottom: 16, background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: '10px 12px' }}>
        <div style={{ fontSize: 12, fontWeight: 500, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
          Будут созданы задачи для позиций
        </div>
        {items.map(item => (
          <div key={item.id} style={{ fontSize: 13, color: '#0F172A', padding: '3px 0' }}>
            • <strong style={{ fontWeight: 500 }}>{item.product_name}</strong> — {itemQtyLabel(item)}
          </div>
        ))}
      </div>

      <MField label="Исполнитель" required error={errExecutor ? 'Выберите исполнителя' : null}>
        <MSelect value={form.executor_id} onChange={e => set('executor_id', e.target.value)} error={errExecutor}>
          <option value="">Выберите исполнителя</option>
          {productionUsers.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}
        </MSelect>
      </MField>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <MField label="Дата начала" required>
          <MInput type="date" value={form.start_date} onChange={e => set('start_date', e.target.value)} />
        </MField>
        <MField label="Дедлайн" required error={errDeadline ? 'Обязательное поле' : null}>
          <MInput type="date" value={form.deadline} onChange={e => set('deadline', e.target.value)} error={errDeadline} />
        </MField>
      </div>

      <MField label="Комментарий" opt="опц.">
        <MTextarea rows={2} value={form.comment} onChange={e => set('comment', e.target.value)} placeholder="Особые указания для исполнителя" />
      </MField>
    </InlineModal>
  )
}

// ── ReservationModal ──────────────────────────────────────────────────────────

function ReservationModal({ open, onClose, order, items, drawerData, mode, onConfirm }) {
  const qc = useQueryClient()
  const [stockByProduct, setStockByProduct] = useState({})
  const [reserveQty, setReserveQty]         = useState({})
  const [reserving, setReserving]           = useState(false)
  const [settingStatus, setSettingStatus]   = useState(false)
  const [fetchTick, setFetchTick]           = useState(0)

  useEffect(() => {
    if (!open || items.length === 0) return
    let cancelled = false
    const load = async () => {
      const results = {}
      await Promise.all(items.map(async (item) => {
        results[item.product_id] = await fetchProductStock(item.product_id)
      }))
      if (!cancelled) setStockByProduct(results)
    }
    load()
    return () => { cancelled = true }
  }, [open, items.length, fetchTick])

  useEffect(() => {
    if (open) setReserveQty({})
  }, [open])

  const handleReserve = async (stockId, qty) => {
    if (!qty || qty <= 0) return
    setReserving(true)
    try {
      await api.post(`/orders/${order.id}/reservations`, { stock_id: stockId, quantity: qty })
      qc.invalidateQueries({ queryKey: ['order-drawer', order.id] })
      setFetchTick(n => n + 1)
      setReserveQty(prev => ({ ...prev, [stockId]: 0 }))
    } catch { /* ignore */ }
    setReserving(false)
  }

  const allCovered = items.every(item => {
    const resList = drawerData?.reservations_by_item?.[String(item.product_id)] ?? []
    const already = resList.reduce((sum, r) => sum + Number(r.quantity), 0)
    return already >= item.quantity
  })

  const handleSetAssembly = async () => {
    setSettingStatus(true)
    try {
      await api.patch(`/orders/${order.id}/status`, { new_status: 'assembly' })
    } catch { /* ignore */ }
    setSettingStatus(false)
    onConfirm()
  }

  const title     = mode === 'to_assembly' ? 'Резервирование → Сборка' : 'Управление резервами'
  const subtitle  = order ? `Заказ № ${fmtOrderNum(order.number)}` : ''

  return (
    <InlineModal open={open} onClose={onClose} title={title} subtitle={subtitle} size={700}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Закрыть</button>
        {mode === 'to_assembly' && (
          <button
            onClick={handleSetAssembly}
            disabled={!allCovered || settingStatus}
            style={{ ...btnPrimary, opacity: allCovered && !settingStatus ? 1 : 0.5, cursor: allCovered ? 'pointer' : 'not-allowed' }}
          >
            <ArrowRightIcon /> {settingStatus ? 'Переводим…' : 'Готово — перевести в Сборку'}
          </button>
        )}
      </>}
    >
      {!allCovered && mode === 'to_assembly' && (
        <div style={{ padding: '8px 12px', background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 8, fontSize: 13, color: '#1D4ED8', marginBottom: 16 }}>
          Зарезервируйте все позиции, чтобы перевести заказ в «Сборку».
        </div>
      )}

      {items.map(item => {
        const resList  = drawerData?.reservations_by_item?.[String(item.product_id)] ?? []
        const already  = resList.reduce((sum, r) => sum + Number(r.quantity), 0)
        const needed   = item.quantity - already
        const stocks   = stockByProduct[item.product_id] ?? []
        const avail    = stocks.filter(s => s.quantity - s.reserved > 0)

        return (
          <div key={item.product_id} style={{ marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #F1F5F9' }}>
            <div style={{ fontSize: 14, fontWeight: 500, color: '#0F172A', marginBottom: 4 }}>
              {item.product_name}
            </div>
            <div style={{ fontSize: 12, color: '#64748B', marginBottom: 10 }}>
              Нужно {item.quantity} шт · Зарезервировано {already} шт
              {needed > 0 && <span style={{ color: '#B45309' }}> · Осталось {needed} шт</span>}
            </div>

            {needed <= 0 ? (
              <div style={{ color: '#047857', fontSize: 13, fontWeight: 500 }}>✓ Полностью зарезервировано</div>
            ) : avail.length === 0 ? (
              <div style={{ color: '#B45309', fontSize: 13 }}>Нет доступных партий на складе</div>
            ) : (
              avail.map(s => {
                const free  = s.quantity - s.reserved
                const label = `П-${s.batch_year}-${String(s.batch_number).padStart(3, '0')}`
                const qtyKey = s.id
                return (
                  <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, background: '#F8FAFC', borderRadius: 6, padding: '6px 10px' }}>
                    <div style={{ flex: 1, fontSize: 12, color: '#475569' }}>
                      {label} · {free} шт свободно · до {fmtDate(s.expiry_date)}
                    </div>
                    <input
                      type="number" min="0" max={Math.min(free, needed)}
                      value={reserveQty[qtyKey] ?? 0}
                      onChange={e => setReserveQty(prev => ({ ...prev, [qtyKey]: Number(e.target.value) }))}
                      style={{ height: 32, width: 80, border: '1px solid #CBD5E1', borderRadius: 6, padding: '0 8px', fontSize: 13, fontFamily: 'inherit', outline: 'none', textAlign: 'center' }}
                    />
                    <span style={{ fontSize: 12, color: '#64748B' }}>шт</span>
                    <button
                      onClick={() => handleReserve(s.id, reserveQty[qtyKey] ?? 0)}
                      disabled={reserving || !(reserveQty[qtyKey] > 0)}
                      style={{ height: 32, padding: '0 12px', border: '1px solid #CBD5E1', borderRadius: 6, background: '#FFF', fontSize: 13, cursor: 'pointer', fontFamily: 'inherit', opacity: (reserveQty[qtyKey] > 0 && !reserving) ? 1 : 0.5 }}
                    >
                      ✓ Зарезервировать
                    </button>
                  </div>
                )
              })
            )}

            {resList.length > 0 && (
              <div style={{ marginTop: 6 }}>
                {resList.map(r => (
                  <div key={r.reservation_id} style={{ fontSize: 12, color: '#64748B', padding: '2px 0' }}>
                    └ {r.batch_label} · {r.quantity} шт зарезервировано
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </InlineModal>
  )
}

// ── ToDeliveryModal ───────────────────────────────────────────────────────────

function ToDeliveryModal({ open, onClose, order, deliveryUsers, onConfirm }) {
  const [executorId, setExecutorId] = useState('')
  const [plannedDate, setPlannedDate] = useState('')
  const [saving, setSaving] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    if (open && order) {
      const preselect = order.delivery_user_id ? String(order.delivery_user_id) : ''
      setExecutorId(preselect || (deliveryUsers[0] ? String(deliveryUsers[0].id) : ''))
      setPlannedDate(order.delivery_date ?? '')
      setSubmitted(false)
    }
  }, [open, order, deliveryUsers])

  const errExecutor = submitted && !executorId
  const errDate     = submitted && !plannedDate

  const handleSave = async () => {
    setSubmitted(true)
    if (!executorId || !plannedDate) return
    setSaving(true)
    try {
      await api.post('/deliveries', {
        order_id:     order.id,
        executor_id:  Number(executorId),
        planned_date: plannedDate,
      })
      await api.patch(`/orders/${order.id}/status`, { new_status: 'delivery' })
    } catch { /* ignore */ }
    setSaving(false)
    onConfirm()
  }

  if (!order) return null
  return (
    <InlineModal
      open={open} onClose={onClose}
      title="Отправить в доставку"
      subtitle={`Заказ № ${fmtOrderNum(order.number)}`}
      size={480}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving} style={{ ...btnPrimary, opacity: saving ? 0.7 : 1 }}>
          {saving ? 'Создаём доставку…' : 'Создать доставку и перевести'}
        </button>
      </>}
    >
      <MField label="Курьер" required error={errExecutor ? 'Выберите курьера' : null}>
        <MSelect value={executorId} onChange={e => setExecutorId(e.target.value)} error={errExecutor}>
          <option value="">Выберите курьера</option>
          {deliveryUsers.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}
        </MSelect>
      </MField>

      <MField label="Плановая дата доставки" required error={errDate ? 'Обязательное поле' : null}>
        <MInput type="date" value={plannedDate} onChange={e => setPlannedDate(e.target.value)} error={errDate} />
      </MField>
    </InlineModal>
  )
}

// ── ReleaseReservationsModal ──────────────────────────────────────────────────

function ReleaseReservationsModal({ open, onClose, orderId, orderNum, onConfirm }) {
  const [deleting, setDeleting] = useState(false)

  const handleConfirm = async () => {
    setDeleting(true)
    try { await api.delete(`/orders/${orderId}/reservations`) } catch { /* ignore */ }
    setDeleting(false)
    onConfirm()
  }

  return (
    <InlineModal open={open} onClose={onClose} title="Снять все резервы" size={440}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleConfirm} disabled={deleting} style={{ ...btnDanger, opacity: deleting ? 0.7 : 1 }}>
          {deleting ? 'Снимаем…' : 'Снять все резервы'}
        </button>
      </>}
    >
      <div style={{ padding: '8px 0 16px', textAlign: 'center' }}>
        <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#FEF2F2', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', color: '#B91C1C', fontSize: 24 }}>
          ✕
        </div>
        <div style={{ fontSize: 15, fontWeight: 500, color: '#0F172A', marginBottom: 8 }}>
          Снять все резервы с заказа № {orderNum}?
        </div>
        <div style={{ fontSize: 13, color: '#64748B' }}>
          Все зарезервированные партии будут освобождены.
        </div>
      </div>
    </InlineModal>
  )
}

// ── Button styles ─────────────────────────────────────────────────────────────

const btnPrimary = {
  display: 'inline-flex', alignItems: 'center', gap: 8, height: 38, padding: '0 16px',
  borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: 'pointer',
  background: '#1E293B', color: '#FFFFFF', border: '1px solid transparent', fontFamily: 'inherit',
}
const btnSecondary = {
  display: 'inline-flex', alignItems: 'center', gap: 8, height: 38, padding: '0 16px',
  borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: 'pointer',
  background: '#FFFFFF', color: '#1E293B', border: '1px solid #CBD5E1', fontFamily: 'inherit',
}
const btnDanger = {
  display: 'inline-flex', alignItems: 'center', gap: 8, height: 38, padding: '0 16px',
  borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: 'pointer',
  background: '#FFFFFF', color: '#B91C1C', border: '1px solid #FCA5A5', fontFamily: 'inherit',
}
const dateInputStyle = {
  height: 32, border: '1px solid #CBD5E1', borderRadius: 6, padding: '0 8px',
  fontSize: 13, color: '#0F172A', fontFamily: 'inherit', outline: 'none',
}

// ── Icons ─────────────────────────────────────────────────────────────────────

function PlusIcon()      { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><line x1="12" y1="5" x2="12" y2="19"/></svg> }
function ChevronDownIcon(){ return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6"/></svg> }
function CloseIcon()     { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg> }
function EditIcon()      { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"/><path d="M18.5 2.5a2.1 2.1 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg> }
function TrashIcon()     { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg> }
function ArrowRightIcon(){ return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg> }
function AlertIcon({ size = 20 }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#B91C1C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="13"/><circle cx="12" cy="16" r="0.5"/></svg> }
function RefreshIcon()   { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><polyline points="21 3 21 8 16 8"/></svg> }
function PackageIcon({ size = 18 }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3 L20 7 L20 17 L12 21 L4 17 L4 7 Z"/><path d="M12 12 L20 7"/><path d="M12 12 L4 7"/><path d="M12 12 L12 21"/></svg> }
