import { useState, useMemo, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useAuth } from '../contexts/AuthContext'

// ── API ───────────────────────────────────────────────────────────────────────

async function fetchRawMaterials() {
  const { data } = await api.get('/references/raw-materials', { params: { include_inactive: true } })
  return data
}
async function fetchPackaging() {
  const { data } = await api.get('/references/packaging', { params: { include_inactive: true } })
  return data
}
async function fetchProducts() {
  const { data } = await api.get('/references/products', { params: { include_inactive: true } })
  return data
}
async function fetchCustomers() {
  const { data } = await api.get('/references/customers', { params: { include_inactive: true } })
  return data
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function applyFilter(items, search, statusFilter, nameKey = 'name') {
  return items.filter(it => {
    const matchName = !search || String(it[nameKey] ?? '').toLowerCase().includes(search.toLowerCase())
    const matchStatus =
      statusFilter === 'all'          ? true :
      statusFilter === 'active'       ? it.is_active :
      /* deactivated */                 !it.is_active
    return matchName && matchStatus
  })
}

// ── Main page ─────────────────────────────────────────────────────────────────

const TABS = ['Сырьё', 'Упаковка', 'Продукция', 'Рецептура', 'Заказчики']

export default function References() {
  const [activeTab, setActiveTab] = useState(0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>

      {/* Header + tab strip */}
      <div style={{ padding: '24px 32px 0', flexShrink: 0 }}>
        <div style={{ fontSize: 24, fontWeight: 500, color: '#0F172A' }}>Справочники</div>
        <div style={{ fontSize: 13, color: '#64748B', marginTop: 4 }}>Управление справочной информацией системы</div>
        <div style={{ display: 'flex', marginTop: 20, borderBottom: '1px solid #E2E8F0' }}>
          {TABS.map((label, i) => (
            <button
              key={i}
              onClick={() => setActiveTab(i)}
              style={{
                padding: '10px 18px', fontSize: 14, fontWeight: 500, cursor: 'pointer',
                background: 'none', border: 'none', fontFamily: 'inherit',
                color: activeTab === i ? '#0F172A' : '#64748B',
                borderBottom: `2px solid ${activeTab === i ? '#0F172A' : 'transparent'}`,
                marginBottom: -1,
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        {activeTab === 0 && <RawMaterialsTab />}
        {activeTab === 1 && <PackagingTab />}
        {activeTab === 2 && <ProductsTab />}
        {activeTab === 3 && <RecipeTab />}
        {activeTab === 4 && <CustomersTab />}
      </div>
    </div>
  )
}

// ── Tab: Сырьё ────────────────────────────────────────────────────────────────

function RawMaterialsTab() {
  const { hasRole } = useAuth()
  const isDirector = hasRole('director')
  const qc = useQueryClient()

  const [selectedId, setSelectedId] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('active')
  const [createOpen, setCreateOpen] = useState(false)
  const [editItem, setEditItem] = useState(null)

  const { data: items = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['raw-materials'],
    queryFn: fetchRawMaterials,
  })

  const filtered = useMemo(() => applyFilter(items, search, statusFilter), [items, search, statusFilter])
  const selected = items.find(it => it.id === selectedId) ?? null

  const invalidate = () => qc.invalidateQueries({ queryKey: ['raw-materials'] })

  const handleToggle = async (item) => {
    const action = item.is_active ? 'deactivate' : 'activate'
    try { await api.post(`/references/raw-materials/${item.id}/${action}`) } catch { /* ignore */ }
    invalidate()
  }

  const cols = '2fr 80px 130px 140px 100px'

  return (
    <div style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>

        {/* Toolbar */}
        <div style={{ padding: '16px 32px 0', display: 'flex', gap: 12, alignItems: 'center', flexShrink: 0 }}>
          <SearchInput value={search} onChange={setSearch} />
          <StatusFilterChip value={statusFilter} onChange={setStatusFilter} />
          {(search || statusFilter !== 'active') && (
            <button onClick={() => { setSearch(''); setStatusFilter('active') }} style={{ fontSize: 13, color: '#475569', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              Сброс
            </button>
          )}
          {isDirector && (
            <button onClick={() => setCreateOpen(true)} style={{ ...btnPrimary, marginLeft: 'auto' }}>
              <PlusIcon /> Добавить сырьё
            </button>
          )}
        </div>

        {/* Table */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 32px 0' }}>
          {isLoading ? <RefSkeleton cols={cols} /> : isError ? <ErrorBlock onRetry={refetch} /> : (
            <RefTable
              cols={cols}
              headers={['Наименование', 'Ед. изм.', 'Срок год. (дни)', 'Крит. остаток', 'Статус']}
              items={filtered}
              selectedId={selectedId}
              onRowClick={id => setSelectedId(prev => prev === id ? null : id)}
              renderRow={(it) => [
                <span style={{ fontWeight: 500 }}>{it.name}</span>,
                it.unit,
                it.shelf_life_days,
                `${it.critical_stock} ${it.unit}`,
                <StatusBadge active={it.is_active} />,
              ]}
            />
          )}
        </div>
      </div>

      {/* Drawer */}
      {selected && (
        <RefDrawer
          title={selected.name}
          isActive={selected.is_active}
          onClose={() => setSelectedId(null)}
          isDirector={isDirector}
          onEdit={() => setEditItem(selected)}
          onToggle={() => handleToggle(selected)}
        >
          <DrSection title="Атрибуты">
            <DrRow label="Наименование" value={selected.name} />
            <DrRow label="Единица изм." value={selected.unit} />
            <DrRow label="Срок годности" value={`${selected.shelf_life_days} дней`} />
            <DrRow label="Крит. остаток" value={`${selected.critical_stock} ${selected.unit}`} />
            <DrRow label="Комментарий" value={selected.comment || '—'} />
          </DrSection>
        </RefDrawer>
      )}

      {/* Modals */}
      <RawMaterialModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSave={async (body) => {
          try { await api.post('/references/raw-materials', body) } catch { /* ignore */ }
          invalidate(); setCreateOpen(false)
        }}
      />
      <RawMaterialModal
        open={!!editItem}
        item={editItem}
        onClose={() => setEditItem(null)}
        onSave={async (body) => {
          try { await api.patch(`/references/raw-materials/${editItem.id}`, body) } catch { /* ignore */ }
          invalidate(); setEditItem(null)
        }}
      />
    </div>
  )
}

function RawMaterialModal({ open, item, onClose, onSave }) {
  const editing = !!item
  const [form, setForm] = useState({ name: '', unit: '', shelf_life_days: '', critical_stock: '', comment: '' })
  const [saving, setSaving] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => {
    if (open) setForm(item
      ? { name: item.name, unit: item.unit, shelf_life_days: String(item.shelf_life_days), critical_stock: String(item.critical_stock), comment: item.comment ?? '' }
      : { name: '', unit: '', shelf_life_days: '', critical_stock: '', comment: '' }
    )
  }, [open, item])

  const isValid = form.name.trim() && form.unit.trim() && Number(form.shelf_life_days) > 0

  const handleSave = async () => {
    if (!isValid) return
    setSaving(true)
    await onSave({
      name: form.name.trim(),
      unit: form.unit.trim(),
      shelf_life_days: Number(form.shelf_life_days),
      critical_stock: Number(form.critical_stock) || 0,
      comment: form.comment.trim(),
    })
    setSaving(false)
  }

  return (
    <InlineModal open={open} onClose={onClose}
      title={editing ? 'Редактировать сырьё' : 'Добавить сырьё'} size={520}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving || !isValid} style={{ ...btnPrimary, opacity: saving || !isValid ? 0.6 : 1 }}>
          {saving ? 'Сохранение…' : 'Сохранить'}
        </button>
      </>}
    >
      <MField label="Наименование" required>
        <MInput value={form.name} onChange={e => set('name', e.target.value)} placeholder="Мука пшеничная" />
      </MField>
      <MField label="Единица измерения" required>
        <MInput value={form.unit} onChange={e => set('unit', e.target.value)} placeholder="кг" />
      </MField>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <MField label="Срок годности (дни)" required>
          <MInput type="number" min="1" value={form.shelf_life_days} onChange={e => set('shelf_life_days', e.target.value)} />
        </MField>
        <MField label="Критический остаток">
          <MInput type="number" min="0" step="0.001" value={form.critical_stock} onChange={e => set('critical_stock', e.target.value)} />
        </MField>
      </div>
      <MField label="Комментарий" opt="опц.">
        <MTextarea rows={2} value={form.comment} onChange={e => set('comment', e.target.value)} />
      </MField>
    </InlineModal>
  )
}

// ── Tab: Упаковка ─────────────────────────────────────────────────────────────

function PackagingTab() {
  const { hasRole } = useAuth()
  const isDirector = hasRole('director')
  const qc = useQueryClient()

  const [selectedId, setSelectedId] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('active')
  const [createOpen, setCreateOpen] = useState(false)
  const [editItem, setEditItem] = useState(null)

  const { data: items = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['packaging'],
    queryFn: fetchPackaging,
  })

  const filtered = useMemo(() => applyFilter(items, search, statusFilter), [items, search, statusFilter])
  const selected = items.find(it => it.id === selectedId) ?? null
  const invalidate = () => qc.invalidateQueries({ queryKey: ['packaging'] })

  const handleToggle = async (item) => {
    const action = item.is_active ? 'deactivate' : 'activate'
    try { await api.post(`/references/packaging/${item.id}/${action}`) } catch { /* ignore */ }
    invalidate()
  }

  const cols = '2fr 100px 160px 100px'

  return (
    <div style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 32px 0', display: 'flex', gap: 12, alignItems: 'center', flexShrink: 0 }}>
          <SearchInput value={search} onChange={setSearch} />
          <StatusFilterChip value={statusFilter} onChange={setStatusFilter} />
          {(search || statusFilter !== 'active') && (
            <button onClick={() => { setSearch(''); setStatusFilter('active') }} style={{ fontSize: 13, color: '#475569', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              Сброс
            </button>
          )}
          {isDirector && (
            <button onClick={() => setCreateOpen(true)} style={{ ...btnPrimary, marginLeft: 'auto' }}>
              <PlusIcon /> Добавить упаковку
            </button>
          )}
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 32px 0' }}>
          {isLoading ? <RefSkeleton cols={cols} /> : isError ? <ErrorBlock onRetry={refetch} /> : (
            <RefTable
              cols={cols}
              headers={['Наименование', 'Ед. изм.', 'Крит. остаток', 'Статус']}
              items={filtered}
              selectedId={selectedId}
              onRowClick={id => setSelectedId(prev => prev === id ? null : id)}
              renderRow={(it) => [
                <span style={{ fontWeight: 500 }}>{it.name}</span>,
                it.unit,
                `${it.critical_stock} ${it.unit}`,
                <StatusBadge active={it.is_active} />,
              ]}
            />
          )}
        </div>
      </div>

      {selected && (
        <RefDrawer title={selected.name} isActive={selected.is_active} onClose={() => setSelectedId(null)} isDirector={isDirector} onEdit={() => setEditItem(selected)} onToggle={() => handleToggle(selected)}>
          <DrSection title="Атрибуты">
            <DrRow label="Наименование" value={selected.name} />
            <DrRow label="Единица изм." value={selected.unit} />
            <DrRow label="Крит. остаток" value={`${selected.critical_stock} ${selected.unit}`} />
            <DrRow label="Комментарий" value={selected.comment || '—'} />
          </DrSection>
        </RefDrawer>
      )}

      <PackagingModal open={createOpen} onClose={() => setCreateOpen(false)}
        onSave={async (body) => { try { await api.post('/references/packaging', body) } catch { } invalidate(); setCreateOpen(false) }} />
      <PackagingModal open={!!editItem} item={editItem} onClose={() => setEditItem(null)}
        onSave={async (body) => { try { await api.patch(`/references/packaging/${editItem.id}`, body) } catch { } invalidate(); setEditItem(null) }} />
    </div>
  )
}

function PackagingModal({ open, item, onClose, onSave }) {
  const editing = !!item
  const [form, setForm] = useState({ name: '', unit: '', critical_stock: '', comment: '' })
  const [saving, setSaving] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => {
    if (open) setForm(item
      ? { name: item.name, unit: item.unit, critical_stock: String(item.critical_stock), comment: item.comment ?? '' }
      : { name: '', unit: '', critical_stock: '', comment: '' }
    )
  }, [open, item])

  const isValid = form.name.trim() && form.unit.trim()

  const handleSave = async () => {
    if (!isValid) return
    setSaving(true)
    await onSave({ name: form.name.trim(), unit: form.unit.trim(), critical_stock: Number(form.critical_stock) || 0, comment: form.comment.trim() })
    setSaving(false)
  }

  return (
    <InlineModal open={open} onClose={onClose} title={editing ? 'Редактировать упаковку' : 'Добавить упаковку'} size={480}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving || !isValid} style={{ ...btnPrimary, opacity: saving || !isValid ? 0.6 : 1 }}>
          {saving ? 'Сохранение…' : 'Сохранить'}
        </button>
      </>}
    >
      <MField label="Наименование" required>
        <MInput value={form.name} onChange={e => set('name', e.target.value)} placeholder="Пакет 1 кг" />
      </MField>
      <MField label="Единица измерения" required>
        <MInput value={form.unit} onChange={e => set('unit', e.target.value)} placeholder="шт" />
      </MField>
      <MField label="Критический остаток">
        <MInput type="number" min="0" value={form.critical_stock} onChange={e => set('critical_stock', e.target.value)} />
      </MField>
      <MField label="Комментарий" opt="опц.">
        <MTextarea rows={2} value={form.comment} onChange={e => set('comment', e.target.value)} />
      </MField>
    </InlineModal>
  )
}

// ── Tab: Продукция ────────────────────────────────────────────────────────────

function ProductsTab() {
  const { hasRole } = useAuth()
  const isDirector = hasRole('director')
  const qc = useQueryClient()

  const [selectedId, setSelectedId] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('active')
  const [createOpen, setCreateOpen] = useState(false)
  const [editItem, setEditItem] = useState(null)

  const { data: products = [], isLoading, isError, refetch } = useQuery({ queryKey: ['products-ref'], queryFn: fetchProducts })
  const { data: rawMaterials = [] } = useQuery({ queryKey: ['raw-materials'], queryFn: fetchRawMaterials })
  const rmMap = useMemo(() => Object.fromEntries(rawMaterials.map(r => [r.id, r])), [rawMaterials])

  const filtered = useMemo(() => applyFilter(products, search, statusFilter), [products, search, statusFilter])
  const selected = products.find(it => it.id === selectedId) ?? null
  const invalidate = () => qc.invalidateQueries({ queryKey: ['products-ref'] })

  const handleToggle = async (item) => {
    const action = item.is_active ? 'deactivate' : 'activate'
    try { await api.post(`/references/products/${item.id}/${action}`) } catch { }
    invalidate()
  }

  const cols = '2fr 110px 130px 140px 100px'

  return (
    <div style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 32px 0', display: 'flex', gap: 12, alignItems: 'center', flexShrink: 0 }}>
          <SearchInput value={search} onChange={setSearch} />
          <StatusFilterChip value={statusFilter} onChange={setStatusFilter} />
          {(search || statusFilter !== 'active') && (
            <button onClick={() => { setSearch(''); setStatusFilter('active') }} style={{ fontSize: 13, color: '#475569', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              Сброс
            </button>
          )}
          {isDirector && (
            <button onClick={() => setCreateOpen(true)} style={{ ...btnPrimary, marginLeft: 'auto' }}>
              <PlusIcon /> Добавить продукт
            </button>
          )}
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 32px 0' }}>
          {isLoading ? <RefSkeleton cols={cols} /> : isError ? <ErrorBlock onRetry={refetch} /> : (
            <RefTable
              cols={cols}
              headers={['Наименование', 'Штук в кор.', 'Срок год. (дни)', 'Крит. запас (шт)', 'Статус']}
              items={filtered}
              selectedId={selectedId}
              onRowClick={id => setSelectedId(prev => prev === id ? null : id)}
              renderRow={(it) => [
                <span style={{ fontWeight: 500 }}>{it.name}</span>,
                it.units_per_box,
                it.shelf_life_days,
                `${it.critical_stock} шт`,
                <StatusBadge active={it.is_active} />,
              ]}
            />
          )}
        </div>
      </div>

      {selected && (
        <RefDrawer title={selected.name} isActive={selected.is_active} onClose={() => setSelectedId(null)} isDirector={isDirector} onEdit={() => setEditItem(selected)} onToggle={() => handleToggle(selected)}>
          <DrSection title="Атрибуты">
            <DrRow label="Штук в коробке" value={String(selected.units_per_box)} />
            <DrRow label="Срок годности" value={`${selected.shelf_life_days} дней`} />
            <DrRow label="Крит. остаток" value={`${selected.critical_stock} шт`} />
          </DrSection>
          {selected.recipe?.length > 0 && (
            <DrSection title="Рецептура">
              {selected.recipe.map((r, i) => {
                const rm = rmMap[r.raw_material_id]
                return (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13 }}>
                    <span style={{ color: '#64748B' }}>{rm?.name ?? `#${r.raw_material_id}`}</span>
                    <span style={{ color: '#0F172A', fontWeight: 500 }}>
                      {Number(r.consumption_per_unit).toFixed(3)} {rm?.unit ?? 'ед'}/шт
                    </span>
                  </div>
                )
              })}
            </DrSection>
          )}
          {!selected.recipe?.length && (
            <DrSection title="Рецептура">
              <div style={{ fontSize: 13, color: '#94A3B8' }}>Рецептура не задана</div>
            </DrSection>
          )}
        </RefDrawer>
      )}

      <ProductModal open={createOpen} onClose={() => setCreateOpen(false)}
        onSave={async (body) => { try { await api.post('/references/products', body) } catch { } invalidate(); setCreateOpen(false) }} />
      <ProductModal open={!!editItem} item={editItem} onClose={() => setEditItem(null)}
        onSave={async (body) => { try { await api.patch(`/references/products/${editItem.id}`, body) } catch { } invalidate(); setEditItem(null) }} />
    </div>
  )
}

function ProductModal({ open, item, onClose, onSave }) {
  const editing = !!item
  const [form, setForm] = useState({ name: '', units_per_box: '', shelf_life_days: '', critical_stock: '' })
  const [saving, setSaving] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => {
    if (open) setForm(item
      ? { name: item.name, units_per_box: String(item.units_per_box), shelf_life_days: String(item.shelf_life_days), critical_stock: String(item.critical_stock) }
      : { name: '', units_per_box: '', shelf_life_days: '', critical_stock: '' }
    )
  }, [open, item])

  const isValid = form.name.trim() && Number(form.units_per_box) > 0 && Number(form.shelf_life_days) > 0

  const handleSave = async () => {
    if (!isValid) return
    setSaving(true)
    await onSave({ name: form.name.trim(), units_per_box: Number(form.units_per_box), shelf_life_days: Number(form.shelf_life_days), critical_stock: Number(form.critical_stock) || 0 })
    setSaving(false)
  }

  return (
    <InlineModal open={open} onClose={onClose} title={editing ? 'Редактировать продукт' : 'Добавить продукт'} size={520}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving || !isValid} style={{ ...btnPrimary, opacity: saving || !isValid ? 0.6 : 1 }}>
          {saving ? 'Сохранение…' : 'Сохранить'}
        </button>
      </>}
    >
      <MField label="Наименование" required>
        <MInput value={form.name} onChange={e => set('name', e.target.value)} placeholder="Сахар фасованный 1 кг" />
      </MField>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <MField label="Штук в коробке" required>
          <MInput type="number" min="1" value={form.units_per_box} onChange={e => set('units_per_box', e.target.value)} />
        </MField>
        <MField label="Срок годности (дни)" required>
          <MInput type="number" min="1" value={form.shelf_life_days} onChange={e => set('shelf_life_days', e.target.value)} />
        </MField>
      </div>
      <MField label="Критический запас (шт)">
        <MInput type="number" min="0" value={form.critical_stock} onChange={e => set('critical_stock', e.target.value)} />
      </MField>
    </InlineModal>
  )
}

// ── Tab: Рецептура ────────────────────────────────────────────────────────────

function RecipeTab() {
  const { hasRole } = useAuth()
  const isDirector = hasRole('director')
  const qc = useQueryClient()

  const [selectedId, setSelectedId] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('active')
  const [recipeModal, setRecipeModal] = useState(null)

  const { data: products = [], isLoading, isError, refetch } = useQuery({ queryKey: ['products-ref'], queryFn: fetchProducts })
  const { data: rawMaterials = [] } = useQuery({ queryKey: ['raw-materials'], queryFn: fetchRawMaterials })
  const rmMap = useMemo(() => Object.fromEntries(rawMaterials.map(r => [r.id, r])), [rawMaterials])

  const filtered = useMemo(() => applyFilter(products, search, statusFilter), [products, search, statusFilter])
  const selected = products.find(it => it.id === selectedId) ?? null

  const invalidate = () => qc.invalidateQueries({ queryKey: ['products-ref'] })

  const cols = '2fr 130px 100px'

  return (
    <div style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 32px 0', display: 'flex', gap: 12, alignItems: 'center', flexShrink: 0 }}>
          <SearchInput value={search} onChange={setSearch} />
          <StatusFilterChip value={statusFilter} onChange={setStatusFilter} />
          {(search || statusFilter !== 'active') && (
            <button onClick={() => { setSearch(''); setStatusFilter('active') }} style={{ fontSize: 13, color: '#475569', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              Сброс
            </button>
          )}
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 32px 0' }}>
          {isLoading ? <RefSkeleton cols={cols} /> : isError ? <ErrorBlock onRetry={refetch} /> : (
            <RefTable
              cols={cols}
              headers={['Продукт', 'Ингредиентов', 'Статус']}
              items={filtered}
              selectedId={selectedId}
              onRowClick={id => setSelectedId(prev => prev === id ? null : id)}
              renderRow={(it) => [
                <span style={{ fontWeight: 500 }}>{it.name}</span>,
                it.recipe?.length ?? 0,
                <StatusBadge active={it.is_active} />,
              ]}
            />
          )}
        </div>
      </div>

      {selected && (
        <aside style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: 420, background: '#FFF', borderLeft: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column', overflow: 'hidden', zIndex: 10 }}>
          {/* Drawer header */}
          <div style={{ padding: '18px 24px 14px', borderBottom: '1px solid #F1F5F9', flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ fontSize: 17, fontWeight: 500, color: '#0F172A', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{selected.name}</div>
              <StatusBadge active={selected.is_active} />
              <button onClick={() => setSelectedId(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748B', width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <CloseIcon />
              </button>
            </div>
          </div>

          {/* Actions */}
          {isDirector && (
            <div style={{ padding: '10px 24px', borderBottom: '1px solid #F1F5F9', flexShrink: 0 }}>
              <button onClick={() => setRecipeModal(selected)} style={btnPrimary}>
                <PencilIcon /> Редактировать рецептуру
              </button>
            </div>
          )}

          {/* Body */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '8px 24px 24px' }}>
            <DrSection title="Состав на 1 штуку продукта">
              {selected.recipe?.length > 0 ? (
                <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left', padding: '6px 0 10px', fontSize: 11, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>Сырьё</th>
                      <th style={{ textAlign: 'right', padding: '6px 0 10px', fontSize: 11, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>Расход</th>
                      <th style={{ textAlign: 'right', padding: '6px 0 10px', fontSize: 11, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>Брак %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.recipe.map((r, i) => {
                      const rm = rmMap[r.raw_material_id]
                      return (
                        <tr key={i}>
                          <td style={{ padding: '6px 0', borderBottom: '1px solid #F8FAFC', color: '#0F172A' }}>{rm?.name ?? `#${r.raw_material_id}`}</td>
                          <td style={{ padding: '6px 0', borderBottom: '1px solid #F8FAFC', textAlign: 'right', color: '#475569', fontWeight: 500 }}>
                            {Number(r.consumption_per_unit).toFixed(3)} {rm?.unit ?? 'ед'}
                          </td>
                          <td style={{ padding: '6px 0', borderBottom: '1px solid #F8FAFC', textAlign: 'right', color: '#475569' }}>
                            {Number(r.waste_percentage).toFixed(1)}%
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              ) : (
                <div style={{ fontSize: 13, color: '#94A3B8', fontStyle: 'italic' }}>
                  Рецептура не задана.{isDirector ? ' Нажмите «Редактировать рецептуру».' : ''}
                </div>
              )}
            </DrSection>
          </div>
        </aside>
      )}

      <RecipeEditModal
        open={!!recipeModal}
        product={recipeModal}
        rawMaterials={rawMaterials}
        onClose={() => setRecipeModal(null)}
        onSave={async (lines) => {
          try {
            await api.put(`/references/products/${recipeModal.id}/recipe`, { lines })
          } catch { }
          invalidate()
          setRecipeModal(null)
        }}
      />
    </div>
  )
}

function RecipeEditModal({ open, product, rawMaterials, onClose, onSave }) {
  const [lines, setLines] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open && product) {
      setLines(
        product.recipe?.length > 0
          ? product.recipe.map(r => ({
              raw_material_id: String(r.raw_material_id),
              consumption_per_unit: String(Number(r.consumption_per_unit).toFixed(3)),
              waste_percentage: String(Number(r.waste_percentage).toFixed(1)),
            }))
          : [{ raw_material_id: '', consumption_per_unit: '', waste_percentage: '0' }]
      )
    }
  }, [open, product])

  const addLine = () => setLines(prev => [...prev, { raw_material_id: '', consumption_per_unit: '', waste_percentage: '0' }])
  const removeLine = (idx) => setLines(prev => prev.filter((_, i) => i !== idx))
  const setLine = (idx, key, val) => setLines(prev => prev.map((l, i) => i === idx ? { ...l, [key]: val } : l))

  const handleSave = async () => {
    setSaving(true)
    const validLines = lines
      .filter(l => l.raw_material_id && Number(l.consumption_per_unit) > 0)
      .map(l => ({
        raw_material_id: Number(l.raw_material_id),
        consumption_per_unit: Number(l.consumption_per_unit),
        waste_percentage: Number(l.waste_percentage) || 0,
      }))
    await onSave(validLines)
    setSaving(false)
  }

  return (
    <InlineModal open={open} onClose={onClose} title={`Рецептура: ${product?.name ?? ''}`} size={680}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving} style={{ ...btnPrimary, opacity: saving ? 0.7 : 1 }}>
          {saving ? 'Сохранение…' : 'Сохранить рецептуру'}
        </button>
      </>}
    >
      {/* Column headers */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 130px 110px 36px', gap: 8, marginBottom: 6, padding: '0 2px' }}>
        {['Сырьё', 'Расход/шт', 'Брак %', ''].map((h, i) => (
          <div key={i} style={{ fontSize: 11, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>{h}</div>
        ))}
      </div>

      {/* Lines */}
      {lines.map((line, idx) => (
        <div key={idx} style={{ display: 'grid', gridTemplateColumns: '1fr 130px 110px 36px', gap: 8, marginBottom: 8, alignItems: 'center' }}>
          <select
            value={line.raw_material_id}
            onChange={e => setLine(idx, 'raw_material_id', e.target.value)}
            style={mInput}
          >
            <option value="">Выберите сырьё</option>
            {rawMaterials.filter(r => r.is_active || String(r.id) === line.raw_material_id).map(r => (
              <option key={r.id} value={r.id}>{r.name} ({r.unit})</option>
            ))}
          </select>
          <input
            type="number" step="0.001" min="0.001"
            value={line.consumption_per_unit}
            onChange={e => setLine(idx, 'consumption_per_unit', e.target.value)}
            placeholder="0.000"
            style={mInput}
          />
          <input
            type="number" step="0.1" min="0" max="100"
            value={line.waste_percentage}
            onChange={e => setLine(idx, 'waste_percentage', e.target.value)}
            placeholder="0"
            style={mInput}
          />
          <button onClick={() => removeLine(idx)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#DC2626', width: 36, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <TrashIcon />
          </button>
        </div>
      ))}

      <button onClick={addLine} style={{ ...btnSecondary, marginTop: 4 }}>
        <PlusIcon /> Добавить строку
      </button>

      <div style={{ fontSize: 12, color: '#64748B', marginTop: 12 }}>
        Расход указывается в единицах сырья на одну штуку готовой продукции.
      </div>
    </InlineModal>
  )
}

// ── Tab: Заказчики ────────────────────────────────────────────────────────────

function CustomersTab() {
  const { hasRole } = useAuth()
  const isDirector = hasRole('director')
  const qc = useQueryClient()

  const [selectedId, setSelectedId] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('active')
  const [createOpen, setCreateOpen] = useState(false)
  const [editItem, setEditItem] = useState(null)

  const { data: items = [], isLoading, isError, refetch } = useQuery({ queryKey: ['customers-ref'], queryFn: fetchCustomers })

  const filtered = useMemo(() => applyFilter(items, search, statusFilter), [items, search, statusFilter])
  const selected = items.find(it => it.id === selectedId) ?? null
  const invalidate = () => qc.invalidateQueries({ queryKey: ['customers-ref'] })

  const handleToggle = async (item) => {
    const action = item.is_active ? 'deactivate' : 'activate'
    try { await api.post(`/references/customers/${item.id}/${action}`) } catch { }
    invalidate()
  }

  const cols = '2fr 2fr 1fr 100px'

  return (
    <div style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 32px 0', display: 'flex', gap: 12, alignItems: 'center', flexShrink: 0 }}>
          <SearchInput value={search} onChange={setSearch} />
          <StatusFilterChip value={statusFilter} onChange={setStatusFilter} />
          {(search || statusFilter !== 'active') && (
            <button onClick={() => { setSearch(''); setStatusFilter('active') }} style={{ fontSize: 13, color: '#475569', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              Сброс
            </button>
          )}
          {isDirector && (
            <button onClick={() => setCreateOpen(true)} style={{ ...btnPrimary, marginLeft: 'auto' }}>
              <PlusIcon /> Добавить заказчика
            </button>
          )}
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 32px 0' }}>
          {isLoading ? <RefSkeleton cols={cols} /> : isError ? <ErrorBlock onRetry={refetch} /> : (
            <RefTable
              cols={cols}
              headers={['Наименование', 'Адрес', 'Контакт', 'Статус']}
              items={filtered}
              selectedId={selectedId}
              onRowClick={id => setSelectedId(prev => prev === id ? null : id)}
              renderRow={(it) => [
                <span style={{ fontWeight: 500 }}>{it.name}</span>,
                <span style={{ color: '#64748B' }}>{it.default_address || '—'}</span>,
                it.contact || '—',
                <StatusBadge active={it.is_active} />,
              ]}
            />
          )}
        </div>
      </div>

      {selected && (
        <RefDrawer title={selected.name} isActive={selected.is_active} onClose={() => setSelectedId(null)} isDirector={isDirector} onEdit={() => setEditItem(selected)} onToggle={() => handleToggle(selected)}>
          <DrSection title="Атрибуты">
            <DrRow label="Наименование" value={selected.name} />
            <DrRow label="Адрес" value={selected.default_address || '—'} />
            <DrRow label="Контакт" value={selected.contact || '—'} />
            <DrRow label="Комментарий" value={selected.comment || '—'} />
          </DrSection>
        </RefDrawer>
      )}

      <CustomerModal open={createOpen} onClose={() => setCreateOpen(false)}
        onSave={async (body) => { try { await api.post('/references/customers', body) } catch { } invalidate(); setCreateOpen(false) }} />
      <CustomerModal open={!!editItem} item={editItem} onClose={() => setEditItem(null)}
        onSave={async (body) => { try { await api.patch(`/references/customers/${editItem.id}`, body) } catch { } invalidate(); setEditItem(null) }} />
    </div>
  )
}

function CustomerModal({ open, item, onClose, onSave }) {
  const editing = !!item
  const [form, setForm] = useState({ name: '', default_address: '', contact: '', comment: '' })
  const [saving, setSaving] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => {
    if (open) setForm(item
      ? { name: item.name, default_address: item.default_address ?? '', contact: item.contact ?? '', comment: item.comment ?? '' }
      : { name: '', default_address: '', contact: '', comment: '' }
    )
  }, [open, item])

  const isValid = form.name.trim()

  const handleSave = async () => {
    if (!isValid) return
    setSaving(true)
    await onSave({ name: form.name.trim(), default_address: form.default_address.trim(), contact: form.contact.trim(), comment: form.comment.trim() })
    setSaving(false)
  }

  return (
    <InlineModal open={open} onClose={onClose} title={editing ? 'Редактировать заказчика' : 'Добавить заказчика'} size={520}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving || !isValid} style={{ ...btnPrimary, opacity: saving || !isValid ? 0.6 : 1 }}>
          {saving ? 'Сохранение…' : 'Сохранить'}
        </button>
      </>}
    >
      <MField label="Наименование" required>
        <MInput value={form.name} onChange={e => set('name', e.target.value)} placeholder="ООО Ромашка" />
      </MField>
      <MField label="Адрес" opt="опц.">
        <MInput value={form.default_address} onChange={e => set('default_address', e.target.value)} placeholder="г. Москва, ул. Примерная, 1" />
      </MField>
      <MField label="Контакт" opt="опц.">
        <MInput value={form.contact} onChange={e => set('contact', e.target.value)} placeholder="+7 (999) 000-00-00" />
      </MField>
      <MField label="Комментарий" opt="опц.">
        <MTextarea rows={2} value={form.comment} onChange={e => set('comment', e.target.value)} />
      </MField>
    </InlineModal>
  )
}

// ── Shared UI components ──────────────────────────────────────────────────────

function RefTable({ cols, headers, items, selectedId, onRowClick, renderRow }) {
  if (items.length === 0) {
    return (
      <div style={{ background: '#FFF', border: '1px solid #E2E8F0', borderRadius: 10, padding: '60px 24px', textAlign: 'center', marginBottom: 16 }}>
        <div style={{ fontSize: 14, color: '#64748B' }}>Нет записей по выбранным фильтрам</div>
      </div>
    )
  }
  return (
    <div style={{ background: '#FFF', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden', marginBottom: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: cols }}>
        {headers.map((h, i) => (
          <div key={i} style={thStyle}>{h}</div>
        ))}
      </div>
      {items.map((item, idx) => {
        const selected = selectedId === item.id
        const cells = renderRow(item)
        return (
          <div
            key={item.id}
            onClick={() => onRowClick(item.id)}
            style={{
              display: 'grid', gridTemplateColumns: cols, alignItems: 'center',
              cursor: 'pointer',
              background: selected ? '#F1F5F9' : item.is_active === false ? '#FAFAFA' : 'transparent',
              borderBottom: idx < items.length - 1 ? '1px solid #F1F5F9' : 'none',
              opacity: item.is_active === false ? 0.75 : 1,
            }}
            onMouseEnter={e => { if (!selected) e.currentTarget.style.background = '#F8FAFC' }}
            onMouseLeave={e => { e.currentTarget.style.background = selected ? '#F1F5F9' : item.is_active === false ? '#FAFAFA' : 'transparent' }}
          >
            {cells.map((cell, ci) => (
              <div key={ci} style={tdStyle}>{cell}</div>
            ))}
          </div>
        )
      })}
    </div>
  )
}

function RefDrawer({ title, isActive, onClose, isDirector, onEdit, onToggle, children }) {
  return (
    <aside style={{ position: 'absolute', right: 0, top: 0, bottom: 0, width: 380, background: '#FFF', borderLeft: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column', overflow: 'hidden', zIndex: 10 }}>
      {/* Header */}
      <div style={{ padding: '18px 24px 14px', borderBottom: '1px solid #F1F5F9', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ fontSize: 17, fontWeight: 500, color: '#0F172A', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{title}</div>
          <StatusBadge active={isActive} />
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748B', width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <CloseIcon />
          </button>
        </div>
      </div>

      {/* Actions */}
      {isDirector && (
        <div style={{ padding: '10px 24px', borderBottom: '1px solid #F1F5F9', display: 'flex', gap: 8, flexShrink: 0 }}>
          <button onClick={onEdit} style={btnSecondary}>
            <PencilIcon /> Редактировать
          </button>
          <button
            onClick={onToggle}
            style={isActive
              ? btnAction('#FFF', '#B45309', '#FCD34D')
              : btnAction('#047857', '#FFF', '#047857')
            }
          >
            {isActive ? <><PauseIcon /> Деактивировать</> : <><PlayIcon /> Активировать</>}
          </button>
        </div>
      )}

      {/* Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 24px 24px' }}>
        {children}
      </div>
    </aside>
  )
}

function StatusBadge({ active }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 10px', borderRadius: 999, fontSize: 12, fontWeight: 500,
      background: active ? '#F0FDF4' : '#F1F5F9',
      color: active ? '#166534' : '#64748B',
      border: `1px solid ${active ? '#86EFAC' : '#CBD5E1'}`,
      whiteSpace: 'nowrap',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: active ? '#22C55E' : '#94A3B8', flexShrink: 0 }} />
      {active ? 'Активна' : 'Деактив.'}
    </span>
  )
}

function SearchInput({ value, onChange }) {
  return (
    <div style={{ position: 'relative', flex: '0 0 260px' }}>
      <svg style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#94A3B8', pointerEvents: 'none' }} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder="Поиск по наименованию"
        style={{ height: 34, border: '1px solid #CBD5E1', borderRadius: 8, padding: '0 12px 0 32px', fontSize: 13, color: '#0F172A', background: '#FFF', width: '100%', fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box' }}
      />
    </div>
  )
}

function StatusFilterChip({ value, onChange }) {
  const LABELS = { all: 'Все', active: 'Активные', inactive: 'Деактив.' }
  return (
    <div style={{ position: 'relative' }}>
      <button style={{ display: 'inline-flex', alignItems: 'center', gap: 8, height: 34, padding: '0 12px', border: '1px solid #CBD5E1', borderRadius: 8, background: '#FFF', fontSize: 13, color: '#334155', cursor: 'pointer', fontFamily: 'inherit' }}>
        Статус: <strong style={{ fontWeight: 500, color: '#0F172A' }}>{LABELS[value]}</strong>
        <ChevronDownIcon />
      </button>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%' }}
      >
        <option value="all">Все</option>
        <option value="active">Активные</option>
        <option value="inactive">Деактив.</option>
      </select>
    </div>
  )
}

function DrSection({ title, children }) {
  return (
    <div style={{ padding: '14px 0', borderBottom: '1px solid #F1F5F9' }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10 }}>{title}</div>
      {children}
    </div>
  )
}

function DrRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13 }}>
      <span style={{ color: '#64748B' }}>{label}</span>
      <span style={{ color: '#0F172A', fontWeight: 500, textAlign: 'right', maxWidth: '60%' }}>{value}</span>
    </div>
  )
}

function RefSkeleton({ cols }) {
  return (
    <div style={{ background: '#FFF', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden' }}>
      <div style={{ display: 'grid', gridTemplateColumns: cols }}>
        {cols.split(' ').map((_, i) => <div key={i} style={thStyle}><Skel w="60%" /></div>)}
      </div>
      {[70, 55, 80, 65, 75].map((w, i) => (
        <div key={i} style={{ display: 'grid', gridTemplateColumns: cols, borderBottom: '1px solid #F1F5F9' }}>
          <div style={tdStyle}><Skel w={`${w}%`} /></div>
          {cols.split(' ').slice(1).map((_, ci) => (
            <div key={ci} style={tdStyle}><Skel w="50%" /></div>
          ))}
        </div>
      ))}
    </div>
  )
}

function Skel({ w, h = 14 }) {
  return <div style={{ width: w, height: h, borderRadius: 4, background: 'linear-gradient(90deg,#F1F5F9 0%,#E2E8F0 50%,#F1F5F9 100%)' }} />
}

function ErrorBlock({ onRetry }) {
  return (
    <div style={{ padding: '14px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 10, display: 'flex', alignItems: 'flex-start', gap: 12 }}>
      <AlertIcon />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: '#B91C1C' }}>Не удалось загрузить данные</div>
        <div style={{ fontSize: 13, color: '#B91C1C', marginTop: 2 }}>Проверьте соединение с сервером.</div>
      </div>
      <button onClick={onRetry} style={btnSecondary}><RefreshIcon /> Повторить</button>
    </div>
  )
}

// ── InlineModal ───────────────────────────────────────────────────────────────

function InlineModal({ open, onClose, title, size = 520, children, footer }) {
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
          <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A' }}>{title}</div>
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

const mField = { marginBottom: 16 }
const mLabel = { fontSize: 13, fontWeight: 500, color: '#334155', marginBottom: 6, display: 'block' }
const mInput = { height: 40, border: '1px solid #CBD5E1', borderRadius: 8, padding: '0 12px', fontSize: 14, color: '#0F172A', background: '#FFF', width: '100%', fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box' }

function MField({ label, required, opt, children }) {
  return (
    <div style={mField}>
      <label style={mLabel}>
        {label}
        {required && <span style={{ color: '#DC2626', marginLeft: 2 }}>*</span>}
        {opt && <span style={{ color: '#94A3B8', fontWeight: 400, fontSize: 12, marginLeft: 4 }}>— {opt}</span>}
      </label>
      {children}
    </div>
  )
}

function MInput({ ...props }) {
  return <input style={mInput} {...props} />
}
function MTextarea({ ...props }) {
  return <textarea style={{ ...mInput, height: 'auto', minHeight: 72, padding: '10px 12px', resize: 'none' }} {...props} />
}

// ── Styles ────────────────────────────────────────────────────────────────────

const thStyle = { fontSize: 11, fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '12px 16px', background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }
const tdStyle = { padding: '13px 16px', fontSize: 14, color: '#0F172A' }

const btnPrimary = { display: 'inline-flex', alignItems: 'center', gap: 8, height: 38, padding: '0 16px', borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: 'pointer', background: '#1E293B', color: '#FFF', border: '1px solid transparent', fontFamily: 'inherit' }
const btnSecondary = { display: 'inline-flex', alignItems: 'center', gap: 8, height: 38, padding: '0 16px', borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: 'pointer', background: '#FFF', color: '#1E293B', border: '1px solid #CBD5E1', fontFamily: 'inherit' }

function btnAction(bg, color, border) {
  return { display: 'inline-flex', alignItems: 'center', gap: 6, height: 34, padding: '0 12px', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer', background: bg, color, border: `1px solid ${border}`, fontFamily: 'inherit' }
}

// ── Icons ─────────────────────────────────────────────────────────────────────

function PlusIcon()    { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><line x1="12" y1="5" x2="12" y2="19"/></svg> }
function CloseIcon()   { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg> }
function PencilIcon()  { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg> }
function TrashIcon()   { return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg> }
function ChevronDownIcon() { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6"/></svg> }
function AlertIcon()   { return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="13"/><circle cx="12" cy="16" r="0.5"/></svg> }
function RefreshIcon() { return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><polyline points="21 3 21 8 16 8"/></svg> }
function PauseIcon()   { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> }
function PlayIcon()    { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg> }
