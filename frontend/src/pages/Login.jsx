import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const ERRORS = {
  invalid:     'Неверное имя пользователя или пароль',
  deactivated: 'Учётная запись деактивирована. Обратитесь к директору.',
  network:     'Ошибка соединения. Проверьте подключение к сети.',
  rate_limit:  null, // shown as locked state
}

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState(null)   // 'invalid' | 'deactivated' | 'network' | null
  const [locked, setLocked] = useState(false)
  const [loading, setLoading] = useState(false)
  const [touched, setTouched] = useState({ username: false, password: false })

  const usernameEmpty = touched.username && !username
  const passwordEmpty = touched.password && !password
  const canSubmit = username && password && !loading && !locked

  const handleSubmit = async (e) => {
    e.preventDefault()
    setTouched({ username: true, password: true })
    if (!username || !password) return
    setError(null)
    setLoading(true)
    try {
      await login(username, password)
      navigate('/orders')
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail ?? ''
      if (status === 429) {
        setLocked(true)
      } else if (status === 401) {
        setError('invalid')
      } else if (status === 403 && detail.toLowerCase().includes('deactivat')) {
        setError('deactivated')
      } else if (!status) {
        setError('network')
      } else {
        setError('invalid')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#F5F6F8', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: 400 }}>

        {/* Card */}
        <div style={{ background: '#FFFFFF', border: '0.5px solid #E2E8F0', borderRadius: 12, padding: 40 }}>

          {/* Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
            <div style={{ width: 48, height: 48, background: '#0F172A', borderRadius: 8, flexShrink: 0 }} />
            <span style={{ fontSize: 18, fontWeight: 500, color: '#0F172A', letterSpacing: '0.02em' }}>ЯРКО</span>
          </div>

          <div style={{ fontSize: 24, fontWeight: 500, lineHeight: '32px', color: '#0F172A', marginBottom: 24 }}>
            Вход в систему
          </div>

          {locked ? (
            <LockedBlock />
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              {/* Username */}
              <div style={{ marginBottom: 16 }}>
                <div style={labelStyle}>Имя пользователя</div>
                <input
                  value={username}
                  onChange={(e) => { setUsername(e.target.value); setError(null) }}
                  onBlur={() => setTouched((t) => ({ ...t, username: true }))}
                  placeholder="Введите логин"
                  autoComplete="username"
                  disabled={loading}
                  style={inputStyle(error === 'invalid', usernameEmpty, loading)}
                />
                {usernameEmpty && <div style={vmsgStyle}>Заполните это поле</div>}
              </div>

              {/* Password */}
              <div style={{ marginBottom: 16 }}>
                <div style={labelStyle}>Пароль</div>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showPw ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => { setPassword(e.target.value); setError(null) }}
                    onBlur={() => setTouched((t) => ({ ...t, password: true }))}
                    placeholder="Введите пароль"
                    autoComplete="current-password"
                    disabled={loading}
                    style={{ ...inputStyle(error === 'invalid', passwordEmpty, loading), paddingRight: 40 }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw((v) => !v)}
                    style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#94A3B8', display: 'flex', alignItems: 'center' }}
                    tabIndex={-1}
                  >
                    {showPw ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>
                {passwordEmpty && <div style={vmsgStyle}>Заполните это поле</div>}
              </div>

              {/* Error block */}
              {error && error !== 'invalid' && (
                <div style={errBlockStyle}>
                  <span style={{ flexShrink: 0, color: '#DC2626', fontSize: 16, marginTop: 2 }}>
                    {error === 'deactivated' ? <BanIcon /> : <AlertCircleIcon />}
                  </span>
                  <span>{ERRORS[error]}</span>
                </div>
              )}
              {error === 'invalid' && (
                <div style={errBlockStyle}>
                  <span style={{ flexShrink: 0, color: '#DC2626', fontSize: 16, marginTop: 2 }}><AlertCircleIcon /></span>
                  <span>Неверное имя пользователя или пароль</span>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={!canSubmit}
                style={btnStyle(!canSubmit, loading)}
              >
                {loading
                  ? <><Spinner /> Вход…</>
                  : 'Войти'}
              </button>
            </form>
          )}
        </div>

        {/* Dev bypass */}
        {import.meta.env.DEV && !locked && (
          <div style={{ marginTop: 12, background: 'rgba(0,0,0,0.04)', border: '1px solid #E2E8F0', borderRadius: 8, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: '#94A3B8', marginBottom: 8 }}>Режим разработки</div>
            <button
              type="button"
              onClick={async () => { await login('demo', 'demo'); navigate('/orders') }}
              style={{ fontSize: 12, color: '#475569', background: 'none', border: '1px solid #CBD5E1', borderRadius: 6, padding: '4px 12px', cursor: 'pointer' }}
            >
              Войти как demo (директор)
            </button>
          </div>
        )}

        {/* Footer */}
        <div style={{ textAlign: 'center', fontSize: 12, color: '#64748B', marginTop: 20 }}>
          АИС «Ярко» · ООО ТД «Ярко» · 2026
        </div>
      </div>
    </div>
  )
}

function LockedBlock() {
  return (
    <div style={{ background: '#FEF2F2', border: '1px solid #DC2626', borderRadius: 8, padding: 16, color: '#B91C1C' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, fontSize: 16, fontWeight: 500 }}>
        <LockIcon />
        <span>Вход временно заблокирован</span>
      </div>
      <div style={{ fontSize: 14, lineHeight: '20px' }}>
        Превышено количество попыток входа. Попробуйте снова через 28 минут или обратитесь к директору.
      </div>
    </div>
  )
}

// Styles
const labelStyle = { fontSize: 14, fontWeight: 500, color: '#334155', marginBottom: 6 }
const vmsgStyle  = { fontSize: 12, color: '#B91C1C', marginTop: 6 }
const errBlockStyle = {
  display: 'flex', alignItems: 'flex-start', gap: 8,
  marginBottom: 16, fontSize: 14, color: '#B91C1C', fontWeight: 500, lineHeight: '20px',
}

function inputStyle(isInvalid, isEmpty, disabled) {
  const hasBorderError = isInvalid || isEmpty
  return {
    width: '100%', height: 40, border: `1px solid ${hasBorderError ? '#DC2626' : '#CBD5E1'}`,
    borderRadius: 8, background: disabled ? '#F7F8FB' : '#FFFFFF',
    padding: '0 12px', fontSize: 14, color: '#0F172A', boxSizing: 'border-box',
    outline: 'none', fontFamily: 'inherit',
  }
}

function btnStyle(disabled, loading) {
  return {
    width: '100%', height: 44, borderRadius: 8, border: 'none', cursor: disabled ? 'not-allowed' : 'pointer',
    background: disabled ? '#E2E8F0' : '#1E293B', color: disabled ? '#94A3B8' : '#FFFFFF',
    fontSize: 14, fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    fontFamily: 'inherit', marginTop: 4,
  }
}

// Inline SVG icons (Tabler outline style)
function EyeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
    </svg>
  )
}
function EyeOffIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
  )
}
function AlertCircleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  )
}
function BanIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
    </svg>
  )
}
function LockIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
  )
}
function Spinner() {
  return (
    <span style={{ width: 14, height: 14, border: '2px solid #FFFFFF', borderRightColor: 'transparent', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.7s linear infinite' }} />
  )
}
