import { useState, useEffect, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { format, differenceInCalendarDays } from 'date-fns'
import api from '../api/client'
import { useAuth } from '../contexts/AuthContext'

// ── helpers ──────────────────────────────────────────────────────────────────

const TASK_STATUS_LABELS = {
  created:     'Создана',
  in_progress: 'В работе',
  stopped:     'Остановлена',
  completed:   'Завершена',
  closed:      'Закрыта',
}

const TASK_TYPE_LABELS = {
  order_task: 'Под заказ',
  stock_task: 'В запас',
}

function fmtDate(iso) {
  if (!iso) return '—'
  try { return format(new Date(String(iso).slice(0, 10)), 'dd.MM.yyyy') } catch { return String(iso) }
}

function fmtDateTime(iso) {
  if (!iso) return '—'
  try { return format(new Date(iso), 'dd.MM.yyyy · HH:mm') } catch { return String(iso) }
}

function taskNumber(id) {
  return `T-26-${String(id).padStart(4, '0')}`
}

function isOverdue(task) {
  if (['completed', 'closed'].includes(task.status)) return false
  const deadline = new Date(String(task.deadline).slice(0, 10))
  const today = new Date(new Date().toDateString())
  return deadline < today
}

function overdueDays(task) {
  const deadline = new Date(String(task.deadline).slice(0, 10))
  const today = new Date(new Date().toDateString())
  return differenceInCalendarDays(today, deadline)
}

// ── API fetchers ──────────────────────────────────────────────────────────────

async function fetchTasks() {
  const { data } = await api.get('/tasks')
  return data
}

async function fetchTaskDrawer(id) {
  const { data } = await api.get(`/tasks/${id}/drawer`)
  return data
}

async function fetchProducts() {
  try {
    const { data } = await api.get('/references/products')
    return data
  } catch { return [] }
}

async function fetchUsers() {
  try {
    const { data } = await api.get('/users')
    return data
  } catch { return [] }
}

async function fetchRawMaterials() {
  try {
    const { data } = await api.get('/references/raw-materials')
    return data
  } catch { return [] }
}

async function fetchOrders() {
  try {
    const { data } = await api.get('/orders')
    return data
  } catch { return [] }
}

// ── page component ────────────────────────────────────────────────────────────

export default function Tasks() {
  const { hasRole } = useAuth()
  const isDirector = hasRole('director')
  const qc = useQueryClient()

  const [selectedId, setSelectedId] = useState(null)
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterExecutor, setFilterExecutor] = useState('all')
  const [filterType, setFilterType] = useState('all')
  const [createOpen, setCreateOpen]   = useState(false)
  const [stopOpen, setStopOpen]       = useState(false)
  const [resumeOpen, setResumeOpen]   = useState(false)
  const [completeOpen, setCompleteOpen] = useState(false)
  const [reassignOpen, setReassignOpen] = useState(false)

  const { data: tasks = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['tasks'],
    queryFn: fetchTasks,
  })

  const { data: products = [] } = useQuery({ queryKey: ['products'], queryFn: fetchProducts })
  const { data: users = [] }    = useQuery({ queryKey: ['users'],    queryFn: fetchUsers })
  const { data: rawMaterials = [] } = useQuery({ queryKey: ['raw-materials'], queryFn: fetchRawMaterials })
  const { data: orders = [] }   = useQuery({ queryKey: ['orders'],   queryFn: fetchOrders })

  const { data: drawer } = useQuery({
    queryKey: ['task-drawer', selectedId],
    queryFn: () => fetchTaskDrawer(selectedId),
    enabled: !!selectedId,
    retry: false,
  })

  const productMap     = useMemo(() => Object.fromEntries(products.map(p => [p.id, p])), [products])
  const userMap        = useMemo(() => Object.fromEntries(users.map(u => [u.id, u])), [users])
  const rawMaterialMap = useMemo(() => Object.fromEntries(rawMaterials.map(m => [m.name, m])), [rawMaterials])
  const orderMap       = useMemo(() => Object.fromEntries(orders.map(o => [o.id, o])), [orders])

  const productionUsers = useMemo(() =>
    users.filter(u => u.is_active && (u.roles?.includes('production') || u.roles?.includes('director'))), [users])

  const filtersActive = filterStatus !== 'all' || (isDirector && filterExecutor !== 'all') || filterType !== 'all'
  const resetFilters = () => { setFilterStatus('all'); setFilterExecutor('all'); setFilterType('all') }

  const filtered = tasks.filter(t => {
    if (filterStatus !== 'all' && t.status !== filterStatus) return false
    if (isDirector && filterExecutor !== 'all' && String(t.executor_id) !== filterExecutor) return false
    if (filterType !== 'all' && t.task_type !== filterType) return false
    return true
  })

  const selectedTask = drawer?.task ?? tasks.find(t => t.id === selectedId) ?? null

  const doAction = async (taskId, endpoint, body) => {
    try {
      if (body !== undefined) await api.post(`/tasks/${taskId}/${endpoint}`, body)
      else await api.post(`/tasks/${taskId}/${endpoint}`)
    } catch { /* ignore */ }
    qc.invalidateQueries({ queryKey: ['tasks'] })
    qc.invalidateQueries({ queryKey: ['task-drawer', taskId] })
  }

  const handleDelete = async (taskId) => {
    if (!window.confirm('Удалить задачу?')) return
    try { await api.delete(`/tasks/${taskId}`) } catch { /* ignore */ }
    qc.setQueryData(['tasks'], prev => prev?.filter(t => t.id !== taskId))
    setSelectedId(null)
  }

  const handleReassign = async (taskId, executorId) => {
    try { await api.patch(`/tasks/${taskId}/assignee`, { executor_id: executorId }) } catch { /* ignore */ }
    qc.invalidateQueries({ queryKey: ['tasks'] })
    qc.invalidateQueries({ queryKey: ['task-drawer', taskId] })
  }

  return (
    <div style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>

        {/* Header */}
        <div style={{ padding: '24px 32px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexShrink: 0 }}>
          <div>
            <div style={{ fontSize: 24, fontWeight: 500, color: '#0F172A' }}>Производственные задачи</div>
            {!isDirector && <div style={{ fontSize: 13, color: '#64748B', marginTop: 4 }}>Только ваши задачи</div>}
          </div>
          {isDirector && (
            <button onClick={() => setCreateOpen(true)} style={btnPrimary}>
              <PlusIcon /> Создать задачу
            </button>
          )}
        </div>

        {/* Filters */}
        <div style={{ padding: '16px 32px 0', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', flexShrink: 0 }}>
          <FilterChip label="Статус" value={filterStatus === 'all' ? 'Все активные' : TASK_STATUS_LABELS[filterStatus]}>
            <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}>
              <option value="all">Все активные</option>
              {Object.entries(TASK_STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </FilterChip>

          {isDirector && (
            <FilterChip label="Исполнитель" value={filterExecutor === 'all' ? 'Любой' : (userMap[Number(filterExecutor)]?.full_name ?? 'Исполнитель')}>
              <select value={filterExecutor} onChange={e => setFilterExecutor(e.target.value)} style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}>
                <option value="all">Любой</option>
                {productionUsers.map(u => <option key={u.id} value={String(u.id)}>{u.full_name}</option>)}
              </select>
            </FilterChip>
          )}

          <FilterChip label="Тип" value={filterType === 'all' ? 'Все' : TASK_TYPE_LABELS[filterType]}>
            <select value={filterType} onChange={e => setFilterType(e.target.value)} style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}>
              <option value="all">Все</option>
              <option value="order_task">Под заказ</option>
              <option value="stock_task">В запас</option>
            </select>
          </FilterChip>

          {filtersActive && (
            <button onClick={resetFilters} style={{ fontSize: 13, color: '#475569', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              Сброс
            </button>
          )}
        </div>

        {/* Table */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 32px 0' }}>
          {isLoading ? (
            <TaskSkeleton isDirector={isDirector} />
          ) : isError ? (
            <ErrorBlock onRetry={refetch} />
          ) : tasks.length === 0 ? (
            <EmptyState isDirector={isDirector} onCreate={() => setCreateOpen(true)} />
          ) : filtered.length === 0 ? (
            <EmptyFiltered onReset={resetFilters} />
          ) : (
            <TaskTable
              tasks={filtered}
              selectedId={selectedId}
              onRowClick={id => setSelectedId(prev => prev === id ? null : id)}
              productMap={productMap}
              userMap={userMap}
              isDirector={isDirector}
            />
          )}
        </div>
      </div>

      {/* Drawer */}
      {selectedId && selectedTask && (
        <aside style={{
          position: 'absolute', right: 0, top: 0, bottom: 0, width: 480,
          background: '#FFFFFF', borderLeft: '1px solid #E2E8F0',
          display: 'flex', flexDirection: 'column', overflow: 'hidden', zIndex: 10,
        }}>
          <TaskDrawerContent
            task={selectedTask}
            drawer={drawer}
            productMap={productMap}
            userMap={userMap}
            orderMap={orderMap}
            isDirector={isDirector}
            onClose={() => setSelectedId(null)}
            onStart={async () => { await doAction(selectedTask.id, 'start') }}
            onStop={() => setStopOpen(true)}
            onResume={() => setResumeOpen(true)}
            onComplete={() => setCompleteOpen(true)}
            onClose_task={async () => { await doAction(selectedTask.id, 'close') }}
            onReassign={() => setReassignOpen(true)}
            onDelete={() => handleDelete(selectedTask.id)}
          />
        </aside>
      )}

      {/* Modals */}
      {isDirector && (
        <CreateTaskModal
          open={createOpen}
          onClose={() => setCreateOpen(false)}
          onCreate={() => { qc.invalidateQueries({ queryKey: ['tasks'] }); setCreateOpen(false) }}
          products={products}
          users={productionUsers}
        />
      )}

      {selectedTask && (
        <>
          <StopModal
            open={stopOpen}
            task={selectedTask}
            productMap={productMap}
            onClose={() => setStopOpen(false)}
            onSave={async (reason) => {
              await doAction(selectedTask.id, 'stop', { reason })
              setStopOpen(false)
            }}
          />
          <ResumeConfirmModal
            open={resumeOpen}
            task={selectedTask}
            productMap={productMap}
            onClose={() => setResumeOpen(false)}
            onConfirm={async () => {
              await doAction(selectedTask.id, 'resume')
              setResumeOpen(false)
            }}
          />
          <CompleteModal
            open={completeOpen}
            task={selectedTask}
            drawer={drawer}
            productMap={productMap}
            rawMaterialMap={rawMaterialMap}
            onClose={() => setCompleteOpen(false)}
            onSave={async (payload) => {
              await doAction(selectedTask.id, 'complete', payload)
              setCompleteOpen(false)
            }}
          />
          {isDirector && (
            <ReassignModal
              open={reassignOpen}
              task={selectedTask}
              drawer={drawer}
              productMap={productMap}
              userMap={userMap}
              users={productionUsers}
              onClose={() => setReassignOpen(false)}
              onSave={async (executorId) => {
                await handleReassign(selectedTask.id, executorId)
                setReassignOpen(false)
              }}
            />
          )}
        </>
      )}
    </div>
  )
}

// ── TaskTable ─────────────────────────────────────────────────────────────────

function TaskTable({ tasks, selectedId, onRowClick, productMap, userMap, isDirector }) {
  const cols = isDirector ? '2fr 100px 130px 130px 60px 160px' : '2fr 100px 130px 130px 60px'
  const today = new Date(new Date().toDateString())

  return (
    <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden', marginBottom: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: cols }}>
        <div style={thStyle}>Продукт</div>
        <div style={thStyle}>Кол-во шт.</div>
        <div style={thStyle}>Дедлайн</div>
        <div style={thStyle}>Статус</div>
        <div style={thStyle}>🔗</div>
        {isDirector && <div style={thStyle}>Исполнитель</div>}
      </div>
      {tasks.map((task, idx) => {
        const overdue = isOverdue(task)
        const days    = overdue ? overdueDays(task) : 0
        const product = productMap[task.product_id]
        const executor = userMap[task.executor_id]
        const units = task.quantity
        const deadlineDate = new Date(String(task.deadline).slice(0, 10))
        const isToday = deadlineDate.getTime() === today.getTime()
        const selected = selectedId === task.id

        return (
          <div
            key={task.id}
            onClick={() => onRowClick(task.id)}
            style={{
              display: 'grid', gridTemplateColumns: cols, alignItems: 'center',
              cursor: 'pointer',
              background: selected ? '#F1F5F9' : 'transparent',
              borderBottom: idx < tasks.length - 1 ? '1px solid #F1F5F9' : 'none',
            }}
            onMouseEnter={e => { if (!selected) e.currentTarget.style.background = '#FAFBFC' }}
            onMouseLeave={e => { e.currentTarget.style.background = selected ? '#F1F5F9' : 'transparent' }}
          >
            <div style={{
              ...tdStyle,
              boxShadow: overdue ? 'inset 4px 0 0 0 #DC2626' : 'none',
              paddingLeft: overdue ? 20 : 16,
            }}>
              {product?.name ?? `Продукт #${task.product_id}`}
            </div>
            <div style={tdStyle}>{units}</div>
            <div style={tdStyle}>
              {overdue
                ? <span style={{ color: '#B91C1C', fontWeight: 500, fontSize: 11 }}>Просрочена {days} дн.</span>
                : isToday
                ? <span>{fmtDate(task.deadline)} <span style={{ color: '#B45309', fontSize: 11 }}>(сегодня)</span></span>
                : fmtDate(task.deadline)
              }
            </div>
            <div style={tdStyle}><TaskBadge status={task.status} /></div>
            <div style={{ ...tdStyle, color: '#64748B' }}>
              {task.order_id ? <LinkIcon /> : null}
            </div>
            {isDirector && (
              <div style={{ ...tdStyle, color: '#475569', fontSize: 13 }}>
                {executor?.full_name ?? `#${task.executor_id}`}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

const thStyle = {
  fontSize: 12, fontWeight: 500, color: '#64748B', textTransform: 'uppercase',
  letterSpacing: '0.06em', padding: '12px 16px',
  background: '#F8FAFC', borderBottom: '1px solid #E2E8F0',
}
const tdStyle = { padding: '14px 16px', fontSize: 14, color: '#0F172A' }

function TaskBadge({ status }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', padding: '3px 10px',
      borderRadius: 999, fontSize: 12, fontWeight: 500,
      border: '1px solid #CBD5E1', background: '#F1F5F9', color: '#475569',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#94A3B8', marginRight: 6, flexShrink: 0 }} />
      {TASK_STATUS_LABELS[status] ?? status}
    </span>
  )
}

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

// ── Drawer ────────────────────────────────────────────────────────────────────

function TaskDrawerContent({ task, drawer, productMap, userMap, orderMap, isDirector, onClose, onStart, onStop, onResume, onComplete, onClose_task, onReassign, onDelete }) {
  const productName  = drawer?.product_name ?? productMap[task.product_id]?.name ?? `Продукт #${task.product_id}`
  const executorName = drawer?.executor_name ?? userMap[task.executor_id]?.full_name ?? `#${task.executor_id}`
  const order        = task.order_id ? orderMap[task.order_id] : null

  const canStart    = task.status === 'created'
  const canStop     = task.status === 'in_progress'
  const canResume   = task.status === 'stopped'
  const canComplete = task.status === 'in_progress'
  const canCloseT   = task.status === 'completed' && isDirector
  const showReassign = isDirector && !['closed'].includes(task.status)
  const showDelete   = isDirector

  const subtitle = task.order_id
    ? `${taskNumber(task.id)} · Под заказ ${order ? `№ ${order.number}` : `#${task.order_id}`}${order?.customer_name ? ` (${order.customer_name.split(',')[0]})` : ''}`
    : taskNumber(task.id)

  return (
    <>
      {/* Header */}
      <div style={{ padding: '18px 24px 14px', borderBottom: '1px solid #F1F5F9', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {productName}
          </div>
          <TaskBadge status={task.status} />
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748B', display: 'flex', alignItems: 'center', width: 28, height: 28, justifyContent: 'center', flexShrink: 0 }}>
            <CloseIcon />
          </button>
        </div>
        <div style={{ fontSize: 12, color: '#64748B', marginTop: 6 }}>{subtitle}</div>
      </div>

      {/* Actions */}
      <div style={{ padding: '12px 24px', display: 'flex', gap: 6, flexWrap: 'wrap', borderBottom: '1px solid #F1F5F9', flexShrink: 0, alignItems: 'center' }}>
        {canStart && (
          <button onClick={onStart} style={btnAction('#1E293B', '#FFF', '#1E293B')}>
            <PlayIcon /> Начать
          </button>
        )}
        {canStop && (
          <button onClick={onStop} style={btnAction('#FFF', '#B45309', '#FCD34D')}>
            <StopIcon /> Остановить
          </button>
        )}
        {canComplete && (
          <button onClick={onComplete} style={btnAction('#047857', '#FFF', '#047857')}>
            <CheckIcon /> Завершить
          </button>
        )}
        {canResume && (
          <button onClick={onResume} style={btnAction('#1E293B', '#FFF', '#1E293B')}>
            <PlayIcon /> Возобновить
          </button>
        )}
        {canCloseT && (
          <button onClick={onClose_task} style={btnAction('#047857', '#FFF', '#047857')}>
            <CheckIcon /> Закрыть задачу
          </button>
        )}

        {(showReassign || showDelete) && (
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
            {showReassign && (
              <button onClick={onReassign} style={btnAction('#FFF', '#1E293B', '#CBD5E1')}>
                <UserIcon /> Сменить исп.
              </button>
            )}
            {showDelete && (
              <button onClick={onDelete} style={btnAction('#FFF', '#B91C1C', '#FCA5A5')}>
                <TrashIcon />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 24px 24px' }}>
        {/* Completed: show report first */}
        {task.status === 'completed' && drawer?.completion && (
          <DrSection title="Отчёт исполнителя">
            <div style={{ fontSize: 11, color: '#64748B', marginBottom: 8 }}>
              Сдан {executorName} · {fmtDateTime(task.actual_end_at)}
            </div>
            <div style={{ background: '#F0FDF4', border: '1px solid #86EFAC', borderRadius: 8, padding: '12px 14px', marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontSize: 13 }}>
                <span style={{ color: '#166534' }}>Факт. выпуск</span>
                <span style={{ color: '#14532D', fontWeight: 500 }}>{drawer.completion.actual_quantity} шт.</span>
              </div>
              {drawer.completion.consumptions.map((c, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontSize: 13 }}>
                  <span style={{ color: '#166534' }}>{c.raw_material_name}</span>
                  <span style={{ color: '#14532D', fontWeight: 500 }}>
                    {String(c.actual_qty)}
                    <span style={{ fontSize: 11, color: '#166534', marginLeft: 4 }}>(план: {String(c.planned_qty)})</span>
                  </span>
                </div>
              ))}
            </div>
            {drawer.completion.comment && (
              <div style={{ fontSize: 13, color: '#334155' }}>
                <strong style={{ fontWeight: 500 }}>Комментарий:</strong> {drawer.completion.comment}
              </div>
            )}
          </DrSection>
        )}

        {/* Основное */}
        <DrSection title="Основное">
          <DrRow label="Кол-во" value={`${task.quantity} шт.`} />
          <DrRow label="Исполнитель" value={executorName} />
          {task.actual_start_at && <DrRow label="Дата начала" value={fmtDateTime(task.actual_start_at)} />}
          <DrRow
            label="Дедлайн"
            value={fmtDate(task.deadline)}
            valueStyle={isOverdue(task) ? { color: '#B45309' } : undefined}
          />
          <DrRow label="Тип" value={TASK_TYPE_LABELS[task.task_type] ?? task.task_type} />
        </DrSection>

        {/* Сырьё */}
        {drawer?.reservations?.length > 0 && task.status !== 'completed' && (
          <DrSection title="Сырьё (плановая потребность)">
            <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
              <tbody>
                {drawer.reservations.map((r, i) => (
                  <tr key={i}>
                    <td style={{ padding: '6px 0', borderBottom: '1px solid #F8FAFC' }}>{r.raw_material_name}</td>
                    <td style={{ padding: '6px 0', borderBottom: '1px solid #F8FAFC', textAlign: 'right' }}>{String(r.quantity)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </DrSection>
        )}

        {/* История остановок */}
        <DrSection title="История остановок">
          {drawer?.stops?.length > 0 ? (
            drawer.stops.map((s, i) => (
              <div key={i} style={{ background: '#FFFBEB', border: '1px solid #FCD34D', borderRadius: 8, padding: '10px 12px', marginBottom: 8, fontSize: 13 }}>
                <div style={{ fontWeight: 500, color: '#B45309' }}>{s.reason}</div>
                <div style={{ fontSize: 11, color: '#92400E', marginTop: 4 }}>
                  {fmtDateTime(s.stopped_at)}{s.resumed_at ? ` → ${fmtDateTime(s.resumed_at)}` : ' (активна)'}
                </div>
              </div>
            ))
          ) : (
            <div style={{ fontSize: 12, color: '#94A3B8' }}>Остановок не было</div>
          )}
        </DrSection>

        {/* Связь с заказом */}
        {task.order_id && (
          <DrSection title="Связь с заказом">
            <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: '10px 12px', fontSize: 13 }}>
              {order ? (
                <>
                  <div style={{ fontWeight: 500, color: '#0F172A' }}>Заказ № {order.number} — {order.customer_name}</div>
                  <div style={{ fontSize: 11, color: '#64748B', marginTop: 4 }}>
                    Дата доставки {fmtDate(order.delivery_date)}
                    {order.delivery_user_name && ` · Курьер ${order.delivery_user_name}`}
                  </div>
                </>
              ) : (
                <div style={{ color: '#64748B' }}>Заказ #{task.order_id}</div>
              )}
            </div>
          </DrSection>
        )}
      </div>
    </>
  )
}

function DrSection({ title, children }) {
  return (
    <div style={{ padding: '14px 0', borderBottom: '1px solid #F1F5F9' }}>
      <div style={{ fontSize: 13, fontWeight: 500, color: '#0F172A', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{title}</div>
      {children}
    </div>
  )
}
function DrRow({ label, value, valueStyle }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13 }}>
      <span style={{ color: '#64748B' }}>{label}</span>
      <span style={{ color: '#0F172A', fontWeight: 500, textAlign: 'right', maxWidth: '60%', ...valueStyle }}>{value}</span>
    </div>
  )
}

// ── States ────────────────────────────────────────────────────────────────────

function TaskSkeleton({ isDirector }) {
  const cols = isDirector ? '2fr 100px 130px 130px 60px 160px' : '2fr 100px 130px 130px 60px'
  return (
    <div style={{ background: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: 10, overflow: 'hidden' }}>
      <div style={{ display: 'grid', gridTemplateColumns: cols }}>
        {(isDirector ? ['Продукт', 'Кол-во шт.', 'Дедлайн', 'Статус', '🔗', 'Исполнитель'] : ['Продукт', 'Кол-во шт.', 'Дедлайн', 'Статус', '🔗']).map((h, i) => (
          <div key={i} style={thStyle}>{h}</div>
        ))}
      </div>
      {[70, 55, 80, 60, 75].map((w, i) => (
        <div key={i} style={{ display: 'grid', gridTemplateColumns: cols, borderBottom: '1px solid #F1F5F9' }}>
          <div style={tdStyle}><Skel w={`${w}%`} /></div>
          <div style={tdStyle}><Skel w={50} /></div>
          <div style={tdStyle}><Skel w={80} /></div>
          <div style={tdStyle}><Skel w={70} h={20} rounded /></div>
          <div style={tdStyle} />
          {isDirector && <div style={tdStyle}><Skel w={90} /></div>}
        </div>
      ))}
    </div>
  )
}

function Skel({ w, h = 14, rounded = false }) {
  return (
    <div style={{ width: typeof w === 'number' ? w : w, height: h, borderRadius: rounded ? 999 : 4, background: 'linear-gradient(90deg,#F1F5F9 0%,#E2E8F0 50%,#F1F5F9 100%)', backgroundSize: '200% 100%' }} />
  )
}

function ErrorBlock({ onRetry }) {
  return (
    <div style={{ padding: '14px 16px', background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 10, display: 'flex', alignItems: 'flex-start', gap: 12 }}>
      <AlertIcon />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: '#B91C1C' }}>Не удалось загрузить задачи</div>
        <div style={{ fontSize: 13, color: '#B91C1C', marginTop: 2 }}>Проверьте соединение с сервером.</div>
      </div>
      <button onClick={onRetry} style={btnSecondary}><RefreshIcon /> Повторить</button>
    </div>
  )
}

function EmptyState({ isDirector, onCreate }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '80px 40px', textAlign: 'center' }}>
      <div style={{ width: 96, height: 96, borderRadius: '50%', background: '#F1F5F9', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20, color: '#94A3B8' }}>
        <FactoryIcon />
      </div>
      <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A', marginBottom: 6 }}>Задач пока нет</div>
      <div style={{ fontSize: 14, color: '#64748B', marginBottom: 18, maxWidth: 360 }}>
        {isDirector ? 'Создайте первую производственную задачу.' : 'Вам ещё не назначено ни одной задачи.'}
      </div>
      {isDirector && <button onClick={onCreate} style={btnPrimary}><PlusIcon /> Создать задачу</button>}
    </div>
  )
}

function EmptyFiltered({ onReset }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 40px', textAlign: 'center' }}>
      <div style={{ width: 96, height: 96, borderRadius: '50%', background: '#F1F5F9', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20, color: '#94A3B8' }}>
        <FactoryIcon />
      </div>
      <div style={{ fontSize: 18, fontWeight: 500, color: '#0F172A', marginBottom: 6 }}>Ничего не найдено</div>
      <div style={{ fontSize: 14, color: '#64748B', marginBottom: 18, maxWidth: 360 }}>По выбранным фильтрам задач не найдено.</div>
      <button onClick={onReset} style={{ fontSize: 14, color: '#1E293B', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer' }}>Сбросить фильтры</button>
    </div>
  )
}

// ── InlineModal ───────────────────────────────────────────────────────────────

function InlineModal({ open, onClose, title, subtitle, size = 520, children, footer }) {
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

const mField = { marginBottom: 16 }
const mLabel = { fontSize: 13, fontWeight: 500, color: '#334155', marginBottom: 6, display: 'block' }
const mInput = { height: 40, border: '1px solid #CBD5E1', borderRadius: 8, padding: '0 12px', fontSize: 14, color: '#0F172A', background: '#FFF', width: '100%', fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box' }
const mInputRo = { ...mInput, background: '#F8FAFC', color: '#475569' }

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

function MInput({ readOnly, ...props }) {
  return <input style={readOnly ? mInputRo : mInput} readOnly={readOnly} {...props} />
}
function MSelect({ children, ...props }) {
  return <select style={mInput} {...props}>{children}</select>
}
function MTextarea({ ...props }) {
  return <textarea style={{ ...mInput, height: 'auto', minHeight: 80, padding: '10px 12px', resize: 'none' }} {...props} />
}

// ── CreateTaskModal (MOD-04) ──────────────────────────────────────────────────

function CreateTaskModal({ open, onClose, onCreate, products, users }) {
  const [form, setForm] = useState({
    product_id: '', quantity: '', executor_id: '', start_date: '', deadline: '', comment: '',
  })
  const [submitted, setSubmitted] = useState(false)
  const [saving, setSaving] = useState(false)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  useEffect(() => {
    if (open) {
      setForm({ product_id: '', quantity: '', executor_id: '', start_date: '', deadline: '', comment: '' })
      setSubmitted(false)
    }
  }, [open])

  const product = products.find(p => String(p.id) === String(form.product_id))
  const isValid = form.product_id && form.quantity > 0 && form.executor_id && form.start_date && form.deadline

  const handleSave = async () => {
    setSubmitted(true)
    if (!isValid) return
    setSaving(true)
    try {
      await api.post('/tasks', {
        product_id:  Number(form.product_id),
        quantity:    Number(form.quantity),
        executor_id: Number(form.executor_id),
        start_date:  form.start_date,
        deadline:    form.deadline,
        task_type:   'stock_task',
        comment:     form.comment || null,
      })
    } catch { /* ignore */ }
    setSaving(false)
    onCreate()
  }

  return (
    <InlineModal open={open} onClose={onClose} title="Новая производственная задача" size={640}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} disabled={saving} style={{ ...btnPrimary, opacity: saving ? 0.7 : 1 }}>
          {saving ? 'Создание…' : 'Создать задачу'}
        </button>
      </>}
    >
      <MField label="Продукт" required>
        <MSelect value={form.product_id} onChange={e => set('product_id', e.target.value)}>
          <option value="">Выберите продукт</option>
          {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </MSelect>
      </MField>

      <MField label="Количество (шт.)" required>
        <MInput type="number" min="1" value={form.quantity} onChange={e => set('quantity', e.target.value)} placeholder="0" />
      </MField>

      <MField label="Исполнитель" required>
        <MSelect value={form.executor_id} onChange={e => set('executor_id', e.target.value)}>
          <option value="">Выберите исполнителя</option>
          {users.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}
        </MSelect>
      </MField>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <MField label="Дата начала" required>
          <MInput type="date" value={form.start_date} onChange={e => set('start_date', e.target.value)} />
        </MField>
        <MField label="Дедлайн" required>
          <MInput type="date" value={form.deadline} onChange={e => set('deadline', e.target.value)} />
        </MField>
      </div>

      <MField label="Комментарий" opt="опц.">
        <MTextarea rows={2} value={form.comment} onChange={e => set('comment', e.target.value)} placeholder="Особые указания для исполнителя" />
      </MField>

      {/* Raw material preview */}
      {product?.recipe?.length > 0 && form.quantity > 0 && (
        <div style={{ marginTop: 4, border: '1px solid #E2E8F0', borderRadius: 8, padding: 14, background: '#F8FAFC' }}>
          <div style={{ fontSize: 12, fontWeight: 500, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>
            Плановая потребность сырья
          </div>
          <table style={{ width: '100%', fontSize: 13 }}>
            <tbody>
              {product.recipe.map((r, i) => {
                const qty = (Number(form.quantity) * r.consumption_per_unit).toFixed(2)
                return (
                  <tr key={i}>
                    <td style={{ padding: '5px 0', borderBottom: '1px solid #EEF2F6' }}>
                      Материал #{r.raw_material_id}
                    </td>
                    <td style={{ padding: '5px 0', borderBottom: '1px solid #EEF2F6', textAlign: 'right', fontWeight: 500 }}>{qty}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </InlineModal>
  )
}

// ── StopModal (MOD-05) ────────────────────────────────────────────────────────

function StopModal({ open, task, productMap, onClose, onSave }) {
  const [reason, setReason] = useState('')
  const productName = productMap[task.product_id]?.name ?? `#${task.product_id}`

  useEffect(() => { if (open) setReason('') }, [open])

  return (
    <InlineModal open={open} onClose={onClose} title="Остановка задачи" subtitle={`${productName} · ${taskNumber(task.id)}`} size={440}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button
          onClick={() => onSave(reason)}
          disabled={!reason.trim()}
          style={{ ...btnAction('#B45309', '#FFF', '#B45309'), opacity: reason.trim() ? 1 : 0.5, cursor: reason.trim() ? 'pointer' : 'not-allowed' }}
        >
          <StopIcon /> Остановить задачу
        </button>
      </>}
    >
      <MField label="Причина остановки" required>
        <MTextarea rows={3} value={reason} onChange={e => setReason(e.target.value)} placeholder="Например: поломка дозатора, ждём наладчика" />
        <div style={{ fontSize: 12, color: '#64748B', marginTop: 8 }}>
          Причина фиксируется в истории задачи. Статус сменится на «Остановлена».
        </div>
      </MField>
    </InlineModal>
  )
}

// ── ResumeConfirmModal (MOD-05r) ──────────────────────────────────────────────

function ResumeConfirmModal({ open, task, productMap, onClose, onConfirm }) {
  const productName = productMap[task.product_id]?.name ?? `#${task.product_id}`

  return (
    <InlineModal open={open} onClose={onClose} title="Возобновить задачу?" subtitle={`${productName} · ${taskNumber(task.id)}`} size={440}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={onConfirm} style={btnPrimary}>Возобновить</button>
      </>}
    >
      <div style={{ textAlign: 'center', padding: '8px 0 16px' }}>
        <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#FFFBEB', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', color: '#B45309' }}>
          <PlayIcon size={26} />
        </div>
        <div style={{ fontSize: 17, fontWeight: 500, color: '#0F172A', marginBottom: 8 }}>Возобновить задачу?</div>
        <div style={{ fontSize: 14, color: '#64748B', lineHeight: '21px', maxWidth: 320, margin: '0 auto' }}>
          Статус сменится со «Остановлена» на «В работе». Исполнитель получит уведомление.
        </div>
      </div>
    </InlineModal>
  )
}

// ── CompleteModal (MOD-06) ────────────────────────────────────────────────────

function CompleteModal({ open, task, drawer, productMap, rawMaterialMap, onClose, onSave }) {
  const productName = productMap[task.product_id]?.name ?? `#${task.product_id}`

  const buildRows = useCallback(() => {
    if (!drawer?.reservations?.length) return []
    const grouped = {}
    drawer.reservations.forEach(r => {
      if (!grouped[r.raw_material_name]) grouped[r.raw_material_name] = { name: r.raw_material_name, planned: 0 }
      grouped[r.raw_material_name].planned += Number(r.quantity)
    })
    return Object.values(grouped).map(g => ({
      name: g.name,
      raw_material_id: rawMaterialMap[g.name]?.id ?? null,
      planned: g.planned,
      actual: String(g.planned),
      waste: '',
    }))
  }, [drawer, rawMaterialMap])

  const [actualQty, setActualQty] = useState('')
  const [rows, setRows] = useState([])
  const [comment, setComment] = useState('')

  useEffect(() => {
    if (open) {
      setActualQty(String(task.quantity))
      setRows(buildRows())
      setComment('')
    }
  }, [open, task.quantity, buildRows])

  const setRow = (idx, field, val) =>
    setRows(prev => prev.map((r, i) => i === idx ? { ...r, [field]: val } : r))

  const handleSave = async () => {
    const payload = {
      actual_quantity: Number(actualQty) || task.quantity,
      consumptions: rows
        .filter(r => r.raw_material_id != null && r.actual)
        .map(r => ({
          raw_material_id: r.raw_material_id,
          actual_qty: r.actual,
          waste_qty: r.waste || null,
        })),
      comment: comment || null,
    }
    await onSave(payload)
  }

  return (
    <InlineModal open={open} onClose={onClose}
      title="Отчёт и завершение задачи"
      subtitle={`${productName} · ${taskNumber(task.id)} · план ${task.quantity} шт.`}
      size={640}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button onClick={handleSave} style={btnAction('#047857', '#FFF', '#047857')}>
          <CheckIcon /> Завершить задачу
        </button>
      </>}
    >
      <MField label="Фактически выпущено (шт.)" required>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <MInput type="number" min="0" value={actualQty} onChange={e => setActualQty(e.target.value)} style={{ ...mInput, maxWidth: 200 }} />
          <span style={{ fontSize: 13, color: '#64748B' }}>шт.</span>
        </div>
      </MField>

      {rows.length > 0 && (
        <MField label="Фактический расход сырья" required>
          <div style={{ border: '1px solid #E2E8F0', borderRadius: 8, overflow: 'hidden' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 90px 110px 110px', background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
              {['Сырьё', 'План', 'Факт', 'Брак (опц.)'].map((h, i) => (
                <div key={i} style={{ padding: '8px 10px', fontSize: 11, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</div>
              ))}
            </div>
            {rows.map((row, idx) => (
              <div key={idx} style={{ display: 'grid', gridTemplateColumns: '1.5fr 90px 110px 110px', alignItems: 'center', borderBottom: idx < rows.length - 1 ? '1px solid #F1F5F9' : 'none' }}>
                <div style={{ padding: '6px 10px', fontSize: 13 }}>{row.name}</div>
                <div style={{ padding: '6px 10px', fontSize: 13, color: '#64748B' }}>{row.planned}</div>
                <div style={{ padding: '4px 6px' }}>
                  <input type="number" step="0.001" value={row.actual} onChange={e => setRow(idx, 'actual', e.target.value)}
                    style={{ height: 32, border: '1px solid #CBD5E1', borderRadius: 6, padding: '0 8px', fontSize: 13, fontFamily: 'inherit', outline: 'none', width: '100%' }} />
                </div>
                <div style={{ padding: '4px 6px' }}>
                  <input type="number" step="0.001" value={row.waste} onChange={e => setRow(idx, 'waste', e.target.value)}
                    placeholder="0"
                    style={{ height: 32, border: '1px solid #CBD5E1', borderRadius: 6, padding: '0 8px', fontSize: 13, fontFamily: 'inherit', outline: 'none', width: '100%', color: row.waste ? '#0F172A' : '#94A3B8' }} />
                </div>
              </div>
            ))}
          </div>
        </MField>
      )}

      <MField label="Комментарий" opt="опц.">
        <MTextarea rows={2} value={comment} onChange={e => setComment(e.target.value)} placeholder="Партия прошла штатно…" />
      </MField>
      <div style={{ fontSize: 12, color: '#64748B', marginTop: 4 }}>
        После завершения резерв сырья снимется.
      </div>
    </InlineModal>
  )
}

// ── ReassignModal (MOD-07) ────────────────────────────────────────────────────

function ReassignModal({ open, task, drawer, productMap, userMap, users, onClose, onSave }) {
  const [executorId, setExecutorId] = useState('')
  const productName  = productMap[task.product_id]?.name ?? `#${task.product_id}`
  const currentName  = drawer?.executor_name ?? userMap[task.executor_id]?.full_name ?? `#${task.executor_id}`

  useEffect(() => { if (open) setExecutorId('') }, [open])

  return (
    <InlineModal open={open} onClose={onClose} title="Смена исполнителя" subtitle={`${productName} · ${taskNumber(task.id)}`} size={520}
      footer={<>
        <button onClick={onClose} style={btnSecondary}>Отмена</button>
        <button
          onClick={() => onSave(Number(executorId))}
          disabled={!executorId}
          style={{ ...btnPrimary, opacity: executorId ? 1 : 0.5, cursor: executorId ? 'pointer' : 'not-allowed' }}
        >
          <UserIcon /> Сменить исполнителя
        </button>
      </>}
    >
      <MField label="Текущий исполнитель">
        <MInput readOnly value={currentName} />
      </MField>
      <MField label="Новый исполнитель" required>
        <MSelect value={executorId} onChange={e => setExecutorId(e.target.value)}>
          <option value="">Выберите исполнителя</option>
          {users.filter(u => u.id !== task.executor_id).map(u => (
            <option key={u.id} value={u.id}>{u.full_name}</option>
          ))}
        </MSelect>
      </MField>
      <div style={{ fontSize: 12, color: '#64748B', marginTop: 4 }}>
        Прежний исполнитель получит уведомление в Telegram о снятии задачи.
      </div>
    </InlineModal>
  )
}

// ── Button / action styles ────────────────────────────────────────────────────

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

function btnAction(bg, color, border) {
  return {
    display: 'inline-flex', alignItems: 'center', gap: 8, height: 32, padding: '0 10px',
    borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer',
    background: bg, color, border: `1px solid ${border}`, fontFamily: 'inherit',
  }
}

// ── Icons ─────────────────────────────────────────────────────────────────────

function PlusIcon()      { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><line x1="12" y1="5" x2="12" y2="19"/></svg> }
function ChevronDownIcon(){ return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6"/></svg> }
function CloseIcon()     { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg> }
function TrashIcon()     { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg> }
function AlertIcon()     { return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="13"/><circle cx="12" cy="16" r="0.5"/></svg> }
function RefreshIcon()   { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><polyline points="21 3 21 8 16 8"/></svg> }
function LinkIcon()      { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg> }
function StopIcon()      { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="6" width="12" height="12" rx="1"/></svg> }
function PlayIcon({ size = 16 }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg> }
function CheckIcon()     { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg> }
function UserIcon()      { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg> }
function FactoryIcon()   { return <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21V11l5 3V11l5 3V11l5 3V21Z"/><path d="M3 21h18"/></svg> }
