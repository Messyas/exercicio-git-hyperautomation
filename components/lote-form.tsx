'use client'

import { useState } from 'react'
import { CheckCircle2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'
import {
  PRODUTOS,
  STATUS_CONFIG,
  STATUS_ORDER,
  type Lote,
  type LoteStatus,
} from '@/lib/lotes'

type Props = {
  onCreate: (lote: Lote) => void
}

export function LoteForm({ onCreate }: Props) {
  const [numero, setNumero] = useState('')
  const [produto, setProduto] = useState('')
  const [status, setStatus] = useState<LoteStatus>('pendente')
  const [sucesso, setSucesso] = useState<string | null>(null)
  const [erro, setErro] = useState<{ numero?: string; produto?: string }>({})

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    const novoErro: { numero?: string; produto?: string } = {}
    if (!numero.trim()) novoErro.numero = 'Informe o número do lote.'
    if (!produto) novoErro.produto = 'Selecione um produto.'
    setErro(novoErro)
    if (Object.keys(novoErro).length > 0) return

    const lote: Lote = {
      id:
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : String(Date.now()),
      numero: numero.trim(),
      produto,
      status,
      criadoEm: new Date().toISOString(),
    }

    onCreate(lote)
    setSucesso(`Lote ${lote.numero} processado com sucesso.`)
    setNumero('')
    setProduto('')
    setStatus('pendente')
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6" noValidate>
      {sucesso && (
        <div
          role="status"
          className="flex items-start justify-between gap-3 border border-success bg-success/10 px-4 py-3 text-sm text-success"
        >
          <span className="flex items-center gap-2">
            <CheckCircle2 className="size-4 shrink-0" aria-hidden="true" />
            {sucesso}
          </span>
          <button
            type="button"
            onClick={() => setSucesso(null)}
            aria-label="Fechar mensagem"
            className="text-success/80 hover:text-success"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
        </div>
      )}

      <div className="flex flex-col gap-2">
        <Label htmlFor="numero">Número do lote</Label>
        <Input
          id="numero"
          value={numero}
          onChange={(e) => setNumero(e.target.value)}
          placeholder="Ex.: LT-2026-0042"
          aria-invalid={!!erro.numero}
          aria-describedby={erro.numero ? 'numero-erro' : undefined}
        />
        {erro.numero && (
          <p id="numero-erro" className="text-xs text-destructive">
            {erro.numero}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="produto">Produto</Label>
        <Select value={produto} onValueChange={(v) => setProduto(v ?? '')}>
          <SelectTrigger
            id="produto"
            className="w-full"
            aria-invalid={!!erro.produto}
            aria-describedby={erro.produto ? 'produto-erro' : undefined}
          >
            <SelectValue placeholder="Selecione um produto" />
          </SelectTrigger>
          <SelectContent>
            {PRODUTOS.map((p) => (
              <SelectItem key={p} value={p}>
                {p}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {erro.produto && (
          <p id="produto-erro" className="text-xs text-destructive">
            {erro.produto}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <Label id="status-label">Status</Label>
        <div
          role="radiogroup"
          aria-labelledby="status-label"
          className="grid grid-cols-1 border border-input sm:grid-cols-3"
        >
          {STATUS_ORDER.map((s, i) => {
            const ativo = status === s
            return (
              <button
                key={s}
                type="button"
                role="radio"
                aria-checked={ativo}
                onClick={() => setStatus(s)}
                className={cn(
                  'px-4 py-2.5 text-sm font-medium transition-colors',
                  'border-input focus-visible:outline-2 focus-visible:outline-ring',
                  i > 0 && 'border-t sm:border-t-0 sm:border-l',
                  ativo
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                )}
              >
                {STATUS_CONFIG[s].label}
              </button>
            )
          })}
        </div>
      </div>

      <Button type="submit" className="w-full sm:w-auto">
        Processar lote
      </Button>
    </form>
  )
}
