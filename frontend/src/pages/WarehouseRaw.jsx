import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'

// ─── Signal helpers ───────────────────────────────────────────────────────────

function daysUntil(dateStr) {
  const today = new Date(); today.setHours(0, 0, 0, 0)
  const d = new Date(dateStr); d.setHours(0, 0, 0, 0)
  return Math.round((d - today) / 86400000)
}

function getSignal(stock, material) {
  const avail = parseFloat(stock.quantity) - parseFloat(stock.reserved)
  const days = daysUntil(stock.expiry_date)
  if (days < 0) return 'expired'
  if (material && avail < parseFloat(material.critical_stock)) return 'crit'
  if (days <= 14) return 'warn14'
  if (days <= 30) return 'warn30'
  return 'ok'
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

function ArrivalModal({ materials, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ raw_material_id: '', quantity: '', arrival_date: '', expiry_date: '', comment: '' })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const mut = useMutation({
    mutationFn: () => api.post('/warehouse/raw-material-stock', {
      raw_material_id: Number(form.raw_material_id),
      quantity: form.quantity,
      arrival_date: form.arrival_date,
      expiry_date: form.expiry_date,
      comment: form.comment || null,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['raw-stock'] }); onClose() },
  })
  const valid = form.raw_material_id && Number(form.quantity) > 0 && form.arrival_date && form.expiry_date
  return (
    <Modal title="Приход сырья" onClose={onClose} onSave={() => valid && mut.mutate()} saving={mut.isPending} error={mut.error?.response?.data?.detail}>
      <Field label="Сырьё *">
        <select style={{ ...inputStyle, background: '#FFF', cursor: 'pointer' }} value={form.raw_material_id} onChange={set('raw_material_id')}>
          <option value="">— выберите —</option>
          {materials.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
      </Field>
      <Field label="Количество *">
        <input style={inputStyle} type="number" min="0.001" step="0.001" placeholder="0.000" value={form.quantity} onChange={set('quantity')} />
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

function WriteOffModal({ stock, material, onClose }) {
  const qc = useQueryClient()
  const [amount, setAmount] = useState('')
  const avail = parseFloat(stock.quantity) - parseFloat(stock.reserved)
  const mut = useMutation({
    mutationFn: () => api.post(`/warehouse/raw-material-stock/${stock.id}/write-off`, { amount: parseFloat(amount) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['raw-stock'] }); onClose() },
  })
  const valid = Number(amount) > 0 && parseFloat(amount) <= avail
  return (
    <Modal title="Списание сырья" onClose={onClose} onSave={() => valid && mut.mutate()} saving={mut.isPending} error={mut.error?.response?.data?.detail}>
      <div style={{ background: '#F8FAFC', borderRadius: 8, padding: '12px 14px', marginBottom: 16, fontSize: 13 }}>
        <div style={{ fontWeight: 500, color: '#0F172A' }}>{material?.name}</div>
        <div style={{ color: '#64748B', marginTop: 4 }}>Доступно: {avail.toFixed(3)} {material?.unit}</div>
      </div>
      <Field label={`Количество * (макс. ${avail.toFixed(3)})`}>
        <input style={inputStyle} type="number" min="0.001" step="0.001" max={avail} placeholder="0.000" value={amount} onChange={e => setAmount(e.target.value)} />
      </Field>
    </Modal>
  )
}

function AdjustModal({ stock, material, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ quantity: String(stock.quantity), comment: stock.comment ?? '' })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const mut = useMutation({
    mutationFn: () => api.patch(`/warehouse/raw-material-stock/${stock.id}`, { quantity: parseFloat(form.quantity), comment: form.comment || null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['raw-stock'] }); onClose() },
  })
  const valid = Number(form.quantity) >= 0
  return (
    <Modal title="Корректировка остатка" onClose={onClose} onSave={() => valid && mut.mutate()} saving={mut.isPending} error={mut.error?.response?.data?.detail}>
      <div style={{ background: '#F8FAFC', borderRadius: 8, padding: '12px 14px', marginBottom: 16, fontSize: 13 }}>
        <div style={{ fontWeight: 500, color: '#0F172A' }}>{material?.name}</div>
        <div style={{ color: '#64748B', marginTop: 4 }}>Текущий остаток: {parseFloat(stock.quantity).toFixed(3)} {material?.unit}</div>
      </div>
      <Field label="Новое количество *">
        <input style={inputStyle} type="number" min="0" step="0.001" value={form.quantity} onChange={set('quantity')} />
      </Field>
      <Field label="Причина корректировки">
        <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: 68 }} value={form.comment} onChange={set('comment')} />
      </Field>
    </Modal>
  )
}

// ─── Drawer ───────────────────────────────────────────────────────────────────

function Drawer({ stock, material, signal, onClose, onWriteOff, onAdjust }) {
  const avail = parseFloat(stock.quantity) - parseFloat(stock.reserved)
  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.15)', zIndex: 100 }} />
      <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 380, background: '#FFF', boxShadow: '-4px 0 24px rgba(0,0,0,0.1)', zIndex: 101, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid #F1F5F9', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#0F172A' }}>{material?.name ?? `Сырьё #${stock.raw_material_id}`}</div>
            <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 2 }}>Партия #{stock.id}</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: '#94A3B8', lineHeight: 1, padding: 0, marginTop: 2 }}>×</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          <DrawerRow label="Сигнал"><SignalBadge signal={signal} /></DrawerRow>
          <DrawerRow label="Единица">{material?.unit ?? '—'}</DrawerRow>
          <DrawerRow label="Количество">{parseFloat(stock.quantity).toFixed(3)}</DrawerRow>
          <DrawerRow label="Зарезервировано">{parseFloat(stock.reserved).toFixed(3)}</DrawerRow>
          <DrawerRow label="Доступно">{avail.toFixed(3)}</DrawerRow>
          <DrawerRow label="Критический остаток">{material?.critical_stock ?? '—'}</DrawerRow>
          <DrawerRow label="Дата прихода">{stock.arrival_date}</DrawerRow>
          <DrawerRow label="Срок годности">{stock.expiry_date}</DrawerRow>
          {stock.comment && <DrawerRow label="Комментарий">{stock.comment}</DrawerRow>}
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #F1F5F9', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <button onClick={onAdjust} style={{ padding: '9px 0', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500, color: '#334155' }}>
            Корректировка
          </button>
          <button onClick={onWriteOff} style={{ padding: '9px 0', border: 'none', borderRadius: 8, background: '#EF4444', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>
            Списание
          </button>
        </div>
      </div>
    </>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const COL = '1fr 55px 95px 95px 95px 105px 105px'

export default function WarehouseRaw() {
  const { data: stocks = [], isLoading } = useQuery({ queryKey: ['raw-stock'], queryFn: () => api.get('/warehouse/raw-material-stock').then(r => r.data) })
  const { data: materials = [] } = useQuery({ queryKey: ['raw-materials'], queryFn: () => api.get('/references/raw-materials').then(r => r.data) })

  const matMap = useMemo(() => Object.fromEntries(materials.map(m => [m.id, m])), [materials])
  const rows = useMemo(() => stocks.map(s => ({ ...s, _mat: matMap[s.raw_material_id], _sig: getSignal(s, matMap[s.raw_material_id]) })), [stocks, matMap])

  const [search, setSearch] = useState('')
  const [sigFilter, setSigFilter] = useState('all')
  const [selectedId, setSelectedId] = useState(null)
  const [modal, setModal] = useState(null)

  const filtered = useMemo(() => rows
    .filter(r => !search || (r._mat?.name ?? '').toLowerCase().includes(search.toLowerCase()))
    .filter(r => sigFilter === 'all' || r._sig === sigFilter)
    .sort((a, b) => SIG_ORDER.indexOf(a._sig) - SIG_ORDER.indexOf(b._sig)),
    [rows, search, sigFilter])

  const summary = useMemo(() => ({
    total: rows.length,
    expired: rows.filter(r => r._sig === 'expired').length,
    crit: rows.filter(r => r._sig === 'crit').length,
    warn: rows.filter(r => r._sig === 'warn14' || r._sig === 'warn30').length,
  }), [rows])

  const selected = rows.find(r => r.id === selectedId) ?? null
  const hasFilters = search || sigFilter !== 'all'

  function closeModal() { setModal(null) }
  function closeDrawer() { setSelectedId(null) }

  return (
    <div style={{ padding: '28px 32px', minHeight: '100%', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0F172A' }}>Склад сырья</h1>
          <div style={{ fontSize: 13, color: '#64748B', marginTop: 2 }}>{rows.length} {rows.length === 1 ? 'партия' : 'партий'}</div>
        </div>
        <button onClick={() => setModal('arrival')} style={{ padding: '9px 18px', border: 'none', borderRadius: 8, background: '#3B82F6', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>
          + Приход
        </button>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <SummaryCard label="Всего партий" value={summary.total} />
        <SummaryCard label="Просрочено" value={summary.expired} color={summary.expired > 0 ? '#DC2626' : undefined} />
        <SummaryCard label="Критический" value={summary.crit} color={summary.crit > 0 ? '#EA580C' : undefined} />
        <SummaryCard label="Истекает" value={summary.warn} color={summary.warn > 0 ? '#B45309' : undefined} />
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          placeholder="Поиск по названию..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ height: 34, padding: '0 12px', border: '1px solid #E2E8F0', borderRadius: 8, fontSize: 13, outline: 'none', width: 240, fontFamily: 'inherit', color: '#0F172A', boxSizing: 'border-box' }}
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
          <span>Сырьё</span>
          <span style={{ textAlign: 'right' }}>Ед.</span>
          <span style={{ textAlign: 'right' }}>Кол-во</span>
          <span style={{ textAlign: 'right' }}>Резерв</span>
          <span style={{ textAlign: 'right' }}>Доступно</span>
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
          const avail = parseFloat(r.quantity) - parseFloat(r.reserved)
          const isSelected = r.id === selectedId
          return (
            <div
              key={r.id}
              onClick={() => setSelectedId(isSelected ? null : r.id)}
              style={{ display: 'grid', gridTemplateColumns: COL, padding: '11px 16px', borderBottom: '1px solid #F8FAFC', cursor: 'pointer', background: isSelected ? '#EFF6FF' : '#FFF', alignItems: 'center', fontSize: 13, gap: 8, transition: 'background 0.1s' }}
            >
              <div>
                <div style={{ fontWeight: 500, color: '#0F172A' }}>{r._mat?.name ?? `Сырьё #${r.raw_material_id}`}</div>
                <div style={{ marginTop: 3 }}><SignalBadge signal={r._sig} /></div>
              </div>
              <span style={{ textAlign: 'right', color: '#64748B' }}>{r._mat?.unit ?? '—'}</span>
              <span style={{ textAlign: 'right', fontWeight: 500, color: '#0F172A' }}>{parseFloat(r.quantity).toFixed(3)}</span>
              <span style={{ textAlign: 'right', color: '#64748B' }}>{parseFloat(r.reserved).toFixed(3)}</span>
              <span style={{ textAlign: 'right', fontWeight: 500, color: avail <= 0 ? '#DC2626' : '#16A34A' }}>{avail.toFixed(3)}</span>
              <span style={{ color: '#64748B' }}>{r.arrival_date}</span>
              <span style={{ color: r._sig === 'expired' ? '#DC2626' : r._sig === 'warn14' ? '#B45309' : r._sig === 'warn30' ? '#CA8A04' : '#64748B' }}>{r.expiry_date}</span>
            </div>
          )
        })}
      </div>

      {selected && (
        <Drawer
          stock={selected}
          material={selected._mat}
          signal={selected._sig}
          onClose={closeDrawer}
          onWriteOff={() => setModal('writeoff')}
          onAdjust={() => setModal('adjust')}
        />
      )}

      {modal === 'arrival' && (
        <ArrivalModal materials={materials.filter(m => m.is_active)} onClose={closeModal} />
      )}
      {modal === 'writeoff' && selected && (
        <WriteOffModal stock={selected} material={selected._mat} onClose={() => { closeModal(); closeDrawer() }} />
      )}
      {modal === 'adjust' && selected && (
        <AdjustModal stock={selected} material={selected._mat} onClose={() => { closeModal(); closeDrawer() }} />
      )}
    </div>
  )
}
