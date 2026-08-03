'use client'

import { useState } from 'react'
import { CheckCircle2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  PRODUTOS,
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
  const [status, setStatus] = useState<LoteStatus>('APROVADO')
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
    setStatus('APROVADO')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-6"
      aria-label="Formulário de cadastro de lote"
      noValidate
    >
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
          <p id="numero-erro" role="alert" className="text-xs text-destructive">
            {erro.numero}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="produto">Produto</Label>
        <select
          id="produto"
          value={produto}
          onChange={(e) => setProduto(e.target.value)}
          aria-invalid={!!erro.produto}
          aria-describedby={erro.produto ? 'produto-erro' : undefined}
          className="h-9 w-full border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30"
        >
          <option value="">Selecione um produto</option>
          {PRODUTOS.map((produtoOption) => (
            <option key={produtoOption} value={produtoOption}>
              {produtoOption}
            </option>
          ))}
        </select>
        {erro.produto && (
          <p id="produto-erro" role="alert" className="text-xs text-destructive">
            {erro.produto}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="status">Status</Label>
        <select
          id="status"
          value={status}
          onChange={(e) => setStatus(e.target.value as LoteStatus)}
          className="h-9 w-full border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30"
        >
          {STATUS_ORDER.map((statusOption) => (
            <option key={statusOption} value={statusOption}>
              {statusOption}
            </option>
          ))}
        </select>
      </div>

      <Button type="submit" className="w-full sm:w-auto">
        Processar lote
      </Button>
    </form>
  )
}
