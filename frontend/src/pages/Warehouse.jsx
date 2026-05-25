import { useState } from 'react'
import { Search, Plus } from 'lucide-react'
import Modal, { Field, Input, Select, ModalFooter, Btn } from '../components/Modal'
import PageHeader from '../components/PageHeader'
import { mockWarehouseRaw, mockWarehousePackaging, mockWarehouseProducts } from '../mock/data'

function getSignal(batch, shelfLifeDays) {
  if (!batch.expiry_date) return null
  const days = Math.floor((new Date(batch.expiry_date) - new Date()) / 86400000)
  if (days < 0) return 'expired'
  if (days <= 14) return 'critical'
  if (days <= 30) return 'warn'
  return null
}

function SignalBadge({ signal }) {
  if (!signal) return null
  const map = {
    expired:  { icon: '⛔', text: 'Истёк',    cls: 'bg-red-100 text-red-700' },
    critical: { icon: '🔴', text: 'Критично', cls: 'bg-red-50 text-red-600' },
    warn:     { icon: '⚠️', text: 'Скоро',    cls: 'bg-amber-50 text-amber-700' },
  }
  const s = map[signal]
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${s.cls}`}>{s.icon} {s.text}</span>
}

const TABS = ['Сырьё', 'Упаковка', 'Продукция']

export default function Warehouse() {
  const [tab, setTab] = useState(0)

  return (
    <div className="p-6">
      <PageHeader title="Склад" />
      <div className="flex gap-1 mb-6 bg-white border border-gray-100 rounded-xl p-1 w-fit">
        {TABS.map((t, i) => (
          <button
            key={i}
            onClick={() => setTab(i)}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === i ? 'bg-[#1E293B] text-white' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === 0 && <RawTab />}
      {tab === 1 && <PackagingTab />}
      {tab === 2 && <ProductsTab />}
    </div>
  )
}

// ───── RAW MATERIALS ─────────────────────────────────────────────────────────

function RawTab() {
  const [items, setItems] = useState(mockWarehouseRaw)
  const [search, setSearch] = useState('')
  const [signalFilter, setSignalFilter] = useState('all')
  const [incomeOpen, setIncomeOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState(null)
  const [expanded, setExpanded] = useState({})

  const enriched = items.map((item) => ({
    ...item,
    totalQty: item.batches.reduce((s, b) => s + b.quantity, 0),
    reserved: item.batches.reduce((s, b) => s + (b.reserved ?? 0), 0),
    signal: item.batches.reduce((worst, b) => {
      const s = getSignal(b)
      if (s === 'expired') return 'expired'
      if (s === 'critical' && worst !== 'expired') return 'critical'
      if (s === 'warn' && !worst) return 'warn'
      return worst
    }, null),
  }))

  const filtered = enriched.filter((it) => {
    const matchSearch = it.name.toLowerCase().includes(search.toLowerCase())
    const matchSig = signalFilter === 'all' || it.signal === signalFilter
    return matchSearch && matchSig
  })

  const toggleExpand = (id) => setExpanded((p) => ({ ...p, [id]: !p[id] }))

  return (
    <>
      <div className="flex gap-3 mb-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Поиск по названию..." className="w-full pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-200" />
        </div>
        <select value={signalFilter} onChange={(e) => setSignalFilter(e.target.value)} className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none">
          <option value="all">Все сигналы</option>
          <option value="expired">⛔ Истёк</option>
          <option value="critical">🔴 Критично</option>
          <option value="warn">⚠️ Скоро истекает</option>
        </select>
        <button onClick={() => setIncomeOpen(true)} className="flex items-center gap-2 bg-[#1E293B] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#273549] transition-colors">
          <Plus size={16} /> Приход
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/60">
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Наименование</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Всего</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Резерв</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Свободно</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Партий</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Сигнал</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && <tr><td colSpan={6} className="text-center py-12 text-slate-400 text-sm">Ничего не найдено</td></tr>}
            {filtered.map((item) => (
              <>
                <tr
                  key={item.id}
                  onClick={() => toggleExpand(item.id)}
                  className={`border-b border-gray-50 cursor-pointer transition-colors hover:bg-gray-50/60 ${expanded[item.id] ? 'bg-slate-50' : ''}`}
                >
                  <td className="px-4 py-3 font-medium text-slate-900">{item.name}</td>
                  <td className="px-4 py-3 text-slate-700">{item.totalQty} {item.unit}</td>
                  <td className="px-4 py-3 text-slate-500">{item.reserved} {item.unit}</td>
                  <td className="px-4 py-3 text-slate-700">{item.totalQty - item.reserved} {item.unit}</td>
                  <td className="px-4 py-3 text-slate-500">{item.batches.length}</td>
                  <td className="px-4 py-3"><SignalBadge signal={item.signal} /></td>
                </tr>
                {expanded[item.id] && item.batches.map((b) => {
                  const sig = getSignal(b)
                  return (
                    <tr key={`b-${b.id}`} className="border-b border-gray-50 bg-slate-50/70">
                      <td className="px-8 py-2 text-slate-500 text-xs">↳ Партия #{b.id}</td>
                      <td className="px-4 py-2 text-slate-600 text-xs">{b.quantity} {item.unit}</td>
                      <td className="px-4 py-2 text-slate-500 text-xs">{b.reserved ?? 0} {item.unit}</td>
                      <td className="px-4 py-2 text-slate-600 text-xs">{b.quantity - (b.reserved ?? 0)} {item.unit}</td>
                      <td className="px-4 py-2 text-slate-500 text-xs">до {b.expiry_date}</td>
                      <td className="px-4 py-2"><SignalBadge signal={sig} /></td>
                    </tr>
                  )
                })}
              </>
            ))}
          </tbody>
        </table>
      </div>

      <IncomeModal
        open={incomeOpen}
        label="Приход сырья"
        options={items.map((i) => ({ value: i.name, label: i.name }))}
        onClose={() => setIncomeOpen(false)}
        onSave={(data) => {
          setItems((prev) => prev.map((it) =>
            it.name === data.material
              ? { ...it, batches: [...it.batches, { id: Date.now(), quantity: data.quantity, expiry_date: data.expiry_date, reserved: 0 }] }
              : it
          ))
          setIncomeOpen(false)
        }}
      />
    </>
  )
}

// ───── PACKAGING ─────────────────────────────────────────────────────────────

function PackagingTab() {
  const [items, setItems] = useState(mockWarehousePackaging)
  const [search, setSearch] = useState('')
  const [incomeOpen, setIncomeOpen] = useState(false)

  const filtered = items.filter((it) => it.name.toLowerCase().includes(search.toLowerCase()))

  return (
    <>
      <div className="flex gap-3 mb-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Поиск..." className="w-full pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-200" />
        </div>
        <button onClick={() => setIncomeOpen(true)} className="flex items-center gap-2 bg-[#1E293B] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#273549] transition-colors">
          <Plus size={16} /> Приход
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/60">
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Наименование</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Остаток</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Критический запас</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Статус</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && <tr><td colSpan={4} className="text-center py-12 text-slate-400 text-sm">Ничего не найдено</td></tr>}
            {filtered.map((item) => {
              const isCritical = item.quantity <= item.critical_stock
              return (
                <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50/60 transition-colors">
                  <td className="px-4 py-3 font-medium text-slate-900">{item.name}</td>
                  <td className={`px-4 py-3 font-medium ${isCritical ? 'text-red-600' : 'text-slate-700'}`}>{item.quantity} {item.unit}</td>
                  <td className="px-4 py-3 text-slate-500">{item.critical_stock} {item.unit}</td>
                  <td className="px-4 py-3">
                    {isCritical
                      ? <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-red-50 text-red-600">🔴 Критично</span>
                      : <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-700">✓ В норме</span>
                    }
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <IncomeModal
        open={incomeOpen}
        label="Приход упаковки"
        options={items.map((i) => ({ value: i.name, label: i.name }))}
        onClose={() => setIncomeOpen(false)}
        onSave={(data) => {
          setItems((prev) => prev.map((it) =>
            it.name === data.material ? { ...it, quantity: it.quantity + data.quantity } : it
          ))
          setIncomeOpen(false)
        }}
      />
    </>
  )
}

// ───── PRODUCTS ───────────────────────────────────────────────────────────────

function ProductsTab() {
  const [items] = useState(mockWarehouseProducts)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState({})

  const enriched = items.map((it) => ({
    ...it,
    totalQty: it.batches.reduce((s, b) => s + b.quantity, 0),
    reserved: it.batches.reduce((s, b) => s + (b.reserved ?? 0), 0),
  }))

  const filtered = enriched.filter((it) => it.name.toLowerCase().includes(search.toLowerCase()))
  const toggleExpand = (id) => setExpanded((p) => ({ ...p, [id]: !p[id] }))

  return (
    <>
      <div className="flex gap-3 mb-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Поиск..." className="w-full pl-9 pr-4 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-200" />
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/60">
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Наименование</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Всего</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Резерв</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Свободно</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Партий</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && <tr><td colSpan={5} className="text-center py-12 text-slate-400 text-sm">Ничего не найдено</td></tr>}
            {filtered.map((item) => (
              <>
                <tr
                  key={item.id}
                  onClick={() => toggleExpand(item.id)}
                  className={`border-b border-gray-50 cursor-pointer hover:bg-gray-50/60 transition-colors ${expanded[item.id] ? 'bg-slate-50' : ''}`}
                >
                  <td className="px-4 py-3 font-medium text-slate-900">{item.name}</td>
                  <td className="px-4 py-3 text-slate-700">{item.totalQty} {item.unit}</td>
                  <td className="px-4 py-3 text-slate-500">{item.reserved} {item.unit}</td>
                  <td className="px-4 py-3 text-slate-700">{item.totalQty - item.reserved} {item.unit}</td>
                  <td className="px-4 py-3 text-slate-500">{item.batches.length}</td>
                </tr>
                {expanded[item.id] && item.batches.map((b) => (
                  <tr key={`b-${b.id}`} className="border-b border-gray-50 bg-slate-50/70">
                    <td className="px-8 py-2 text-slate-500 text-xs">↳ Партия #{b.id} (от {b.produced_at})</td>
                    <td className="px-4 py-2 text-slate-600 text-xs">{b.quantity} {item.unit}</td>
                    <td className="px-4 py-2 text-slate-500 text-xs">{b.reserved ?? 0} {item.unit}</td>
                    <td className="px-4 py-2 text-slate-600 text-xs">{b.quantity - (b.reserved ?? 0)} {item.unit}</td>
                    <td></td>
                  </tr>
                ))}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

// ───── INCOME MODAL ───────────────────────────────────────────────────────────

function IncomeModal({ open, label, options, onClose, onSave }) {
  const [form, setForm] = useState({ material: '', quantity: '', expiry_date: '' })
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  return (
    <Modal open={open} onClose={onClose} title={label}>
      <Field label="Наименование" required>
        <Select value={form.material} onChange={(e) => set('material', e.target.value)}>
          <option value="">Выберите...</option>
          {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </Select>
      </Field>
      <Field label="Количество" required>
        <Input type="number" min="0.1" step="0.1" value={form.quantity} onChange={(e) => set('quantity', e.target.value)} placeholder="кг / шт" />
      </Field>
      <Field label="Срок годности">
        <Input type="date" value={form.expiry_date} onChange={(e) => set('expiry_date', e.target.value)} />
      </Field>
      <ModalFooter>
        <Btn variant="secondary" onClick={onClose}>Отмена</Btn>
        <Btn onClick={() => onSave({ ...form, quantity: Number(form.quantity) })} disabled={!form.material || !form.quantity}>Сохранить</Btn>
      </ModalFooter>
    </Modal>
  )
}
