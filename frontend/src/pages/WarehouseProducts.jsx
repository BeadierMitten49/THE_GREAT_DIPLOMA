import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useAuth } from '../contexts/AuthContext'

// ─── Signal helpers ───────────────────────────────────────────────────────────

function daysUntil(dateStr) {
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const d = new Date(dateStr); d.setHours(0, 0, 0, 0)
  return Math.round((d - today) / 86400000)
}

function getSignal(stock, product) {
  const avail = stock.quantity - stock.reserved
  const days = daysUntil(stock.expiry_date)
  if (days < 0) return 'expired'
  if (product && avail < parseFloat(product.critical_stock)) return 'crit'
  if (days <= 14) return 'warn14'
  if (days <= 30) return 'warn30'
  return 'ok'
}

function batchLabel(stock) {
  return `П-${stock.batch_year}-${String(stock.batch_number).padStart(3, '0')}`
}

const SIG_LABEL = { expired: 'Просрочено', crit: 'Критич.', warn14: '≤14 дней', warn30: '≤30 дней', ok: 'В норме' }
const SIG_COLOR = {
  expired: { bg: '#FEE2E2', color: '#DC2626' },
  crit:    { bg: '#FFEDD5', color: '#EA580C' },
  warn14:  { bg: '#FEF3C7', color: '#B45309' },
  warn30:  { bg: '#FEF9C3', color: '#CA8A04' },
  ok:      { bg: '#DCFCE7', color: '#16A34A' },
}
const SIG_ORDER = ['expired', 'crit', 'warn14', 'warn30', 'ok']

function SignalBadge({ signal }) {
  const s = SIG_COLOR[signal] ?? SIG_COLOR.ok
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', height: 20, padding: '0 7px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: s.bg, color: s.color }}>
      {SIG_LABEL[signal]}
    </span>
  )
}

// ─── Shared UI ────────────────────────────────────────────────────────────────

const inputStyle = { width: '100%', padding: '8px 12px', border: '1px solid #E2E8F0', borderRadius: 8, fontSize: 13, outline: 'none', boxSizing: 'border-box', fontFamily: 'inherit', color: '#0F172A' }

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 12, fontWeight: 500, color: '#64748B', marginBottom: 6 }}>{label}</div>
      {children}
    </div>
  )
}

function Modal({ title, onClose, onSave, saving, error, children }) {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}>
      <div style={{ background: '#FFF', borderRadius: 12, width: 480, maxHeight: '90vh', overflowY: 'auto', padding: 28, boxShadow: '0 20px 60px rgba(0,0,0,0.25)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: '#0F172A' }}>{title}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: '#94A3B8', lineHeight: 1, padding: 0 }}>×</button>
        </div>
        {children}
        {error && <div style={{ color: '#DC2626', fontSize: 12, marginTop: 8 }}>{error}</div>}
        <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '8px 18px', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, color: '#334155' }}>Отмена</button>
          <button onClick={onSave} disabled={saving} style={{ padding: '8px 18px', border: 'none', borderRadius: 8, background: '#3B82F6', color: '#FFF', cursor: saving ? 'not-allowed' : 'pointer', fontSize: 13, fontWeight: 500, opacity: saving ? 0.6 : 1 }}>
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  )
}

function FilterChip({ label, children }) {
  return (
    <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', gap: 6, height: 34, padding: '0 12px', border: '1px solid #CBD5E1', borderRadius: 8, background: '#FFF', fontSize: 13, cursor: 'pointer', userSelect: 'none', color: '#334155', flexShrink: 0 }}>
      <span>{label}</span>
      {children}
    </div>
  )
}

function SummaryCard({ label, value, color }) {
  return (
    <div style={{ background: '#FFF', borderRadius: 10, border: '1px solid #E2E8F0', padding: '14px 20px', minWidth: 140 }}>
      <div style={{ fontSize: 11, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700, color: color ?? '#0F172A' }}>{value}</div>
    </div>
  )
}

function DrawerRow({ label, children }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', paddingBottom: 12, marginBottom: 12, borderBottom: '1px solid #F1F5F9', fontSize: 13 }}>
      <span style={{ color: '#64748B', flexShrink: 0, marginRight: 12 }}>{label}</span>
      <span style={{ color: '#0F172A', fontWeight: 500, textAlign: 'right' }}>{children}</span>
    </div>
  )
}

// ─── Modals ───────────────────────────────────────────────────────────────────

function AcceptFromTaskModal({ onClose }) {
  const qc = useQueryClient()
  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['pending-tasks'],
    queryFn: () => api.get('/warehouse/product-stock/pending-tasks').then(r => r.data),
  })
  const [taskId, setTaskId] = useState('')
  const mut = useMutation({
    mutationFn: () => api.post('/warehouse/product-stock/from-task', { task_id: Number(taskId) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['prod-stock'] }); qc.invalidateQueries({ queryKey: ['pending-tasks'] }); onClose() },
  })
  return (
    <Modal title="Приёмка по задаче" onClose={onClose} onSave={() => taskId && mut.mutate()} saving={mut.isPending} error={mut.error?.response?.data?.detail}>
      {isLoading && <div style={{ color: '#94A3B8', fontSize: 13, textAlign: 'center', padding: 20 }}>Загрузка задач...</div>}
      {!isLoading && tasks.length === 0 && (
        <div style={{ background: '#F8FAFC', borderRadius: 8, padding: '16px 14px', fontSize: 13, color: '#64748B', textAlign: 'center' }}>
          Нет готовых задач для приёмки
        </div>
      )}
      {!isLoading && tasks.length > 0 && (
        <>
          <div style={{ fontSize: 13, color: '#64748B', marginBottom: 12 }}>Выберите выполненную задачу для оприходования продукции:</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {tasks.map(t => (
              <div
                key={t.task_id}
                onClick={() => setTaskId(String(t.task_id))}
                style={{ padding: '12px 14px', border: `1px solid ${taskId === String(t.task_id) ? '#3B82F6' : '#E2E8F0'}`, borderRadius: 8, cursor: 'pointer', background: taskId === String(t.task_id) ? '#EFF6FF' : '#FFF', transition: 'all 0.1s' }}
              >
                <div style={{ fontWeight: 500, fontSize: 13, color: '#0F172A' }}>{t.product_name}</div>
                <div style={{ display: 'flex', gap: 16, marginTop: 6, fontSize: 12, color: '#64748B' }}>
                  <span>Задача #{t.task_id}</span>
                  <span>Плановое: {t.planned_quantity}</span>
                  <span>Фактическое: {t.actual_quantity}</span>
                </div>
                {t.completed_at && <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 4 }}>Завершено: {t.completed_at.slice(0, 10)}</div>}
              </div>
            ))}
          </div>
        </>
      )}
    </Modal>
  )
}

function ArrivalModal({ products, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ product_id: '', quantity: '', arrival_date: '', expiry_date: '', comment: '' })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const mut = useMutation({
    mutationFn: () => api.post('/warehouse/product-stock', {
      product_id: Number(form.product_id),
      quantity: Number(form.quantity),
      arrival_date: form.arrival_date,
      expiry_date: form.expiry_date,
      comment: form.comment || null,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['prod-stock'] }); onClose() },
  })
  const valid = form.product_id && Number(form.quantity) > 0 && form.arrival_date && form.expiry_date
  return (
    <Modal title="Приход продукции" onClose={onClose} onSave={() => valid && mut.mutate()} saving={mut.isPending} error={mut.error?.response?.data?.detail}>
      <Field label="Продукция *">
        <select style={{ ...inputStyle, background: '#FFF', cursor: 'pointer' }} value={form.product_id} onChange={set('product_id')}>
          <option value="">— выберите —</option>
          {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </Field>
      <Field label="Количество (коробок) *">
        <input style={inputStyle} type="number" min="1" step="1" placeholder="0" value={form.quantity} onChange={set('quantity')} />
      </Field>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <Field label="Дата прихода *">
          <input style={inputStyle} type="date" value={form.arrival_date} onChange={set('arrival_date')} />
        </Field>
        <Field label="Срок годности *">
          <input style={inputStyle} type="date" value={form.expiry_date} onChange={set('expiry_date')} />
        </Field>
      </div>
      <Field label="Комментарий">
        <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: 68 }} value={form.comment} onChange={set('comment')} />
      </Field>
    </Modal>
  )
}

function AdjustModal({ stock, product, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ quantity: String(stock.quantity), comment: stock.comment ?? '' })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const mut = useMutation({
    mutationFn: () => api.patch(`/warehouse/product-stock/${stock.id}`, { quantity: Number(form.quantity), comment: form.comment || null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['prod-stock'] }); onClose() },
  })
  const valid = Number(form.quantity) >= 0
  return (
    <Modal title="Корректировка остатка" onClose={onClose} onSave={() => valid && mut.mutate()} saving={mut.isPending} error={mut.error?.response?.data?.detail}>
      <div style={{ background: '#F8FAFC', borderRadius: 8, padding: '12px 14px', marginBottom: 16, fontSize: 13 }}>
        <div style={{ fontWeight: 500, color: '#0F172A' }}>{product?.name} — {batchLabel(stock)}</div>
        <div style={{ color: '#64748B', marginTop: 4 }}>Текущий остаток: {stock.quantity} коробок</div>
      </div>
      <Field label="Новое количество *">
        <input style={inputStyle} type="number" min="0" step="1" value={form.quantity} onChange={set('quantity')} />
      </Field>
      <Field label="Причина корректировки">
        <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: 68 }} value={form.comment} onChange={set('comment')} />
      </Field>
    </Modal>
  )
}

function WriteOffModal({ stock, product, onClose }) {
  const qc = useQueryClient()
  const [amount, setAmount] = useState('')
  const avail = stock.quantity - stock.reserved
  const mut = useMutation({
    mutationFn: () => api.post(`/warehouse/product-stock/${stock.id}/write-off`, { amount: Number(amount) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['prod-stock'] }); onClose() },
  })
  const valid = Number(amount) > 0 && Number(amount) <= avail
  return (
    <Modal title="Списание продукции" onClose={onClose} onSave={() => valid && mut.mutate()} saving={mut.isPending} error={mut.error?.response?.data?.detail}>
      <div style={{ background: '#F8FAFC', borderRadius: 8, padding: '12px 14px', marginBottom: 16, fontSize: 13 }}>
        <div style={{ fontWeight: 500, color: '#0F172A' }}>{product?.name} — {batchLabel(stock)}</div>
        <div style={{ color: '#64748B', marginTop: 4 }}>Доступно: {avail} коробок</div>
      </div>
      <Field label={`Количество * (макс. ${avail})`}>
        <input style={inputStyle} type="number" min="1" step="1" max={avail} placeholder="0" value={amount} onChange={e => setAmount(e.target.value)} />
      </Field>
    </Modal>
  )
}

// ─── Drawer ───────────────────────────────────────────────────────────────────

function Drawer({ stock, product, signal, isDirector, onClose, onAdjust, onWriteOff }) {
  const avail = stock.quantity - stock.reserved
  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.15)', zIndex: 100 }} />
      <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 380, background: '#FFF', boxShadow: '-4px 0 24px rgba(0,0,0,0.1)', zIndex: 101, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid #F1F5F9', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#0F172A' }}>{product?.name ?? `Продукт #${stock.product_id}`}</div>
            <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 2 }}>Партия {batchLabel(stock)}</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: '#94A3B8', lineHeight: 1, padding: 0, marginTop: 2 }}>×</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          <DrawerRow label="Сигнал"><SignalBadge signal={signal} /></DrawerRow>
          <DrawerRow label="Кол-во (коробок)">{stock.quantity}</DrawerRow>
          <DrawerRow label="Зарезервировано">{stock.reserved}</DrawerRow>
          <DrawerRow label="Доступно">{avail}</DrawerRow>
          <DrawerRow label="Критический остаток">{product?.critical_stock ?? '—'}</DrawerRow>
          <DrawerRow label="Дата прихода">{stock.arrival_date}</DrawerRow>
          <DrawerRow label="Срок годности">{stock.expiry_date}</DrawerRow>
          {stock.comment && <DrawerRow label="Комментарий">{stock.comment}</DrawerRow>}

          {stock.reserved_orders.length > 0 && (
            <div style={{ marginTop: 4 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
                Заказы под резерв
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {stock.reserved_orders.map(ordId => (
                  <span key={ordId} style={{ display: 'inline-flex', alignItems: 'center', height: 24, padding: '0 10px', borderRadius: 4, background: '#EFF6FF', color: '#3B82F6', fontSize: 12, fontWeight: 500 }}>
                    Заказ #{ordId}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #F1F5F9', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <button onClick={onAdjust} style={{ padding: '9px 0', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500, color: '#334155' }}>
            Корректировка
          </button>
          {isDirector && (
            <button onClick={onWriteOff} style={{ padding: '9px 0', border: 'none', borderRadius: 8, background: '#EF4444', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>
              Списание
            </button>
          )}
        </div>
      </div>
    </>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const COL = '90px 1fr 80px 80px 105px 105px'

export default function WarehouseProducts() {
  const { hasRole } = useAuth()
  const isDirector = hasRole('director')

  const { data: stocks = [], isLoading } = useQuery({ queryKey: ['prod-stock'], queryFn: () => api.get('/warehouse/product-stock').then(r => r.data) })
  const { data: products = [] } = useQuery({ queryKey: ['product-refs'], queryFn: () => api.get('/references/products').then(r => r.data) })
  const { data: pendingTasks = [] } = useQuery({ queryKey: ['pending-tasks'], queryFn: () => api.get('/warehouse/product-stock/pending-tasks').then(r => r.data) })

  const prodMap = useMemo(() => Object.fromEntries(products.map(p => [p.id, p])), [products])
  const rows = useMemo(() => stocks.map(s => ({ ...s, _prod: prodMap[s.product_id], _sig: getSignal(s, prodMap[s.product_id]) })), [stocks, prodMap])

  const [search, setSearch] = useState('')
  const [sigFilter, setSigFilter] = useState('all')
  const [selectedId, setSelectedId] = useState(null)
  const [modal, setModal] = useState(null)

  const filtered = useMemo(() => rows
    .filter(r => !search || (r._prod?.name ?? '').toLowerCase().includes(search.toLowerCase()) || batchLabel(r).toLowerCase().includes(search.toLowerCase()))
    .filter(r => sigFilter === 'all' || r._sig === sigFilter)
    .sort((a, b) => SIG_ORDER.indexOf(a._sig) - SIG_ORDER.indexOf(b._sig)),
    [rows, search, sigFilter])

  const summary = useMemo(() => ({
    total: rows.length,
    expired: rows.filter(r => r._sig === 'expired').length,
    crit: rows.filter(r => r._sig === 'crit').length,
    pending: pendingTasks.length,
  }), [rows, pendingTasks])

  const selected = rows.find(r => r.id === selectedId) ?? null
  const hasFilters = search || sigFilter !== 'all'

  function closeModal() { setModal(null) }
  function closeDrawer() { setSelectedId(null) }

  return (
    <div style={{ padding: '28px 32px', minHeight: '100%', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0F172A' }}>Склад готовой продукции</h1>
          <div style={{ fontSize: 13, color: '#64748B', marginTop: 2 }}>{rows.length} {rows.length === 1 ? 'партия' : 'партий'}</div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {pendingTasks.length > 0 && (
            <button onClick={() => setModal('from-task')} style={{ padding: '9px 18px', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500, color: '#334155', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 20, height: 20, borderRadius: '50%', background: '#3B82F6', color: '#FFF', fontSize: 11, fontWeight: 700 }}>{pendingTasks.length}</span>
              Приёмка по задаче
            </button>
          )}
          <button onClick={() => setModal('arrival')} style={{ padding: '9px 18px', border: 'none', borderRadius: 8, background: '#3B82F6', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>
            + Приход
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <SummaryCard label="Всего партий" value={summary.total} />
        <SummaryCard label="Просрочено" value={summary.expired} color={summary.expired > 0 ? '#DC2626' : undefined} />
        <SummaryCard label="Критический" value={summary.crit} color={summary.crit > 0 ? '#EA580C' : undefined} />
        <SummaryCard label="К приёмке" value={summary.pending} color={summary.pending > 0 ? '#3B82F6' : undefined} />
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          placeholder="Поиск по продукту или партии..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ height: 34, padding: '0 12px', border: '1px solid #E2E8F0', borderRadius: 8, fontSize: 13, outline: 'none', width: 260, fontFamily: 'inherit', color: '#0F172A', boxSizing: 'border-box' }}
        />
        <FilterChip label={`Сигнал: ${sigFilter === 'all' ? 'Все' : SIG_LABEL[sigFilter]}`}>
          <select value={sigFilter} onChange={e => setSigFilter(e.target.value)} style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}>
            <option value="all">Все</option>
            {SIG_ORDER.map(s => <option key={s} value={s}>{SIG_LABEL[s]}</option>)}
          </select>
        </FilterChip>
        {hasFilters && (
          <button onClick={() => { setSearch(''); setSigFilter('all') }} style={{ height: 34, padding: '0 12px', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', fontSize: 13, cursor: 'pointer', color: '#64748B' }}>
            Сбросить
          </button>
        )}
      </div>

      <div style={{ background: '#FFF', borderRadius: 12, border: '1px solid #E2E8F0', overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: COL, padding: '10px 16px', borderBottom: '1px solid #F1F5F9', fontSize: 11, fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.06em', gap: 8 }}>
          <span>Партия</span>
          <span>Продукция</span>
          <span style={{ textAlign: 'right' }}>Кол-во</span>
          <span style={{ textAlign: 'right' }}>Резерв</span>
          <span>Приход</span>
          <span>Срок годн.</span>
        </div>

        {isLoading && <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8', fontSize: 13 }}>Загрузка...</div>}
        {!isLoading && filtered.length === 0 && (
          <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8', fontSize: 13 }}>
            {hasFilters ? 'Ничего не найдено' : 'Нет данных'}
          </div>
        )}

        {filtered.map(r => {
          const isSelected = r.id === selectedId
          return (
            <div
              key={r.id}
              onClick={() => setSelectedId(isSelected ? null : r.id)}
              style={{ display: 'grid', gridTemplateColumns: COL, padding: '11px 16px', borderBottom: '1px solid #F8FAFC', cursor: 'pointer', background: isSelected ? '#EFF6FF' : '#FFF', alignItems: 'center', fontSize: 13, gap: 8, transition: 'background 0.1s' }}
            >
              <span style={{ fontFamily: 'monospace', fontSize: 12, color: '#64748B', fontWeight: 500 }}>{batchLabel(r)}</span>
              <div>
                <div style={{ fontWeight: 500, color: '#0F172A' }}>{r._prod?.name ?? `Продукт #${r.product_id}`}</div>
                <div style={{ marginTop: 3 }}><SignalBadge signal={r._sig} /></div>
              </div>
              <span style={{ textAlign: 'right', fontWeight: 500, color: '#0F172A' }}>{r.quantity}</span>
              <span style={{ textAlign: 'right', color: r.reserved > 0 ? '#3B82F6' : '#94A3B8' }}>{r.reserved}</span>
              <span style={{ color: '#64748B' }}>{r.arrival_date}</span>
              <span style={{ color: r._sig === 'expired' ? '#DC2626' : r._sig === 'warn14' ? '#B45309' : r._sig === 'warn30' ? '#CA8A04' : '#64748B' }}>{r.expiry_date}</span>
            </div>
          )
        })}
      </div>

      {selected && (
        <Drawer
          stock={selected}
          product={selected._prod}
          signal={selected._sig}
          isDirector={isDirector}
          onClose={closeDrawer}
          onAdjust={() => setModal('adjust')}
          onWriteOff={() => setModal('writeoff')}
        />
      )}

      {modal === 'from-task' && <AcceptFromTaskModal onClose={closeModal} />}
      {modal === 'arrival' && <ArrivalModal products={products.filter(p => p.is_active)} onClose={closeModal} />}
      {modal === 'adjust' && selected && <AdjustModal stock={selected} product={selected._prod} onClose={() => { closeModal(); closeDrawer() }} />}
      {modal === 'writeoff' && selected && <WriteOffModal stock={selected} product={selected._prod} onClose={() => { closeModal(); closeDrawer() }} />}
    </div>
  )
}
