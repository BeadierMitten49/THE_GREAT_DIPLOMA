import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'

// ─── Signal helpers ───────────────────────────────────────────────────────────

function getSignal(stock, packaging) {
  if (packaging && stock.quantity < parseFloat(packaging.critical_stock)) return 'crit'
  return 'ok'
}

const SIG_LABEL = { crit: 'Критич.', ok: 'В норме' }
const SIG_COLOR = {
  crit: { bg: '#FFEDD5', color: '#EA580C' },
  ok:   { bg: '#DCFCE7', color: '#16A34A' },
}

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

function ArrivalModal({ packagingList, onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ packaging_id: '', quantity: '', comment: '' })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const mut = useMutation({
    mutationFn: () => api.post('/warehouse/packaging-stock', {
      packaging_id: Number(form.packaging_id),
      quantity: Number(form.quantity),
      comment: form.comment || null,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['pkg-stock'] }); onClose() },
  })
  const valid = form.packaging_id && Number(form.quantity) > 0
  return (
    <Modal title="Приход упаковки" onClose={onClose} onSave={() => valid && mut.mutate()} saving={mut.isPending} error={mut.error?.response?.data?.detail}>
      <Field label="Упаковка *">
        <select style={{ ...inputStyle, background: '#FFF', cursor: 'pointer' }} value={form.packaging_id} onChange={set('packaging_id')}>
          <option value="">— выберите —</option>
          {packagingList.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </Field>
      <Field label="Количество *">
        <input style={inputStyle} type="number" min="1" step="1" placeholder="0" value={form.quantity} onChange={set('quantity')} />
      </Field>
      <Field label="Комментарий">
        <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: 68 }} value={form.comment} onChange={set('comment')} />
      </Field>
    </Modal>
  )
}

function WriteOffModal({ stock, packaging, onClose }) {
  const qc = useQueryClient()
  const [amount, setAmount] = useState('')
  const mut = useMutation({
    mutationFn: () => api.post(`/warehouse/packaging-stock/${stock.id}/write-off`, { amount: Number(amount) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['pkg-stock'] }); onClose() },
  })
  const valid = Number(amount) > 0 && Number(amount) <= stock.quantity
  return (
    <Modal title="Списание упаковки" onClose={onClose} onSave={() => valid && mut.mutate()} saving={mut.isPending} error={mut.error?.response?.data?.detail}>
      <div style={{ background: '#F8FAFC', borderRadius: 8, padding: '12px 14px', marginBottom: 16, fontSize: 13 }}>
        <div style={{ fontWeight: 500, color: '#0F172A' }}>{packaging?.name}</div>
        <div style={{ color: '#64748B', marginTop: 4 }}>В наличии: {stock.quantity} {packaging?.unit}</div>
      </div>
      <Field label={`Количество * (макс. ${stock.quantity})`}>
        <input style={inputStyle} type="number" min="1" step="1" max={stock.quantity} placeholder="0" value={amount} onChange={e => setAmount(e.target.value)} />
      </Field>
    </Modal>
  )
}

// ─── Drawer ───────────────────────────────────────────────────────────────────

function Drawer({ stock, packaging, signal, onClose, onWriteOff }) {
  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.15)', zIndex: 100 }} />
      <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: 380, background: '#FFF', boxShadow: '-4px 0 24px rgba(0,0,0,0.1)', zIndex: 101, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid #F1F5F9', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#0F172A' }}>{packaging?.name ?? `Упаковка #${stock.packaging_id}`}</div>
            <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 2 }}>Запись #{stock.id}</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: '#94A3B8', lineHeight: 1, padding: 0, marginTop: 2 }}>×</button>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
          <DrawerRow label="Сигнал"><SignalBadge signal={signal} /></DrawerRow>
          <DrawerRow label="Единица">{packaging?.unit ?? '—'}</DrawerRow>
          <DrawerRow label="Количество">{stock.quantity}</DrawerRow>
          <DrawerRow label="Критический остаток">{packaging?.critical_stock ?? '—'}</DrawerRow>
          {stock.comment && <DrawerRow label="Комментарий">{stock.comment}</DrawerRow>}
        </div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #F1F5F9' }}>
          <button onClick={onWriteOff} style={{ width: '100%', padding: '9px 0', border: 'none', borderRadius: 8, background: '#EF4444', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>
            Списание
          </button>
        </div>
      </div>
    </>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const COL = '1fr 60px 100px 100px'

export default function WarehousePackaging() {
  const { data: stocks = [], isLoading } = useQuery({ queryKey: ['pkg-stock'], queryFn: () => api.get('/warehouse/packaging-stock').then(r => r.data) })
  const { data: packagingList = [] } = useQuery({ queryKey: ['packaging-refs'], queryFn: () => api.get('/references/packaging').then(r => r.data) })

  const pkgMap = useMemo(() => Object.fromEntries(packagingList.map(p => [p.id, p])), [packagingList])
  const rows = useMemo(() => stocks.map(s => ({ ...s, _pkg: pkgMap[s.packaging_id], _sig: getSignal(s, pkgMap[s.packaging_id]) })), [stocks, pkgMap])

  const [search, setSearch] = useState('')
  const [sigFilter, setSigFilter] = useState('all')
  const [selectedId, setSelectedId] = useState(null)
  const [modal, setModal] = useState(null)

  const filtered = useMemo(() => rows
    .filter(r => !search || (r._pkg?.name ?? '').toLowerCase().includes(search.toLowerCase()))
    .filter(r => sigFilter === 'all' || r._sig === sigFilter)
    .sort((a, b) => (a._sig === 'crit' ? -1 : 1) - (b._sig === 'crit' ? -1 : 1)),
    [rows, search, sigFilter])

  const summary = useMemo(() => ({
    total: rows.length,
    crit: rows.filter(r => r._sig === 'crit').length,
    totalQty: rows.reduce((s, r) => s + r.quantity, 0),
  }), [rows])

  const selected = rows.find(r => r.id === selectedId) ?? null
  const hasFilters = search || sigFilter !== 'all'

  return (
    <div style={{ padding: '28px 32px', minHeight: '100%', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#0F172A' }}>Склад упаковки</h1>
          <div style={{ fontSize: 13, color: '#64748B', marginTop: 2 }}>{rows.length} позиций</div>
        </div>
        <button onClick={() => setModal('arrival')} style={{ padding: '9px 18px', border: 'none', borderRadius: 8, background: '#3B82F6', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>
          + Приход
        </button>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <SummaryCard label="Позиций" value={summary.total} />
        <SummaryCard label="Критический" value={summary.crit} color={summary.crit > 0 ? '#EA580C' : undefined} />
        <SummaryCard label="Всего единиц" value={summary.totalQty.toLocaleString('ru')} />
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
            <option value="crit">{SIG_LABEL.crit}</option>
            <option value="ok">{SIG_LABEL.ok}</option>
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
          <span>Упаковка</span>
          <span style={{ textAlign: 'right' }}>Ед.</span>
          <span style={{ textAlign: 'right' }}>Кол-во</span>
          <span style={{ textAlign: 'right' }}>Критич.</span>
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
              <div>
                <div style={{ fontWeight: 500, color: '#0F172A' }}>{r._pkg?.name ?? `Упаковка #${r.packaging_id}`}</div>
                <div style={{ marginTop: 3 }}><SignalBadge signal={r._sig} /></div>
              </div>
              <span style={{ textAlign: 'right', color: '#64748B' }}>{r._pkg?.unit ?? '—'}</span>
              <span style={{ textAlign: 'right', fontWeight: 500, color: r._sig === 'crit' ? '#EA580C' : '#0F172A' }}>{r.quantity.toLocaleString('ru')}</span>
              <span style={{ textAlign: 'right', color: '#64748B' }}>{r._pkg?.critical_stock ?? '—'}</span>
            </div>
          )
        })}
      </div>

      {selected && (
        <Drawer
          stock={selected}
          packaging={selected._pkg}
          signal={selected._sig}
          onClose={() => setSelectedId(null)}
          onWriteOff={() => setModal('writeoff')}
        />
      )}

      {modal === 'arrival' && (
        <ArrivalModal packagingList={packagingList.filter(p => p.is_active)} onClose={() => setModal(null)} />
      )}
      {modal === 'writeoff' && selected && (
        <WriteOffModal stock={selected} packaging={selected._pkg} onClose={() => { setModal(null); setSelectedId(null) }} />
      )}
    </div>
  )
}
