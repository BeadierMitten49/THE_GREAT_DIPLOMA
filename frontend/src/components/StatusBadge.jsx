// Unified gray badge per UI Kit — same style for all status types
export const ORDER_STATUSES = {
  created:    { label: 'Создан' },
  production: { label: 'Производство' },
  assembly:   { label: 'Сборка' },
  delivery:   { label: 'Доставка' },
  completed:  { label: 'Завершён' },
  cancelled:  { label: 'Отменён' },
}

export const TASK_STATUSES = {
  created:     { label: 'Создана' },
  in_progress: { label: 'В работе' },
  stopped:     { label: 'Остановлена' },
  completed:   { label: 'Завершена' },
  closed:      { label: 'Закрыта' },
}

export const DELIVERY_STATUSES = {
  pending:    { label: 'Ожидает' },
  picked_up:  { label: 'Забрана' },
  in_transit: { label: 'В пути' },
  completed:  { label: 'Доставлена' },
  cancelled:  { label: 'Отменена' },
}

const ALL = { ...ORDER_STATUSES, ...TASK_STATUSES, ...DELIVERY_STATUSES }

export default function StatusBadge({ status }) {
  const cfg = ALL[status] ?? { label: status }
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', padding: '3px 10px',
      borderRadius: 999, fontSize: 12, fontWeight: 500,
      border: '1px solid #CBD5E1', background: '#F1F5F9', color: '#475569',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#94A3B8', marginRight: 6, flexShrink: 0, display: 'inline-block' }} />
      {cfg.label}
    </span>
  )
}
