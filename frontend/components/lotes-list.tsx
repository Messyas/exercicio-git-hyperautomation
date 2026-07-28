'use client'

import { Inbox, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { LoteStatusBadge } from '@/components/lote-status-badge'
import type { Lote } from '@/lib/lotes'

type Props = {
  lotes: Lote[]
  onDelete: (id: string) => void
}

function formatarData(iso: string) {
  const d = new Date(iso)
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function LotesList({ lotes, onDelete }: Props) {
  if (lotes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 border border-dashed border-border py-16 text-center">
        <Inbox className="size-8 text-muted-foreground" aria-hidden="true" />
        <div>
          <p className="text-sm font-medium">Nenhum lote cadastrado</p>
          <p className="text-sm text-muted-foreground">
            Cadastre um lote na aba &ldquo;Cadastro&rdquo; para vê-lo aqui.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nº do lote</TableHead>
            <TableHead>Produto</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Cadastrado em</TableHead>
            <TableHead className="text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {lotes.map((lote) => (
            <TableRow key={lote.id}>
              <TableCell className="font-mono font-medium">
                {lote.numero}
              </TableCell>
              <TableCell>{lote.produto}</TableCell>
              <TableCell>
                <LoteStatusBadge status={lote.status} />
              </TableCell>
              <TableCell className="text-muted-foreground">
                {formatarData(lote.criadoEm)}
              </TableCell>
              <TableCell className="text-right">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => onDelete(lote.id)}
                  aria-label={`Excluir lote ${lote.numero}`}
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
