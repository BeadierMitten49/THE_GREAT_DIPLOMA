import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

const WAREHOUSE_LINKS = [
  { to: '/warehouse/raw',      label: 'Склад сырья' },
  { to: '/warehouse/packaging', label: 'Склад упаковки' },
  { to: '/warehouse/products',  label: 'Склад продукции' },
]

const SETTINGS_LINKS = [
  { to: '/settings', label: 'Настройки профиля' },
  { to: '/users',    label: 'Пользователи' },
]

function initials(name) {
  if (!name) return '?'
  return name.split(' ').slice(0, 2).map((w) => w[0]).join('').toUpperCase()
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const isOnWarehouse = location.pathname.startsWith('/warehouse')
  const isOnSettings  = location.pathname.startsWith('/settings') || location.pathname.startsWith('/users')
  const [warehouseOpen, setWarehouseOpen] = useState(isOnWarehouse)
  const [settingsOpen, setSettingsOpen]   = useState(isOnSettings)

  const handleLogout = () => { logout(); navigate('/login') }

  const navLinkStyle = (isActive) => ({
    display: 'flex', alignItems: 'center', gap: 12,
    padding: '9px 12px', borderRadius: 6, margin: '1px 0',
    fontSize: 14, fontWeight: isActive ? 500 : 400,
    color: isActive ? '#FFFFFF' : '#CBD5E1',
    background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
    textDecoration: 'none', transition: 'background 0.15s, color 0.15s',
  })

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <aside style={{ width: 240, background: '#0F172A', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        {/* Brand */}
        <div style={{ padding: '20px 20px 16px', display: 'flex', alignItems: 'center', gap: 10, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ width: 32, height: 32, background: '#FFFFFF', borderRadius: 6, flexShrink: 0 }} />
          <span style={{ fontSize: 15, fontWeight: 500, color: '#FFFFFF', letterSpacing: '0.02em' }}>АИС Ярко</span>
        </div>

        {/* Nav */}
        <nav style={{ padding: '12px 8px', flex: 1, overflowY: 'auto' }}>
          <NavLink to="/orders" style={({ isActive }) => navLinkStyle(isActive)}>
            <IconPackage />Заказы
          </NavLink>
          <NavLink to="/tasks" style={({ isActive }) => navLinkStyle(isActive)}>
            <IconFactory />Производственные задачи
          </NavLink>

          {/* Warehouse group */}
          <div>
            <button
              onClick={() => setWarehouseOpen(v => !v)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12, width: '100%',
                padding: '9px 12px', borderRadius: 6, margin: '1px 0',
                fontSize: 14, fontWeight: isOnWarehouse ? 500 : 400,
                color: isOnWarehouse ? '#FFFFFF' : '#CBD5E1',
                background: isOnWarehouse ? 'rgba(255,255,255,0.08)' : 'transparent',
                border: 'none', cursor: 'pointer', textAlign: 'left',
                transition: 'background 0.15s, color 0.15s',
              }}
            >
              <IconBuilding />
              <span style={{ flex: 1 }}>Склад</span>
              <span style={{ fontSize: 10, transition: 'transform 0.2s', transform: warehouseOpen ? 'rotate(180deg)' : 'none', opacity: 0.6 }}>▼</span>
            </button>

            {warehouseOpen && (
              <div style={{ marginLeft: 8, marginBottom: 4 }}>
                {WAREHOUSE_LINKS.map(({ to, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    style={({ isActive }) => ({
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '7px 12px 7px 26px', borderRadius: 6, margin: '1px 0',
                      fontSize: 13, fontWeight: isActive ? 500 : 400,
                      color: isActive ? '#FFFFFF' : '#94A3B8',
                      background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
                      textDecoration: 'none', transition: 'background 0.15s, color 0.15s',
                    })}
                  >
                    <span style={{ width: 4, height: 4, borderRadius: '50%', background: 'currentColor', flexShrink: 0 }} />
                    {label}
                  </NavLink>
                ))}
              </div>
            )}
          </div>

          <NavLink to="/assembly" style={({ isActive }) => navLinkStyle(isActive)}>
            <IconBox />Сборка
          </NavLink>
          <NavLink to="/deliveries" style={({ isActive }) => navLinkStyle(isActive)}>
            <IconTruck />Доставки
          </NavLink>
          <NavLink to="/references" style={({ isActive }) => navLinkStyle(isActive)}>
            <IconClipboard />Справочники
          </NavLink>

          {/* Settings group */}
          <div>
            <button
              onClick={() => setSettingsOpen(v => !v)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12, width: '100%',
                padding: '9px 12px', borderRadius: 6, margin: '1px 0',
                fontSize: 14, fontWeight: isOnSettings ? 500 : 400,
                color: isOnSettings ? '#FFFFFF' : '#CBD5E1',
                background: isOnSettings ? 'rgba(255,255,255,0.08)' : 'transparent',
                border: 'none', cursor: 'pointer', textAlign: 'left',
                transition: 'background 0.15s, color 0.15s',
              }}
            >
              <IconSettings />
              <span style={{ flex: 1 }}>Настройки</span>
              <span style={{ fontSize: 10, transition: 'transform 0.2s', transform: settingsOpen ? 'rotate(180deg)' : 'none', opacity: 0.6 }}>▼</span>
            </button>

            {settingsOpen && (
              <div style={{ marginLeft: 8, marginBottom: 4 }}>
                {SETTINGS_LINKS.map(({ to, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    style={({ isActive }) => ({
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '7px 12px 7px 26px', borderRadius: 6, margin: '1px 0',
                      fontSize: 13, fontWeight: isActive ? 500 : 400,
                      color: isActive ? '#FFFFFF' : '#94A3B8',
                      background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
                      textDecoration: 'none', transition: 'background 0.15s, color 0.15s',
                    })}
                  >
                    <span style={{ width: 4, height: 4, borderRadius: '50%', background: 'currentColor', flexShrink: 0 }} />
                    {label}
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        </nav>

        {/* User */}
        <div style={{ padding: '14px 18px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#334155', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 500, color: '#FFFFFF', flexShrink: 0 }}>
            {initials(user?.name)}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: '#FFFFFF', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.name ?? user?.username}</div>
            <div style={{ fontSize: 11, color: '#94A3B8', marginTop: 1 }}>{user?.roles?.[0] ?? ''}</div>
          </div>
          <button onClick={handleLogout} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94A3B8', display: 'flex', alignItems: 'center', padding: 0 }} title="Выйти">
            <IconLogout />
          </button>
        </div>
      </aside>

      {/* Content */}
      <main style={{ flex: 1, overflowY: 'auto', background: '#F5F6F8', position: 'relative' }}>
        {children}
      </main>
    </div>
  )
}

// Tabler-style outline SVG icons
function IconPackage() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3 L20 7 L20 17 L12 21 L4 17 L4 7 Z"/><path d="M12 12 L20 7"/><path d="M12 12 L4 7"/><path d="M12 12 L12 21"/></svg>
}
function IconFactory() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21V11l5 3V11l5 3V11l5 3V21Z"/><path d="M3 21h18"/><path d="M9 17v2"/><path d="M14 17v2"/></svg>
}
function IconBuilding() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="3" width="16" height="18" rx="1"/><path d="M8 7h2M14 7h2M8 11h2M14 11h2M8 15h2M14 15h2"/></svg>
}
function IconBox() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
}
function IconTruck() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 16V6h11v10"/><path d="M14 9h4l3 4v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>
}
function IconClipboard() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="4" width="12" height="17" rx="2"/><path d="M9 4V3a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v1"/><path d="M9 12h6M9 16h6"/></svg>
}
function IconSettings() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/></svg>
}
function IconLogout() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
}
