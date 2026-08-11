'use client'

import { useState } from 'react'
import { CheckCircle2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  PRODUTOS,
  type Lote,
} from '@/lib/lotes'

type Props = {
  onCreate: (lote: Lote) => void
}

const STATUS_OPTIONS = [
  'APROVADO',
  'REPROVADO',
  'PENDENTE',
  'OK',
  'NOK',
  'REPROV.',
  'APROVADO PARCIAL',
]

export function LoteForm({ onCreate }: Props) {
  const [loteId, setLoteId] = useState('')
  const [produto, setProduto] = useState('')
  const [linha, setLinha] = useState('')
  const [turno, setTurno] = useState('')
  const [status, setStatus] = useState('APROVADO')
  const [responsavel, setResponsavel] = useState('')
  const [data, setData] = useState('')
  const [observacao, setObservacao] = useState('')
  const [sucesso, setSucesso] = useState<string | null>(null)
  const [erro, setErro] = useState<{ loteId?: string; produto?: string }>({})

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    const novoErro: { loteId?: string; produto?: string } = {}
    if (!loteId.trim()) novoErro.loteId = 'Informe o número do lote.'
    if (!produto) novoErro.produto = 'Selecione um produto.'
    setErro(novoErro)
    if (Object.keys(novoErro).length > 0) return

    const lote: Lote = {
      id:
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : String(Date.now()),
      lote_id: loteId.trim(),
      produto,
      linha: linha.trim(),
      turno: turno.trim(),
      status,
      responsavel: responsavel.trim(),
      data: data.trim(),
      observacao: observacao.trim(),
      criadoEm: new Date().toISOString(),
    }

    onCreate(lote)
    setSucesso(`Lote ${lote.lote_id} processado com sucesso.`)
    setLoteId('')
    setProduto('')
    setLinha('')
    setTurno('')
    setStatus('APROVADO')
    setResponsavel('')
    setData('')
    setObservacao('')
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
        <Label htmlFor="lote_id">Número do lote</Label>
        <Input
          id="lote_id"
          value={loteId}
          onChange={(e) => setLoteId(e.target.value)}
          placeholder="Ex.: LT-2026-0042"
          aria-invalid={!!erro.loteId}
          aria-describedby={erro.loteId ? 'lote-id-erro' : undefined}
        />
        {erro.loteId && (
          <p id="lote-id-erro" role="alert" className="text-xs text-destructive">
            {erro.loteId}
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

      <div className="grid gap-6 sm:grid-cols-2">
        <div className="flex flex-col gap-2">
          <Label htmlFor="linha">Linha</Label>
          <Input
            id="linha"
            value={linha}
            onChange={(e) => setLinha(e.target.value)}
            placeholder="Ex.: L1"
          />
        </div>

        <div className="flex flex-col gap-2">
          <Label htmlFor="turno">Turno</Label>
          <Input
            id="turno"
            value={turno}
            onChange={(e) => setTurno(e.target.value)}
            placeholder="Ex.: A"
          />
        </div>
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium">Status</legend>
        <div className="flex flex-wrap gap-4">
          {STATUS_OPTIONS.map((statusOption) => (
            <label key={statusOption} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="status"
                value={statusOption}
                checked={status === statusOption}
                onChange={() => setStatus(statusOption)}
              />
              {statusOption}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="flex flex-col gap-2">
        <Label htmlFor="responsavel">Responsável</Label>
        <Input
          id="responsavel"
          value={responsavel}
          onChange={(e) => setResponsavel(e.target.value)}
          placeholder="Nome do responsável"
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="data">Data</Label>
        <Input
          id="data"
          value={data}
          onChange={(e) => setData(e.target.value)}
          placeholder="DD/MM/AAAA"
        />
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="observacao">Observação</Label>
        <textarea
          id="observacao"
          value={observacao}
          onChange={(e) => setObservacao(e.target.value)}
          placeholder="Observação do lote"
          className="min-h-24 w-full border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/30"
        />
      </div>

      <Button type="submit" className="w-full sm:w-auto">
        Processar lote
      </Button>
    </form>
  )
}
