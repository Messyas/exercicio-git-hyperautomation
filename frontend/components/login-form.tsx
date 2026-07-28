'use client'

import { useState } from 'react'
import { Boxes, Lock, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

type LoginFormProps = {
  onLogin: (usuario: string) => void
}

export function LoginForm({ onLogin }: LoginFormProps) {
  const [usuario, setUsuario] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!usuario.trim() || !senha.trim()) {
      setErro('Informe usuário e senha para continuar.')
      return
    }

    setErro(null)
    onLogin(usuario.trim())
  }

  return (
    <main className="flex min-h-svh items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <div className="flex size-12 items-center justify-center border border-border bg-primary text-primary-foreground">
            <Boxes className="size-6" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-balance">
              Sistema de Lotes
            </h1>
            <p className="text-sm text-muted-foreground">
              Acesse para gerenciar os lotes de produção.
            </p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Entrar</CardTitle>
            <CardDescription>
              Use qualquer usuário e senha para acessar a demonstração.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <div className="flex flex-col gap-2">
                <Label htmlFor="usuario">Usuário</Label>
                <div className="relative">
                  <User
                    className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
                    aria-hidden="true"
                  />
                  <Input
                    id="usuario"
                    value={usuario}
                    onChange={(e) => setUsuario(e.target.value)}
                    placeholder="seu.usuario"
                    className="pl-9"
                    autoComplete="username"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="senha">Senha</Label>
                <div className="relative">
                  <Lock
                    className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
                    aria-hidden="true"
                  />
                  <Input
                    id="senha"
                    type="password"
                    value={senha}
                    onChange={(e) => setSenha(e.target.value)}
                    placeholder="••••••••"
                    className="pl-9"
                    autoComplete="current-password"
                  />
                </div>
              </div>

              {erro && (
                <p
                  role="alert"
                  className="border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
                >
                  {erro}
                </p>
              )}

              <Button type="submit" className="w-full">
                Entrar
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          Ambiente de demonstração &mdash; nenhuma credencial é validada.
        </p>
      </div>
    </main>
  )
}
