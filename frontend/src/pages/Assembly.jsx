import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'

// ─── Shared UI ────────────────────────────────────────────────────────────────

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

// ─── Drawer ───────────────────────────────────────────────────────────────────

function Drawer({ delivery, order, userMap, onClose }) {
  const qc = useQueryClient()

  // Simulated checklist from order items (we use delivery items if available)
  const [checked, setChecked] = useState({})

  const items = useMemo(() => {
    if (order?.items && order.items.length > 0) return order.items
    return []
  }, [order])

  const totalItems  = items.length
  const checkedCount = Object.values(checked).filter(Boolean).length
  const allChecked   = totalItems > 0 && checkedCount === totalItems
  const progress     = totalItems > 0 ? Math.round((checkedCount / totalItems) * 100) : 0

  const pickUpMut = useMutation({
    mutationFn: () => api.post(`/deliveries/${delivery.id}/pick-up`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assembly-deliveries'] }); onClose() },
  })

  const executor = userMap[delivery.executor_id]

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
              <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A' }}>
                {order ? `Заказ #${order.number}` : `Доставка #${delivery.id}`}
              </div>
              {order && <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 3 }}>{order.customer_name}</div>}
            </div>
            <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: '#94A3B8', lineHeight: 1, padding: 0 }}>×</button>
          </div>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 24px' }}>
          {/* Info */}
          <div style={{ marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span style={{ color: '#64748B' }}>Курьер</span>
              <span style={{ color: '#0F172A', fontWeight: 500 }}>{executor?.full_name ?? `ID ${delivery.executor_id}`}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
              <span style={{ color: '#64748B' }}>Плановая дата</span>
              <span style={{ color: '#0F172A', fontWeight: 500 }}>{delivery.planned_date}</span>
            </div>
            {order?.delivery_address && (
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: '#64748B' }}>Адрес</span>
                <span style={{ color: '#0F172A', fontWeight: 500, textAlign: 'right', maxWidth: 260 }}>{order.delivery_address}</span>
              </div>
            )}
          </div>

          {/* Checklist */}
          <div style={{ background: '#F8FAFC', borderRadius: 8, padding: '12px 14px', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Состав заказа
              </div>
              <div style={{ fontSize: 12, color: '#64748B' }}>{checkedCount}/{totalItems}</div>
            </div>
            {totalItems > 0 && (
              <div style={{ height: 4, background: '#E2E8F0', borderRadius: 2, marginBottom: 12, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${progress}%`, background: allChecked ? '#059669' : '#3B82F6', borderRadius: 2, transition: 'width 0.2s' }} />
              </div>
            )}

            {totalItems === 0 ? (
              <div style={{ fontSize: 13, color: '#94A3B8', padding: '8px 0' }}>
                Состав заказа недоступен. Отметьте готовность вручную.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {items.map((item, i) => {
                  const isChecked = !!checked[i]
                  return (
                    <div
                      key={i}
                      onClick={() => setChecked(c => ({ ...c, [i]: !c[i] }))}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 10,
                        border: `1px solid ${isChecked ? '#86EFAC' : '#E2E8F0'}`,
                        borderRadius: 8, padding: 12, cursor: 'pointer',
                        background: isChecked ? '#ECFDF5' : '#FFF',
                        transition: 'all 0.15s',
                      }}
                    >
                      <div style={{
                        width: 18, height: 18, borderRadius: 4, flexShrink: 0,
                        border: `2px solid ${isChecked ? '#059669' : '#CBD5E1'}`,
                        background: isChecked ? '#059669' : '#FFF',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        {isChecked && <span style={{ color: '#FFF', fontSize: 11, lineHeight: 1, fontWeight: 700 }}>✓</span>}
                      </div>
                      <div style={{ flex: 1, fontSize: 13, color: isChecked ? '#047857' : '#0F172A' }}>
                        <div style={{ fontWeight: 500 }}>{item.product_name ?? item.name ?? `Позиция ${i + 1}`}</div>
                        {item.quantity && <div style={{ fontSize: 12, color: '#64748B', marginTop: 1 }}>{item.quantity} {item.unit ?? 'шт.'}</div>}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div style={{ padding: '14px 24px', borderTop: '1px solid #F1F5F9', flexShrink: 0 }}>
          {delivery.status === 'pending' && (
            <button
              onClick={() => pickUpMut.mutate()}
              disabled={pickUpMut.isPending || (totalItems > 0 && !allChecked)}
              style={{
                width: '100%', height: 40, border: 'none', borderRadius: 8,
                background: (totalItems === 0 || allChecked) ? '#047857' : '#E2E8F0',
                color: (totalItems === 0 || allChecked) ? '#FFF' : '#94A3B8',
                cursor: (totalItems === 0 || allChecked) ? 'pointer' : 'not-allowed',
                fontSize: 14, fontWeight: 500,
                opacity: pickUpMut.isPending ? 0.6 : 1,
                transition: 'all 0.2s',
              }}
            >
              {pickUpMut.isPending ? 'Подтверждение...' : totalItems > 0 && !allChecked
                ? `Отметьте все позиции (${checkedCount}/${totalItems})`
                : '✓ Выдано — сборка завершена'}
            </button>
          )}
          {delivery.status === 'picked_up' && (
            <div style={{ fontSize: 13, color: '#047857', fontWeight: 500, textAlign: 'center', padding: '8px 0' }}>
              ✓ Сборка завершена, ожидает отправки
            </div>
          )}
          {pickUpMut.isError && (
            <div style={{ color: '#DC2626', fontSize: 12, marginTop: 8 }}>{pickUpMut.error?.response?.data?.detail ?? 'Ошибка'}</div>
          )}
        </div>
      </div>
    </>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const COL = '100px 1.5fr 130px 130px 110px'

export default function Assembly() {
  const { data: allDeliveries = [], isLoading } = useQuery({
    queryKey: ['assembly-deliveries'],
    queryFn: () => api.get('/deliveries').then(r => r.data),
  })
  const { data: orders = [] } = useQuery({
    queryKey: ['orders-assembly'],
    queryFn: () => api.get('/orders').then(r => r.data).catch(() => []),
  })
  const { data: users = [] } = useQuery({
    queryKey: ['users-assembly'],
    queryFn: () => api.get('/users').then(r => r.data).catch(() => []),
  })

  const orderMap = useMemo(() => Object.fromEntries(orders.map(o => [o.id, o])), [orders])
  const userMap  = useMemo(() => Object.fromEntries(users.map(u => [u.id, u])), [users])

  const deliveries = useMemo(
    () => allDeliveries.filter(d => d.status === 'pending' || d.status === 'picked_up'),
    [allDeliveries]
  )

  const deliveryUsers = useMemo(() => users.filter(u => u.roles?.includes('delivery')), [users])

  const [dateFilter, setDateFilter]         = useState('')
  const [executorFilter, setExecutorFilter] = useState('all')
  const [readyFilter, setReadyFilter]       = useState('all') // 'all' | 'ready' | 'pending'
  const [search, setSearch]                 = useState('')
  const [selectedId, setSelectedId]         = useState(null)

  const filtered = useMemo(() => deliveries
    .filter(d => executorFilter === 'all' || String(d.executor_id) === executorFilter)
    .filter(d => !dateFilter || d.planned_date === dateFilter)
    .filter(d => {
      if (readyFilter === 'ready')   return d.status === 'picked_up'
      if (readyFilter === 'pending') return d.status === 'pending'
      return true
    })
    .filter(d => {
      if (!search) return true
      const s = search.toLowerCase()
      const o = orderMap[d.order_id]
      return (
        String(d.id).includes(s) ||
        (o?.customer_name ?? '').toLowerCase().includes(s) ||
        (userMap[d.executor_id]?.full_name ?? '').toLowerCase().includes(s)
      )
    })
    .sort((a, b) => (a.status === 'pending' ? -1 : 1) - (b.status === 'pending' ? -1 : 1)),
    [deliveries, executorFilter, dateFilter, readyFilter, search, orderMap, userMap]
  )

  const pendingCount = deliveries.filter(d => d.status === 'pending').length
  const readyCount   = deliveries.filter(d => d.status === 'picked_up').length
  const selected     = deliveries.find(d => d.id === selectedId) ?? null
  const hasFilters   = search || executorFilter !== 'all' || dateFilter || readyFilter !== 'all'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '24px 32px 0', flexShrink: 0 }}>
        <div style={{ marginBottom: 20 }}>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 500, color: '#0F172A' }}>Сборка</h1>
          <div style={{ fontSize: 13, color: '#64748B', marginTop: 2 }}>Заказы в очереди на сборку и отгрузку</div>
        </div>

        {/* Summary */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          {[
            { label: 'Ожидают сборки', value: pendingCount, color: pendingCount > 0 ? '#3B82F6' : '#94A3B8' },
            { label: 'Готовы к отгрузке', value: readyCount, color: readyCount > 0 ? '#047857' : '#94A3B8' },
            { label: 'Всего в работе', value: deliveries.length, color: '#0F172A' },
          ].map(c => (
            <div key={c.label} style={{ background: '#FFF', borderRadius: 10, border: '1px solid #E2E8F0', padding: '14px 20px', minWidth: 130 }}>
              <div style={{ fontSize: 11, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>{c.label}</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: c.color }}>{c.value}</div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            placeholder="Поиск по клиенту или исполнителю..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ height: 34, padding: '0 12px', border: '1px solid #E2E8F0', borderRadius: 8, fontSize: 13, outline: 'none', width: 280, fontFamily: 'inherit', color: '#0F172A', boxSizing: 'border-box' }}
          />
          <FilterChip label={`Готовность: ${readyFilter === 'all' ? 'Все' : readyFilter === 'ready' ? 'Готовы' : 'В сборке'}`}>
            <select value={readyFilter} onChange={e => setReadyFilter(e.target.value)} style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}>
              <option value="all">Все</option>
              <option value="pending">В сборке</option>
              <option value="ready">Готовы</option>
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
          <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', gap: 6, height: 34, padding: '0 12px', border: '1px solid #CBD5E1', borderRadius: 8, background: '#FFF', fontSize: 13, color: '#334155', flexShrink: 0 }}>
            <span>Дата:{dateFilter ? ` ${dateFilter}` : ' Все'}</span>
            <input
              type="date"
              value={dateFilter}
              onChange={e => setDateFilter(e.target.value)}
              style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%' }}
            />
          </div>
          {hasFilters && (
            <button onClick={() => { setSearch(''); setReadyFilter('all'); setExecutorFilter('all'); setDateFilter('') }} style={{ height: 34, padding: '0 12px', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', fontSize: 13, cursor: 'pointer', color: '#64748B' }}>
              Сбросить
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 32px 28px' }}>
        <div style={{ background: '#FFF', borderRadius: 10, border: '1px solid #E2E8F0', overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: COL, padding: '12px 16px', background: '#F8FAFC', borderBottom: '1px solid #E2E8F0', fontSize: 12, fontWeight: 500, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.06em', gap: 8 }}>
            <span>№ доставки</span>
            <span>Клиент</span>
            <span>Дата доставки</span>
            <span>Курьер</span>
            <span>Готовность</span>
          </div>

          {isLoading && <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8', fontSize: 13 }}>Загрузка...</div>}

          {!isLoading && filtered.length === 0 && (
            <div style={{ padding: '60px 24px', textAlign: 'center' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>✓</div>
              <div style={{ fontSize: 15, fontWeight: 500, color: '#0F172A', marginBottom: 6 }}>
                {hasFilters ? 'Ничего не найдено' : 'Очередь сборки пуста'}
              </div>
              <div style={{ fontSize: 13, color: '#94A3B8' }}>
                {hasFilters ? 'Попробуйте изменить фильтры' : 'Все заказы собраны или находятся в доставке'}
              </div>
            </div>
          )}

          {filtered.map(d => {
            const order    = orderMap[d.order_id]
            const executor = userMap[d.executor_id]
            const isReady  = d.status === 'picked_up'
            const isSelected = d.id === selectedId

            const items     = order?.items ?? []
            const totalItems = items.length

            return (
              <div
                key={d.id}
                onClick={() => setSelectedId(isSelected ? null : d.id)}
                style={{
                  display: 'grid', gridTemplateColumns: COL,
                  padding: '14px 16px', borderBottom: '1px solid #F1F5F9',
                  cursor: 'pointer', alignItems: 'center', fontSize: 14, gap: 8,
                  background: isSelected ? '#F0FDF4' : '#FFF',
                  boxShadow: isReady ? 'inset 4px 0 0 0 #059669' : 'none',
                  transition: 'background 0.1s',
                }}
              >
                <span style={{ color: '#94A3B8', fontFamily: 'monospace', fontSize: 13 }}>#{d.id}</span>
                <div>
                  <div style={{ fontWeight: 500, color: '#0F172A' }}>{order?.customer_name ?? `Заказ #${d.order_id}`}</div>
                  {order?.delivery_address && (
                    <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{order.delivery_address}</div>
                  )}
                </div>
                <span style={{ color: '#64748B', fontSize: 13 }}>{d.planned_date ?? '—'}</span>
                <span style={{ color: '#64748B', fontSize: 13 }}>{executor?.full_name ?? `ID ${d.executor_id}`}</span>
                <span>
                  {isReady ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 13, fontWeight: 600, color: '#047857' }}>
                      {totalItems > 0 ? `${totalItems}/${totalItems}` : '✓'} <span style={{ fontSize: 14 }}>✓</span>
                    </span>
                  ) : (
                    <span style={{ fontSize: 13, color: '#64748B' }}>
                      {totalItems > 0 ? `0/${totalItems}` : 'В сборке'}
                    </span>
                  )}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {selected && (
        <Drawer
          delivery={selected}
          order={orderMap[selected.order_id] ?? null}
          userMap={userMap}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  )
}
