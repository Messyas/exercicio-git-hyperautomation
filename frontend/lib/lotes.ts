export type LoteStatus = string

export type Lote = {
  id: string
  lote_id: string
  produto: string
  linha: string
  turno: string
  status: LoteStatus
  responsavel: string
  data: string
  observacao: string
  criadoEm: string
}

export const STORAGE_KEY = 'lotes-cadastrados'

export const PRODUTOS = [
  'AC12-SPLIT',
  'AC18-SPLIT',
  'AC9-WINDOW',
  'MON24-FHD',
  'MON27-QHD',
  'MON32-4K',
  'TV43-FHD',
  'TV50-4K-B',
  'TV55-4K-B',
  'TV65-OLED',
] as const

export const STATUS_CONFIG: Record<string, { label: string; badge: string }> = {
  APROVADO: {
    label: 'Aprovado',
    badge: 'border-success text-success bg-success/10',
  },
  REPROVADO: {
    label: 'Reprovado',
    badge: 'border-destructive text-destructive bg-destructive/10',
  },
  PENDENTE: {
    label: 'Pendente',
    badge: 'border-warning text-warning bg-warning/10',
  },
  OK: {
    label: 'OK',
    badge: 'border-info text-info bg-info/10',
  },
  NOK: {
    label: 'NOK',
    badge: 'border-destructive text-destructive bg-destructive/10',
  },
  'REPROV.': {
    label: 'Reprov.',
    badge: 'border-destructive text-destructive bg-destructive/10',
  },
  'APROVADO PARCIAL': {
    label: 'Aprovado parcial',
    badge: 'border-info text-info bg-info/10',
  },
}

export function loadLotes(): Lote[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.map((item) => ({
      id: String(item.id ?? ''),
      lote_id: String(item.lote_id ?? item.numero ?? ''),
      produto: String(item.produto ?? ''),
      linha: String(item.linha ?? ''),
      turno: String(item.turno ?? ''),
      status: String(item.status ?? ''),
      responsavel: String(item.responsavel ?? ''),
      data: String(item.data ?? ''),
      observacao: String(item.observacao ?? ''),
      criadoEm: String(item.criadoEm ?? ''),
    }))
  } catch {
    return []
  }
}

export function saveLotes(lotes: Lote[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(lotes))
}
