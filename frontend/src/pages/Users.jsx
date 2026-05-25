import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useAuth } from '../contexts/AuthContext'

// ─── Config ───────────────────────────────────────────────────────────────────

const ROLES = [
  { value: 'director',   label: 'Директор' },
  { value: 'production', label: 'Производство' },
  { value: 'warehouse',  label: 'Склад' },
  { value: 'delivery',   label: 'Доставка' },
]

function roleName(r) { return ROLES.find(x => x.value === r)?.label ?? r }

// ─── Shared UI ────────────────────────────────────────────────────────────────

const controlStyle = {
  width: '100%', height: 40, padding: '0 12px',
  border: '1px solid #CBD5E1', borderRadius: 8,
  fontSize: 14, outline: 'none', boxSizing: 'border-box',
  fontFamily: 'inherit', color: '#0F172A', background: '#FFF',
}

function Field({ label, hint, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 500, color: '#334155', marginBottom: 6 }}>{label}</div>
      {children}
      {hint && <div style={{ fontSize: 11, color: '#94A3B8', marginTop: 4 }}>{hint}</div>}
    </div>
  )
}

function RoleTag({ role }) {
  return (
    <span style={{
      fontSize: 11, padding: '2px 8px', borderRadius: 4,
      background: '#F1F5F9', color: '#475569', border: '1px solid #E2E8F0',
      display: 'inline-flex', alignItems: 'center',
    }}>
      {roleName(role)}
    </span>
  )
}

function TelegramIndicator({ user }) {
  if (user.telegram_id) {
    return (
      <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 13, color: '#047857' }}>
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#059669', flexShrink: 0 }} />
        Привязан
      </span>
    )
  }
  if (user.telegram_username) {
    return (
      <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 13, color: '#B45309' }}>
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#D97706', flexShrink: 0 }} />
        Ожидает /start
      </span>
    )
  }
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 13, color: '#94A3B8' }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#CBD5E1', flexShrink: 0 }} />
      Не указан
    </span>
  )
}

function StatusBadge({ isActive }) {
  return isActive ? (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 10px', borderRadius: 999, fontSize: 12, fontWeight: 500, background: '#ECFDF5', border: '1px solid #86EFAC', color: '#047857' }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#059669' }} />
      Активен
    </span>
  ) : (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '3px 10px', borderRadius: 999, fontSize: 12, fontWeight: 500, background: '#F8FAFC', border: '1px dashed #CBD5E1', color: '#94A3B8' }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#CBD5E1' }} />
      Деактивирован
    </span>
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
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>{children}</div>
        <div style={{ padding: '16px 24px', borderTop: '1px solid #F1F5F9', display: 'flex', justifyContent: 'flex-end', gap: 10, flexShrink: 0 }}>
          {footer}
        </div>
      </div>
    </div>
  )
}

function RoleCheckboxes({ selected, onChange }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {ROLES.map(r => {
        const isOn = selected.includes(r.value)
        return (
          <label key={r.value} style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 14, color: '#0F172A' }}>
            <div
              style={{
                width: 18, height: 18, borderRadius: 4, flexShrink: 0,
                border: `2px solid ${isOn ? '#3B82F6' : '#CBD5E1'}`,
                background: isOn ? '#3B82F6' : '#FFF',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
              onClick={() => onChange(isOn ? selected.filter(x => x !== r.value) : [...selected, r.value])}
            >
              {isOn && <span style={{ color: '#FFF', fontSize: 11, fontWeight: 700, lineHeight: 1 }}>✓</span>}
            </div>
            {r.label}
          </label>
        )
      })}
    </div>
  )
}

function CreateUserModal({ onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ full_name: '', password: '', roles: [] })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const mut = useMutation({
    mutationFn: () => api.post('/users', { full_name: form.full_name, password: form.password }),
    onSuccess: async (res) => {
      const userId = res.data.id
      if (form.roles.length > 0) await api.post(`/users/${userId}/roles`, { roles: form.roles })
      qc.invalidateQueries({ queryKey: ['users-page'] })
      onClose()
    },
  })
  const valid = form.full_name.trim() && form.password.length >= 6 && form.roles.length > 0

  return (
    <Modal
      title="Создать пользователя"
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
      <Field label="ФИО *">
        <input style={controlStyle} placeholder="Иванов Иван Иванович" value={form.full_name} onChange={set('full_name')} />
      </Field>
      <Field label="Пароль *" hint="Минимум 6 символов">
        <input style={controlStyle} type="password" placeholder="••••••" value={form.password} onChange={set('password')} />
      </Field>
      <Field label="Роли *">
        <RoleCheckboxes selected={form.roles} onChange={roles => setForm(f => ({ ...f, roles }))} />
      </Field>
      {mut.error && <div style={{ color: '#DC2626', fontSize: 12, marginTop: 8 }}>{mut.error?.response?.data?.detail ?? 'Ошибка'}</div>}
    </Modal>
  )
}

function EditUserModal({ user, onClose }) {
  const qc = useQueryClient()
  const [fullName, setFullName] = useState(user.full_name)
  const [roles, setRoles] = useState([...user.roles])
  const nameMut  = useMutation({ mutationFn: () => api.patch(`/users/${user.id}`, { full_name: fullName }) })
  const rolesMut = useMutation({ mutationFn: () => api.post(`/users/${user.id}/roles`, { roles }) })
  const isPending = nameMut.isPending || rolesMut.isPending
  const error = nameMut.error?.response?.data?.detail ?? rolesMut.error?.response?.data?.detail

  const handleSave = async () => {
    if (!fullName.trim() || roles.length === 0) return
    await nameMut.mutateAsync()
    await rolesMut.mutateAsync()
    qc.invalidateQueries({ queryKey: ['users-page'] })
    onClose()
  }

  return (
    <Modal
      title="Редактировать пользователя"
      onClose={onClose}
      footer={<>
        <button onClick={onClose} style={{ height: 38, padding: '0 18px', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, color: '#334155' }}>Отмена</button>
        <button
          onClick={handleSave}
          disabled={!fullName.trim() || roles.length === 0 || isPending}
          style={{ height: 38, padding: '0 18px', border: 'none', borderRadius: 8, background: '#1E293B', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500, opacity: isPending ? 0.6 : 1 }}
        >
          {isPending ? 'Сохранение...' : 'Сохранить'}
        </button>
      </>}
    >
      <div style={{ background: '#F8FAFC', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 13, color: '#64748B', fontFamily: 'monospace' }}>
        @{user.username}
      </div>
      <Field label="ФИО *">
        <input style={controlStyle} value={fullName} onChange={e => setFullName(e.target.value)} />
      </Field>
      <Field label="Роли *">
        <RoleCheckboxes selected={roles} onChange={setRoles} />
      </Field>
      {error && <div style={{ color: '#DC2626', fontSize: 12, marginTop: 8 }}>{error}</div>}
    </Modal>
  )
}

function ResetPasswordModal({ user, onClose }) {
  const [form, setForm] = useState({ old_password: '', new_password: '' })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))
  const mut = useMutation({
    mutationFn: () => api.post(`/users/${user.id}/reset-password`, { old_password: form.old_password, new_password: form.new_password }),
    onSuccess: onClose,
  })
  const valid = form.old_password && form.new_password.length >= 6

  return (
    <Modal
      title={`Сброс пароля — ${user.full_name}`}
      onClose={onClose}
      footer={<>
        <button onClick={onClose} style={{ height: 38, padding: '0 18px', border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, color: '#334155' }}>Отмена</button>
        <button
          onClick={() => valid && mut.mutate()}
          disabled={!valid || mut.isPending}
          style={{ height: 38, padding: '0 18px', border: 'none', borderRadius: 8, background: '#1E293B', color: '#FFF', cursor: valid ? 'pointer' : 'not-allowed', fontSize: 13, fontWeight: 500, opacity: !valid || mut.isPending ? 0.5 : 1 }}
        >
          {mut.isPending ? 'Сохранение...' : 'Сохранить пароль'}
        </button>
      </>}
    >
      <Field label="Текущий пароль *">
        <input style={controlStyle} type="password" placeholder="••••••" value={form.old_password} onChange={set('old_password')} />
      </Field>
      <Field label="Новый пароль *" hint="Минимум 6 символов">
        <input style={controlStyle} type="password" placeholder="••••••" value={form.new_password} onChange={set('new_password')} />
      </Field>
      {mut.error && <div style={{ color: '#DC2626', fontSize: 12, marginTop: 4 }}>{mut.error?.response?.data?.detail ?? 'Ошибка'}</div>}
    </Modal>
  )
}

// ─── Drawer ───────────────────────────────────────────────────────────────────

function Drawer({ user, currentUserId, onClose, onEdit, onResetPw }) {
  const qc = useQueryClient()
  const toggleMut = useMutation({
    mutationFn: () => api.post(user.is_active ? `/users/${user.id}/deactivate` : `/users/${user.id}/activate`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users-page'] }); onClose() },
  })

  const isSelf = user.id === currentUserId

  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 100 }} />
      <div style={{
        position: 'absolute', top: 0, right: 0, bottom: 0, width: 400,
        background: '#FFF', borderLeft: '1px solid #E2E8F0',
        zIndex: 101, display: 'flex', flexDirection: 'column',
        boxShadow: '-4px 0 24px rgba(0,0,0,0.06)',
      }}>
        {/* Head */}
        <div style={{ padding: '18px 24px 14px', borderBottom: '1px solid #F1F5F9', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 500, color: user.is_active ? '#0F172A' : '#94A3B8' }}>{user.full_name}</div>
              <div style={{ fontSize: 13, color: '#94A3B8', marginTop: 3, fontFamily: 'monospace' }}>@{user.username}</div>
            </div>
            <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 22, color: '#94A3B8', lineHeight: 1, padding: 0 }}>×</button>
          </div>
          <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            <StatusBadge isActive={user.is_active} />
            {isSelf && (
              <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: '#EFF6FF', color: '#1E40AF', fontWeight: 500 }}>это вы</span>
            )}
          </div>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 24px' }}>
          <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid #F1F5F9' }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Роли</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {user.roles.map(r => <RoleTag key={r} role={r} />)}
            </div>
          </div>
          <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: '1px solid #F1F5F9' }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Telegram</div>
            <TelegramIndicator user={user} />
            {user.telegram_username && (
              <div style={{ fontSize: 12, color: '#94A3B8', marginTop: 4 }}>@{user.telegram_username}</div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div style={{ padding: '14px 24px', borderTop: '1px solid #F1F5F9', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            onClick={onEdit}
            style={{ height: 38, border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, color: '#334155', fontWeight: 500 }}
          >
            Редактировать
          </button>
          <button
            onClick={onResetPw}
            style={{ height: 38, border: '1px solid #E2E8F0', borderRadius: 8, background: '#FFF', cursor: 'pointer', fontSize: 13, color: '#334155', fontWeight: 500 }}
          >
            Сбросить пароль
          </button>
          {!isSelf && (
            <button
              onClick={() => toggleMut.mutate()}
              disabled={toggleMut.isPending}
              style={{
                height: 38, border: `1px solid ${user.is_active ? '#FCA5A5' : '#86EFAC'}`,
                borderRadius: 8,
                background: user.is_active ? '#FEF2F2' : '#ECFDF5',
                color: user.is_active ? '#B91C1C' : '#047857',
                cursor: 'pointer', fontSize: 13, fontWeight: 500,
                opacity: toggleMut.isPending ? 0.6 : 1,
              }}
            >
              {user.is_active ? 'Деактивировать' : 'Активировать'}
            </button>
          )}
          {toggleMut.isError && (
            <div style={{ color: '#DC2626', fontSize: 12 }}>{toggleMut.error?.response?.data?.detail ?? 'Ошибка'}</div>
          )}
        </div>
      </div>
    </>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

const COL = '1.5fr 1.2fr 1.5fr 150px 130px'

export default function Users() {
  const { user: authUser, hasRole } = useAuth()
  const isDirector = hasRole('director')

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users-page'],
    queryFn: () => api.get('/users?include_inactive=true').then(r => r.data),
    enabled: isDirector,
  })
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get('/users/me').then(r => r.data),
  })

  const [search, setSearch]           = useState('')
  const [showInactive, setShowInactive] = useState(false)
  const [selectedId, setSelectedId]   = useState(null)
  const [modal, setModal]             = useState(null) // 'create' | { type, user }

  const currentUserId = me?.id ?? null

  const filtered = useMemo(() => users
    .filter(u => showInactive || u.is_active)
    .filter(u => !search || u.full_name.toLowerCase().includes(search.toLowerCase()) || u.username.toLowerCase().includes(search.toLowerCase())),
    [users, showInactive, search])

  const selected = users.find(u => u.id === selectedId) ?? null

  if (!isDirector) {
    return (
      <div style={{ padding: '48px 32px', textAlign: 'center', color: '#94A3B8', fontSize: 14 }}>
        Доступ только для директора
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '24px 32px 0', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 500, color: '#0F172A' }}>Пользователи</h1>
          <button
            onClick={() => setModal('create')}
            style={{ height: 38, padding: '0 18px', border: 'none', borderRadius: 8, background: '#1E293B', color: '#FFF', cursor: 'pointer', fontSize: 13, fontWeight: 500 }}
          >
            + Создать пользователя
          </button>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
          <input
            placeholder="Поиск по имени или логину..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ height: 34, padding: '0 12px', border: '1px solid #E2E8F0', borderRadius: 8, fontSize: 13, outline: 'none', width: 280, fontFamily: 'inherit', color: '#0F172A', boxSizing: 'border-box' }}
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer', color: '#64748B', userSelect: 'none' }}>
            <input type="checkbox" checked={showInactive} onChange={e => setShowInactive(e.target.checked)} style={{ cursor: 'pointer' }} />
            Показать деактивированных
          </label>
        </div>
      </div>

      {/* Table */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 32px 28px' }}>
        <div style={{ background: '#FFF', borderRadius: 10, border: '1px solid #E2E8F0', overflow: 'hidden' }}>
          <div style={{ display: 'grid', gridTemplateColumns: COL, padding: '12px 16px', background: '#F8FAFC', borderBottom: '1px solid #E2E8F0', fontSize: 12, fontWeight: 500, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.06em', gap: 8 }}>
            <span>ФИО</span>
            <span>Username</span>
            <span>Роли</span>
            <span>Telegram</span>
            <span>Статус</span>
          </div>

          {isLoading && <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8', fontSize: 13 }}>Загрузка...</div>}

          {!isLoading && filtered.length === 0 && (
            <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8', fontSize: 13 }}>
              {search ? 'Ничего не найдено' : 'Нет пользователей'}
            </div>
          )}

          {filtered.map(u => {
            const isSelf     = u.id === currentUserId
            const isSelected = u.id === selectedId
            return (
              <div
                key={u.id}
                onClick={() => setSelectedId(isSelected ? null : u.id)}
                style={{
                  display: 'grid', gridTemplateColumns: COL,
                  padding: '14px 16px', borderBottom: '1px solid #F1F5F9',
                  cursor: 'pointer', alignItems: 'center', fontSize: 14, gap: 8,
                  background: isSelected ? '#F0F9FF' : '#FFF',
                  boxShadow: isSelf ? 'inset 4px 0 0 0 #1E40AF' : 'none',
                  transition: 'background 0.1s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    fontWeight: 500,
                    color: u.is_active ? '#0F172A' : '#94A3B8',
                    textDecoration: u.is_active ? 'none' : 'line-through',
                  }}>
                    {u.full_name}
                  </span>
                  {isSelf && (
                    <span style={{ fontSize: 11, padding: '1px 6px', borderRadius: 4, background: '#EFF6FF', color: '#1E40AF', fontWeight: 500, flexShrink: 0 }}>это вы</span>
                  )}
                </div>
                <span style={{ color: '#64748B', fontFamily: 'monospace', fontSize: 13 }}>@{u.username}</span>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {u.roles.map(r => <RoleTag key={r} role={r} />)}
                </div>
                <TelegramIndicator user={u} />
                <StatusBadge isActive={u.is_active} />
              </div>
            )
          })}
        </div>
      </div>

      {selected && (
        <Drawer
          user={selected}
          currentUserId={currentUserId}
          onClose={() => setSelectedId(null)}
          onEdit={() => setModal({ type: 'edit', user: selected })}
          onResetPw={() => setModal({ type: 'resetpw', user: selected })}
        />
      )}

      {modal === 'create' && <CreateUserModal onClose={() => setModal(null)} />}
      {modal?.type === 'edit' && <EditUserModal user={modal.user} onClose={() => setModal(null)} />}
      {modal?.type === 'resetpw' && <ResetPasswordModal user={modal.user} onClose={() => setModal(null)} />}
    </div>
  )
}
