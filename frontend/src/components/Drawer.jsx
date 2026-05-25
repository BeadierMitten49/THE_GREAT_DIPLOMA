import { X } from 'lucide-react'

export default function Drawer({ open, onClose, title, children }) {
  return (
    <div
      className={`fixed top-0 right-0 h-full w-[420px] bg-white shadow-2xl z-40 flex flex-col transition-transform duration-300 ${
        open ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 shrink-0">
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
          <X size={18} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
    </div>
  )
}

export function DrawerSection({ title, children }) {
  return (
    <div className="mb-5">
      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">{title}</div>
      {children}
    </div>
  )
}

export function DrawerRow({ label, value }) {
  return (
    <div className="flex gap-2 text-sm mb-1.5">
      <span className="text-slate-500 shrink-0 w-36">{label}</span>
      <span className="text-slate-900 font-medium">{value ?? '—'}</span>
    </div>
  )
}
