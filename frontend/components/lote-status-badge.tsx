import { CircleDashed, AlertCircle, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { STATUS_CONFIG, type LoteStatus } from '@/lib/lotes'

const ICONS: Record<string, typeof CircleDashed> = {
  APROVADO: CheckCircle2,
  REPROVADO: AlertCircle,
  PENDENTE: CircleDashed,
  OK: CheckCircle2,
  NOK: AlertCircle,
  'REPROV.': AlertCircle,
  'APROVADO PARCIAL': CircleDashed,
}

export function LoteStatusBadge({ status }: { status: LoteStatus }) {
  const config = STATUS_CONFIG[status] ?? {
    label: status || 'Não informado',
    badge: 'border-border text-muted-foreground bg-muted',
  }
  const Icon = ICONS[status] ?? CircleDashed

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 border px-2 py-1 text-xs font-medium',
        config.badge,
      )}
    >
      <Icon className="size-3.5" aria-hidden="true" />
      {config.label}
    </span>
  )
}
