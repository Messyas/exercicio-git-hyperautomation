export type LoteStatus = 'pendente' | 'em_processamento' | 'concluido'

export type Lote = {
  id: string
  numero: string
  produto: string
  status: LoteStatus
  criadoEm: string
}

export const STORAGE_KEY = 'lotes-cadastrados'

export const PRODUTOS = [
  'Chapa de Aço 1020',
  'Perfil de Alumínio',
  'Tubo Galvanizado',
  'Bobina Laminada',
  'Barra Trefilada',
  'Fio de Cobre',
] as const

export const STATUS_CONFIG: Record<
  LoteStatus,
  { label: string; badge: string }
> = {
  pendente: {
    label: 'Pendente',
    badge: 'border-warning text-warning bg-warning/10',
  },
  em_processamento: {
    label: 'Em processamento',
    badge: 'border-info text-info bg-info/10',
  },
  concluido: {
    label: 'Concluído',
    badge: 'border-success text-success bg-success/10',
  },
}

export const STATUS_ORDER: LoteStatus[] = [
  'pendente',
  'em_processamento',
  'concluido',
]

export function loadLotes(): Lote[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as Lote[]) : []
  } catch {
    return []
  }
}

export function saveLotes(lotes: Lote[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(lotes))
}
