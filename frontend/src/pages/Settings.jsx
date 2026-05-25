import { useState } from 'react'
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

function initials(name) {
  if (!name) return '?'
  return name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
}

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

function Section({ title, children }) {
  return (
    <div style={{ background: '#FFF', borderRadius: 10, border: '1px solid #E2E8F0', padding: '20px 24px', marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 16 }}>{title}</div>
      {children}
    </div>
  )
}

function SuccessMsg({ show }) {
  if (!show) return null
  return <span style={{ fontSize: 12, color: '#047857', fontWeight: 500 }}>✓ Сохранено</span>
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Settings() {
  const { user: authUser } = useAuth()
  const qc = useQueryClient()

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get('/users/me').then(r => r.data),
  })

  // Password form
  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', confirm: '' })
  const [pwOk, setPwOk] = useState(false)
  const setPw = k => e => setPwForm(f => ({ ...f, [k]: e.target.value }))
  const pwMut = useMutation({
    mutationFn: () => api.post('/users/me/reset-password', { old_password: pwForm.old_password, new_password: pwForm.new_password }),
    onSuccess: () => {
      setPwForm({ old_password: '', new_password: '', confirm: '' })
      setPwOk(true)
      setTimeout(() => setPwOk(false), 3000)
    },
  })
  const pwValid = pwForm.old_password && pwForm.new_password.length >= 6 && pwForm.new_password === pwForm.confirm

  // Telegram form
  const [tgUsername, setTgUsername] = useState('')
  const [tgOk, setTgOk] = useState(false)
  const tgMut = useMutation({
    mutationFn: () => api.post('/users/me/bind-telegram', { telegram_username: tgUsername.replace('@', '') }),
    onSuccess: () => {
      setTgOk(true)
      setTgUsername('')
      qc.invalidateQueries({ queryKey: ['me'] })
      setTimeout(() => setTgOk(false), 3000)
    },
  })

  const displayName = me?.full_name ?? authUser?.name ?? '—'
  const username    = me?.username ?? authUser?.sub ?? ''
  const roles       = me?.roles ?? authUser?.roles ?? []
  const hasTelegram = !!me?.telegram_id
  const tgPending   = !me?.telegram_id && !!me?.telegram_username

  return (
    <div style={{ padding: '24px 32px', maxWidth: 680, boxSizing: 'border-box' }}>
      <h1 style={{ margin: '0 0 20px', fontSize: 24, fontWeight: 500, color: '#0F172A' }}>Настройки</h1>

      {/* Profile card */}
      <Section title="Профиль">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 52, height: 52, borderRadius: '50%', background: '#1E293B', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 600, color: '#FFF', flexShrink: 0 }}>
            {initials(displayName)}
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#0F172A' }}>{displayName}</div>
            <div style={{ fontSize: 13, color: '#94A3B8', marginTop: 2, fontFamily: 'monospace' }}>@{username}</div>
            <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
              {roles.map(r => (
                <span key={r} style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: '#F1F5F9', color: '#475569', border: '1px solid #E2E8F0' }}>
                  {roleName(r)}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Telegram status */}
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #F1F5F9', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
          {hasTelegram ? (
            <>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#059669', flexShrink: 0 }} />
              <span style={{ color: '#047857', fontWeight: 500 }}>Telegram привязан</span>
              {me?.telegram_username && <span style={{ color: '#94A3B8' }}>· @{me.telegram_username}</span>}
            </>
          ) : tgPending ? (
            <>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#D97706', flexShrink: 0 }} />
              <span style={{ color: '#B45309', fontWeight: 500 }}>Ожидает /start в боте</span>
              <span style={{ color: '#94A3B8' }}>· @{me.telegram_username}</span>
            </>
          ) : (
            <>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#CBD5E1', flexShrink: 0 }} />
              <span style={{ color: '#94A3B8' }}>Telegram не привязан</span>
            </>
          )}
        </div>
      </Section>

      {/* Change password */}
      <Section title="Изменить пароль">
        <div style={{ maxWidth: 360 }}>
          <Field label="Текущий пароль *">
            <input style={controlStyle} type="password" placeholder="••••••" value={pwForm.old_password} onChange={setPw('old_password')} />
          </Field>
          <Field label="Новый пароль *" hint="Минимум 6 символов">
            <input style={controlStyle} type="password" placeholder="••••••" value={pwForm.new_password} onChange={setPw('new_password')} />
          </Field>
          <Field label="Подтверждение *">
            <input style={controlStyle} type="password" placeholder="••••••" value={pwForm.confirm} onChange={setPw('confirm')} />
            {pwForm.confirm && pwForm.new_password !== pwForm.confirm && (
              <div style={{ fontSize: 11, color: '#DC2626', marginTop: 4 }}>Пароли не совпадают</div>
            )}
          </Field>
          {pwMut.error && <div style={{ fontSize: 12, color: '#DC2626', marginBottom: 12 }}>{pwMut.error?.response?.data?.detail ?? 'Ошибка'}</div>}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={() => pwValid && pwMut.mutate()}
              disabled={!pwValid || pwMut.isPending}
              style={{ height: 38, padding: '0 18px', border: 'none', borderRadius: 8, background: '#1E293B', color: '#FFF', cursor: pwValid ? 'pointer' : 'not-allowed', fontSize: 13, fontWeight: 500, opacity: !pwValid || pwMut.isPending ? 0.5 : 1 }}
            >
              {pwMut.isPending ? 'Сохранение...' : 'Изменить пароль'}
            </button>
            <SuccessMsg show={pwOk} />
          </div>
        </div>
      </Section>

      {/* Telegram */}
      <Section title="Привязать Telegram">
        <div style={{ fontSize: 13, color: '#64748B', marginBottom: 14 }}>
          {me?.telegram_username
            ? `Текущий аккаунт: @${me.telegram_username}. Вы можете изменить его.`
            : 'Укажите ваш Telegram username для получения уведомлений.'}
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', maxWidth: 360 }}>
          <div style={{ flex: 1 }}>
            <Field label="Telegram username">
              <input
                style={controlStyle}
                placeholder="@username"
                value={tgUsername}
                onChange={e => setTgUsername(e.target.value)}
              />
            </Field>
          </div>
          <button
            onClick={() => tgUsername.trim() && tgMut.mutate()}
            disabled={!tgUsername.trim() || tgMut.isPending}
            style={{ height: 38, padding: '0 18px', border: 'none', borderRadius: 8, background: '#1E293B', color: '#FFF', cursor: tgUsername.trim() ? 'pointer' : 'not-allowed', fontSize: 13, fontWeight: 500, opacity: !tgUsername.trim() || tgMut.isPending ? 0.5 : 1, marginBottom: 16, whiteSpace: 'nowrap' }}
          >
            Привязать
          </button>
        </div>
        {tgMut.error && <div style={{ fontSize: 12, color: '#DC2626', marginTop: -8 }}>{tgMut.error?.response?.data?.detail ?? 'Ошибка'}</div>}
        <SuccessMsg show={tgOk} />
      </Section>
    </div>
  )
}
