# Design System · LG Adaptable Dark System (The DX Way)

## 🎨 Paleta de Cores Oficial (LG Brand Guidelines Dark)

### Base Dark & Superfícies
- `--lg-black`: `#000000` (Preto Absoluto — Fundo principal)
- `--lg-surface-1`: `#181818` (Superfície primária / Painéis de fundo)
- `--lg-surface-2`: `#242424` (Cards, tabelas e menus flutuantes)
- `--lg-surface-3`: `#2E2E2E` (Charcoal — Superfícies elevadas, inputs e hovers)
- `--lg-border`: `#383838` (Linhas de contenção e divisores sutis)
- `--lg-border-subtle`: `rgba(255, 255, 255, 0.08)`

### The Red Spectrum (Cores de Destaque)
- `--lg-active-red`: `#FD312E` (Vermelho Ativo — Botões primários, foco ativo, badges de destaque)
- `--lg-heritage-red`: `#A50034` (Vermelho Legado — Identidade institucional, logotipo e gradiente atmosférico)
- `--lg-active-red-hover`: `#e02421`
- `--lg-active-red-muted`: `rgba(253, 49, 46, 0.12)`

### Tipografia & Neutros
- `--lg-text-pure`: `#FFFFFF` (Branco Puro — Títulos e dados críticos com contraste AAA)
- `--lg-text-main`: `#F0F0F0` (Corpo de texto e células de tabela)
- `--lg-text-muted`: `#A3A3A3` (Subtítulos, instruções e rótulos de formulário)
- `--lg-text-dim`: `#737373` (Metadados secundários e carimbos de tempo)

### Cores Semânticas de Estado
- `--status-success`: `#10b981` / `--status-success-bg`: `rgba(16, 185, 129, 0.12)` (Lotes Válidos / OK)
- `--status-warning`: `#f59e0b` / `--status-warning-bg`: `rgba(245, 158, 11, 0.12)` (Ambíguos / Revisão Humana)
- `--status-error`: `#ef4444` / `--status-error-bg`: `rgba(239, 68, 68, 0.12)` (Divergências / Dead Letter)
- `--status-info`: `#38bdf8` / `--status-info-bg`: `rgba(56, 189, 248, 0.12)` (Informações de Pipeline)

### Gradiente Assinatura Dark
```css
background: radial-gradient(circle at 10% 10%, rgba(165, 0, 52, 0.18) 0%, transparent 45%),
            radial-gradient(circle at 90% 90%, rgba(165, 0, 52, 0.08) 0%, transparent 40%),
            #000000;
```

---

## 📐 Tipografia & Escala (Legibilidade Impeccable)

- **Famílias:**
  - Display / Títulos: `'Outfit'`, system-ui, sans-serif (pesos 600, 700)
  - Interface / Corpo: `'Inter'`, system-ui, sans-serif (pesos 400, 500, 600)
  - Código / IDs: `'JetBrains Mono'`, monospace (pesos 500, 600)
- **Escala de Tamanhos (Mínimo de 12px para leitura, 11px para micro-tags):**
  - Textos de Suporte / Tags: `12px` (`0.75rem`), peso 600
  - Rótulos & Células: `14px` (`0.875rem`), peso 400/500
  - Corpo Principal: `15px` (`0.9375rem`), peso 400/500
  - Subtítulos de Seção: `16px` (`1rem`), peso 600
  - Títulos de Seção: `20px` (`1.25rem`), peso 700
  - Título do Header / Hero: `24px` (`1.5rem`), peso 700

---

## 🧱 Componentes & Padrões Sem Anti-Patterns

1. **Cards & Elevação:**
   - Fundo em `--lg-surface-2` com borda de 1px em `--lg-border`.
   - Sombra sutil natural: `0 4px 20px rgba(0, 0, 0, 0.45)`.
   - **Sem halos luminosos fluorescentes artificiais** (`no zero-offset dark-glows`).
   - **Sem listras laterais grossas arbitrárias** (`no thick side-tabs`).
2. **Botões:**
   - Primário: Fundo sólido em `--lg-active-red` com texto `#FFFFFF`. Foco visível com anel de 2px `--lg-active-red` e offset de 2px.
   - Secundário / Ghost: Fundo `--lg-surface-3` com borda `--lg-border` e hover sutil.
3. **Tabelas:**
   - Inset e padding interno de no mínimo 12px a 16px.
   - Cabeçalhos contrastados em `--lg-surface-3` com texto `--lg-text-pure`.
