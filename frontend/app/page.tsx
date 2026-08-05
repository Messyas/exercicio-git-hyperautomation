'use client'

import { useEffect, useState } from 'react'
import { Boxes, LogOut } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { LoteForm } from '@/components/lote-form'
import { LotesList } from '@/components/lotes-list'
import { LoginForm } from '@/components/login-form'
import { loadLotes, saveLotes, type Lote } from '@/lib/lotes'

export default function Page() {
  const [lotes, setLotes] = useState<Lote[]>([])
  const [aba, setAba] = useState('cadastro')
  const [usuario, setUsuario] = useState<string | null>(null)

  useEffect(() => {
    setLotes(loadLotes())
  }, [])

  if (!usuario) {
    return <LoginForm onLogin={setUsuario} />
  }

  function handleCreate(lote: Lote) {
    setLotes((prev) => {
      const next = [lote, ...prev]
      saveLotes(next)
      return next
    })
  }

  function handleDelete(id: string) {
    setLotes((prev) => {
      const next = prev.filter((l) => l.id !== id)
      saveLotes(next)
      return next
    })
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 md:py-12">
      <header className="mb-8 flex items-center gap-3 border-b border-border pb-6">
        <div className="flex size-10 items-center justify-center border border-border bg-primary text-primary-foreground">
          <Boxes className="size-5" aria-hidden="true" />
        </div>
        <div className="flex-1">
          <h1 className="text-xl font-semibold tracking-tight text-balance">
            Cadastro de Lotes
          </h1>
          <p className="text-sm text-muted-foreground">
            Registro e acompanhamento de lotes de produção.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-muted-foreground sm:inline">
            Olá, <span className="font-medium text-foreground">{usuario}</span>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setUsuario(null)}
          >
            <LogOut className="size-4" aria-hidden="true" />
            Sair
          </Button>
        </div>
      </header>

      <Tabs value={aba} onValueChange={setAba}>
        <TabsList>
          <TabsTrigger value="cadastro">Cadastro</TabsTrigger>
          <TabsTrigger value="lotes">
            Lotes cadastrados
            {lotes.length > 0 && (
              <span className="ml-2 inline-flex min-w-5 items-center justify-center border border-border bg-muted px-1 text-xs text-muted-foreground">
                {lotes.length}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="cadastro" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Novo lote</CardTitle>
              <CardDescription>
                Preencha os dados e clique em &ldquo;Processar lote&rdquo;. Os
                registros ficam salvos no cache local do navegador.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LoteForm onCreate={handleCreate} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="lotes" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Lotes cadastrados</CardTitle>
              <CardDescription>
                Lista dos lotes registrados neste navegador.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LotesList lotes={lotes} onDelete={handleDelete} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </main>
  )
}
