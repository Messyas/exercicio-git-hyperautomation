import { CircleDashed, Loader, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { STATUS_CONFIG, type LoteStatus } from '@/lib/lotes'

const ICONS: Record<LoteStatus, typeof CircleDashed> = {
  pendente: CircleDashed,
  em_processamento: Loader,
  concluido: CheckCircle2,
}

export function LoteStatusBadge({ status }: { status: LoteStatus }) {
  const config = STATUS_CONFIG[status]
  const Icon = ICONS[status]

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
