import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useAuth } from '../contexts/AuthContext'

// ─── Status config ────────────────────────────────────────────────────────────

const STATUS_LABEL = {
  pending:    'Ожидает сборки',
  picked_up:  'Собрана',
  in_transit: 'В пути',
  completed:  'Доставлена',
  cancelled:  'Отменена',
}

const STATUS_STYLE = {
  pending:    { bg: '#F1F5F9', border: '#CBD5E1', color: '#475569', dot: '#94A3B8' },
  picked_up:  { bg: '#F5F3FF', border: '#C4B5FD', color: '#6D28D9', dot: '#7C3AED' },
  in_transit: { bg: '#EFF6FF', border: '#93C5FD', color: '#1E40AF', dot: '#2563EB' },
  completed:  { bg: '#ECFDF5', border: '#86EFAC', color: '#047857', dot: '#059669' },
  cancelled:  { bg: '#F8FAFC', border: '#CBD5E1', color: '#94A3B8', dot: '#CBD5E1' },
}

function StatusBadge({ status }) {
  const s = STATUS_STYLE[status] ?? STATUS_STYLE.cancelled
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '3px 10px', borderRadius: 999, fontSize: 12, fontWeight: 500,
      background: s.bg, border: `1px solid ${s.border}`, color: s.color,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.dot, flexShrink: 0 }} />
      {STATUS_LABEL[status] ?? status}
    </span>
  )
}

// ─── Shared UI ────────────────────────────────────────────────────────────────

const controlStyle = {
  width: '100%', height: 40, padding: '0 12px',
  border: '1px solid #CBD5E1', borderRadius: 8,
  fontSize: 14, outline: 'none', boxSizing: 'border-box',
  fontFamily: 'inherit', color: '#0F172A', background: '#FFF',
}

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 500, color: '#334155', marginBottom: 6 }}>{label}</div>
      {children}
    </div>
  )
}

function FilterChip({ label, children }) {
  return (
    <div style={{
      position: 'relative', display: 'inline-flex', alignItems: 'center', gap: 6,
      height: 34, padding: '0 12px', border: '1px solid #CBD5E1', borderRadius: 8,
      background: '#FFF', fontSize: 13, cursor: 'pointer', userSelect: 'none',
      color: '#334155', flexShrink: 0,
    }}>
      <span>{label}</span>
      <span style={{ fontSize: 10, opacity: 0.5 }}>▼</span>
      {children}
    </div>
  )
}

// ─── Modals ───────────────────────────────────────────────────────────────────

function Modal({ title, onClose, footer, children }) {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}>
      <div style={{ background: '#FFF', borderRadius: 12, width: 520, maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 60px rgba(15,23,42,0.3)' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #F1F5F9', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A' }}>{title}</div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: '#94A3B8', lineHeight: 1, padding: 0 }}>×</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          {children}
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #F1F5F9', display: 'flex', justifyContent: 'flex-end', gap: 10, flexShrink: 0 }}>
          {footer}
        </div>
      </div>
    </div>
  )
}

function CreateDeliveryModal({ orders, users, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ order_id: '', executor_id: '', planned_date: '' })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const deliveryUsers = users.filter(u => u.roles?.includes('delivery') && u.is_active)
  const mut = useMutation({
    mutationFn: () => api.post('/deliveries', {
      order_id: Number(form.order_id),
      executor_id: Number(form.executor_id),
      planned_date: form.planned_date,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['deliveries'] }); onClose() },
  })
  const valid = form.order_id && form.executor_id && form.planned_date

  return (
    <Modal
      title="Новая доставка"
      onClose={onClose}
      footer={<>
        <button onClick={onClose} style={{ height: 38, padding: '0 18px', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, color: '#334155' }}>Отмена</button>
        <button
          onClick={() => valid && mut.mutate()}
          disabled={!valid || mut.isPending}
          style={{ height: 38, padding: '0 18px', border: 'none', borderRadius: 8, background: '#1E293B', color: '#FFF', cursor: valid ? 'pointer' : 'not-allowed', fontSize: 13, fontWeight: 500, opacity: !valid || mut.isPending ? 0.5 : 1 }}
        >
          {mut.isPending ? 'Создание...' : 'Создать'}
        </button>
      </>}
    >
      <Field label="Заказ *">
        {orders.length > 0 ? (
          <select style={{ ...controlStyle, cursor: 'pointer' }} value={form.order_id} onChange={set('order_id')}>
            <option value="">— выберите заказ —</option>
            {orders.filter(o => o.status === 'assembly' || o.status === 'delivery').map(o => (
              <option key={o.id} value={o.id}>#{o.number} — {o.customer_name}</option>
            ))}
          </select>
        ) : (
          <input style={controlStyle} type="number" placeholder="ID заказа" value={form.order_id} onChange={set('order_id')} />
        )}
      </Field>
      <Field label="Исполнитель *">
        <select style={{ ...controlStyle, cursor: 'pointer' }} value={form.executor_id} onChange={set('executor_id')}>
          <option value="">— выберите исполнителя —</option>
          {deliveryUsers.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}
        </select>
      </Field>
      <Field label="Плановая дата доставки *">
        <input style={controlStyle} type="date" value={form.planned_date} onChange={set('planned_date')} />
      </Field>
      {mut.error && <div style={{ color: '#DC2626', fontSize: 12, marginTop: 4 }}>{mut.error?.response?.data?.detail ?? 'Ошибка'}</div>}
    </Modal>
  )
}

function CancelModal({ delivery, onClose }) {
  const qc = useQueryClient()
  const [reason, setReason] = useState('')
  const mut = useMutation({
    mutationFn: () => api.post(`/deliveries/${delivery.id}/cancel`, { reason }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['deliveries'] }); onClose() },
  })
  const valid = reason.trim().length > 0

  return (
    <Modal
      title="Отмена доставки"
      onClose={onClose}
      footer={<>
        <button onClick={onClose} style={{ height: 38, padding: '0 18px', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, color: '#334155' }}>Назад</button>
        <button
          onClick={() => valid && mut.mutate()}
          disabled={!valid || mut.isPending}
          style={{ height: 38, padding: '0 18px', border: 'none', borderRadius: 8, background: '#DC2626', color: '#FFF', cursor: valid ? 'pointer' : 'not-allowed', fontSize: 13, fontWeight: 500, opacity: !valid || mut.isPending ? 0.5 : 1 }}
        >
          {mut.isPending ? 'Отмена...' : 'Отменить доставку'}
        </button>
      </>}
    >
      <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, padding: '12px 14px', marginBottom: 16, fontSize: 13, color: '#B91C1C' }}>
        Доставка #{delivery.id} будет отменена. Это действие необратимо.
      </div>
      <Field label="Причина отмены *">
        <textarea
          style={{ ...controlStyle, height: 'auto', padding: '10px 12px', resize: 'vertical', minHeight: 80 }}
          placeholder="Укажите причину отмены..."
          value={reason}
          onChange={e => setReason(e.target.value)}
        />
      </Field>
      {mut.error && <div style={{ color: '#DC2626', fontSize: 12 }}>{mut.error?.response?.data?.detail ?? 'Ошибка'}</div>}
    </Modal>
  )
}

// ─── Drawer ───────────────────────────────────────────────────────────────────

function DrSection({ title, children }) {
  return (
    <div style={{ padding: '14px 0', borderBottom: '1px solid #F1F5F9' }}>
      {title && <div style={{ fontSize: 11, fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>{title}</div>}
      {children}
    </div>
  )
}

function DrRow({ label, children }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8, fontSize: 13 }}>
      <span style={{ color: '#64748B', flexShrink: 0, marginRight: 12 }}>{label}</span>
      <span style={{ color: '#0F172A', fontWeight: 500, textAlign: 'right' }}>{children ?? '—'}</span>
    </div>
  )
}

function Drawer({ delivery, orderMap, userMap, onClose, onCancel, isDirector }) {
  const qc = useQueryClient()
  const order = orderMap[delivery.order_id]
  const executor = userMap[delivery.executor_id]

  const actionMut = useMutation({
    mutationFn: (endpoint) => api.post(`/deliveries/${delivery.id}/${endpoint}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deliveries'] }),
  })

  const canActOn = ['pending', 'picked_up', 'in_transit'].includes(delivery.status)

  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 100 }} />
      <div style={{
        position: 'absolute', top: 0, right: 0, bottom: 0, width: 480,
        background: '#FFF', borderLeft: '1px solid #E2E8F0',
        zIndex: 101, display: 'flex', flexDirection: 'column',
        boxShadow: '-4px 0 24px rgba(0,0,0,0.06)',
      }}>
        {/* Head */}
        <div style={{ padding: '18px 24px 14px', borderBottom: '1px solid #F1F5F9', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A' }}>Доставка #{delivery.id}</div>
              {order && <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 3 }}>Заказ #{order.number} · {order.customer_name}</div>}
            </div>
            <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: '#94A3B8', lineHeight: 1, padding: 0, marginTop: 2 }}>×</button>
          </div>
          <div style={{ marginTop: 10 }}><StatusBadge status={delivery.status} /></div>
        </div>

        {/* Actions bar */}
        {canActOn && (
          <div style={{ padding: '12px 24px', borderBottom: '1px solid #F1F5F9', display: 'flex', gap: 8, flexShrink: 0, flexWrap: 'wrap' }}>
            {delivery.status === 'pending' && (
              <button
                onClick={() => actionMut.mutate('pick-up')}
                disabled={actionMut.isPending}
                style={{ height: 34, padding: '0 14px', border: 'none', borderRadius: 8, background: '#047857', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500, opacity: actionMut.isPending ? 0.6 : 1 }}
              >
                Забрать (сборка готова)
              </button>
            )}
            {delivery.status === 'picked_up' && (
              <button
                onClick={() => actionMut.mutate('start')}
                disabled={actionMut.isPending}
                style={{ height: 34, padding: '0 14px', border: 'none', borderRadius: 8, background: '#2563EB', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500, opacity: actionMut.isPending ? 0.6 : 1 }}
              >
                Выехать (в пути)
              </button>
            )}
            {delivery.status === 'in_transit' && (
              <button
                onClick={() => actionMut.mutate('complete')}
                disabled={actionMut.isPending}
                style={{ height: 34, padding: '0 14px', border: 'none', borderRadius: 8, background: '#047857', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500, opacity: actionMut.isPending ? 0.6 : 1 }}
              >
                ✓ Доставлено
              </button>
            )}
            <button
              onClick={onCancel}
              style={{ height: 34, padding: '0 14px', border: '1px solid #FCA5A5', borderRadius: 8, background: '#FFF', color: '#B91C1C', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}
            >
              Отменить
            </button>
            {actionMut.isError && (
              <div style={{ width: '100%', color: '#DC2626', fontSize: 12 }}>{actionMut.error?.response?.data?.detail ?? 'Ошибка'}</div>
            )}
          </div>
        )}

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px' }}>
          <DrSection title="Детали доставки">
            <DrRow label="Исполнитель">{executor?.full_name ?? `ID ${delivery.executor_id}`}</DrRow>
            <DrRow label="Плановая дата">{delivery.planned_date}</DrRow>
            {delivery.started_at && <DrRow label="Выехал">{new Date(delivery.started_at).toLocaleString('ru')}</DrRow>}
            {delivery.completed_at && <DrRow label="Доставлено">{new Date(delivery.completed_at).toLocaleString('ru')}</DrRow>}
            {delivery.cancellation_reason && <DrRow label="Причина отмены">{delivery.cancellation_reason}</DrRow>}
          </DrSection>

          {order && (
            <DrSection title="Заказ">
              <DrRow label="Номер">#{order.number}</DrRow>
              <DrRow label="Клиент">{order.customer_name}</DrRow>
              {order.delivery_address && <DrRow label="Адрес">{order.delivery_address}</DrRow>}
              {order.delivery_date && <DrRow label="Дата доставки">{order.delivery_date}</DrRow>}
              <DrRow label="Статус заказа">{order.status}</DrRow>
            </DrSection>
          )}
        </div>
      </div>
    </>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const COL = '90px 80px 1fr 1.6fr 130px 140px'
const ALL_STATUSES = ['pending', 'picked_up', 'in_transit', 'completed', 'cancelled']

function fmtDate(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return isNaN(d) ? iso : d.toLocaleDateString('ru', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function fmtTime(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return isNaN(d) ? '' : d.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })
}

export default function Deliveries() {
  const { hasRole } = useAuth()
  const isDirector = hasRole('director')

  const { data: deliveries = [], isLoading } = useQuery({
    queryKey: ['deliveries'],
    queryFn: () => api.get('/deliveries').then(r => r.data),
  })
  const { data: orders = [] } = useQuery({
    queryKey: ['orders-for-delivery'],
    queryFn: () => api.get('/orders').then(r => r.data).catch(() => []),
  })
  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/users').then(r => r.data).catch(() => []),
  })

  const orderMap = useMemo(() => Object.fromEntries(orders.map(o => [o.id, o])), [orders])
  const userMap  = useMemo(() => Object.fromEntries(users.map(u => [u.id, u])), [users])

  const [statusFilter, setStatusFilter]     = useState('all')
  const [executorFilter, setExecutorFilter] = useState('all')
  const [search, setSearch]                 = useState('')
  const [selectedId, setSelectedId]         = useState(null)
  const [modal, setModal]                   = useState(null)

  const deliveryUsers = useMemo(() => users.filter(u => u.roles?.includes('delivery')), [users])

  const filtered = useMemo(() => deliveries
    .filter(d => statusFilter === 'all' || d.status === statusFilter)
    .filter(d => executorFilter === 'all' || String(d.executor_id) === executorFilter)
    .filter(d => {
      if (!search) return true
      const s = search.toLowerCase()
      const o = orderMap[d.order_id]
      return (
        String(d.id).includes(s) ||
        (o?.customer_name ?? '').toLowerCase().includes(s) ||
        (o?.delivery_address ?? '').toLowerCase().includes(s) ||
        (userMap[d.executor_id]?.full_name ?? '').toLowerCase().includes(s)
      )
    }),
    [deliveries, statusFilter, executorFilter, search, orderMap, userMap])

  const selected = deliveries.find(d => d.id === selectedId) ?? null
  const hasFilters = search || statusFilter !== 'all' || executorFilter !== 'all'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative', overflow: 'hidden' }}>
      {/* Page header */}
      <div style={{ padding: '24px 32px 0', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 500, color: '#0F172A' }}>Доставки</h1>
          {isDirector && (
            <button
              onClick={() => setModal('create')}
              style={{ height: 38, padding: '0 18px', border: 'none', borderRadius: 8, background: '#1E293B', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}
            >
              + Новая доставка
            </button>
          )}
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            placeholder="Поиск по клиенту, адресу, исполнителю..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ height: 34, padding: '0 12px', border: '1px solid #E2E8F0', borderRadius: 8, fontSize: 13, outline: 'none', width: 300, fontFamily: 'inherit', color: '#0F172A', boxSizing: 'border-box' }}
          />
          <FilterChip label={`Статус: ${statusFilter === 'all' ? 'Все' : STATUS_LABEL[statusFilter]}`}>
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}>
              <option value="all">Все</option>
              {ALL_STATUSES.map(s => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
            </select>
          </FilterChip>
          {deliveryUsers.length > 0 && (
            <FilterChip label={`Курьер: ${executorFilter === 'all' ? 'Все' : (userMap[executorFilter]?.full_name ?? executorFilter)}`}>
              <select value={executorFilter} onChange={e => setExecutorFilter(e.target.value)} style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}>
                <option value="all">Все</option>
                {deliveryUsers.map(u => <option key={u.id} value={String(u.id)}>{u.full_name}</option>)}
              </select>
            </FilterChip>
          )}
          {hasFilters && (
            <button onClick={() => { setSearch(''); setStatusFilter('all'); setExecutorFilter('all') }} style={{ height: 34, padding: '0 12px', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', fontSize: 13, cursor: 'pointer', color: '#64748B' }}>
              Сбросить
            </button>
          )}
        </div>
      </div>

      {/* Table area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 32px 28px' }}>
        <div style={{ background: '#FFF', borderRadius: 10, border: '1px solid #E2E8F0', overflow: 'hidden' }}>
          {/* Header */}
          <div style={{ display: 'grid', gridTemplateColumns: COL, padding: '12px 16px', background: '#F8FAFC', borderBottom: '1px solid #E2E8F0', fontSize: 12, fontWeight: 500, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.06em', gap: 8 }}>
            <span>Дата</span>
            <span>Время</span>
            <span>Клиент</span>
            <span>Адрес</span>
            <span>Курьер</span>
            <span>Статус</span>
          </div>

          {isLoading && (
            <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8', fontSize: 13 }}>Загрузка...</div>
          )}

          {!isLoading && filtered.length === 0 && (
            <div style={{ padding: '48px 24px', textAlign: 'center' }}>
              <div style={{ fontSize: 13, color: '#94A3B8' }}>{hasFilters ? 'Ничего не найдено' : 'Нет доставок'}</div>
            </div>
          )}

          {filtered.map(d => {
            const order    = orderMap[d.order_id]
            const executor = userMap[d.executor_id]
            const isSelected   = d.id === selectedId
            const isInTransit  = d.status === 'in_transit'

            const dateStr = fmtDate(d.planned_date ?? d.created_at)
            const timeStr = fmtTime(d.started_at)

            return (
              <div
                key={d.id}
                onClick={() => setSelectedId(isSelected ? null : d.id)}
                style={{
                  display: 'grid', gridTemplateColumns: COL,
                  padding: '14px 16px', borderBottom: '1px solid #F1F5F9',
                  cursor: 'pointer', alignItems: 'center', fontSize: 14, gap: 8,
                  color: '#0F172A',
                  background: isSelected ? '#F0F9FF' : '#FFF',
                  boxShadow: isInTransit && !isSelected ? 'inset 4px 0 0 0 #2563EB' : isSelected ? 'inset 4px 0 0 0 #0EA5E9' : 'none',
                  transition: 'background 0.1s',
                }}
              >
                <span style={{ color: '#64748B', fontSize: 13 }}>{dateStr ?? `#${d.id}`}</span>
                <span style={{ color: '#94A3B8', fontSize: 13 }}>{timeStr || '—'}</span>
                <div>
                  <div style={{ fontWeight: 500 }}>{order?.customer_name ?? `Заказ #${d.order_id}`}</div>
                  <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 2 }}>#{d.id}</div>
                </div>
                <span style={{ color: '#64748B', fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {order?.delivery_address ?? '—'}
                </span>
                <span style={{ color: '#64748B', fontSize: 13 }}>{executor?.full_name ?? `ID ${d.executor_id}`}</span>
                <span><StatusBadge status={d.status} /></span>
              </div>
            )
          })}
        </div>
      </div>

      {selected && (
        <Drawer
          delivery={selected}
          orderMap={orderMap}
          userMap={userMap}
          isDirector={isDirector}
          onClose={() => setSelectedId(null)}
          onCancel={() => setModal('cancel')}
        />
      )}

      {modal === 'create' && <CreateDeliveryModal orders={orders} users={users} onClose={() => setModal(null)} />}
      {modal === 'cancel' && selected && (
        <CancelModal delivery={selected} onClose={() => { setModal(null); setSelectedId(null) }} />
      )}
    </div>
  )
}
