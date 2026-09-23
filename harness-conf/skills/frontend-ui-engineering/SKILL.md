---
name: frontend-ui-engineering
description: >
  Use ao construir componentes ou páginas de UI, alterar interfaces visíveis
  ao usuário, implementar layouts responsivos, adicionar interatividade ou
  gerenciamento de estado, ou corrigir problemas visuais e de UX.
  Frontend de qualidade de produção: design system, acessibilidade e
  interações polidas.
  Triggers: "frontend", "UI",
  "component", "layout", "responsive", "CSS", "design system", "state
  management", "React", "Vue", "Angular", "Svelte", "accessibility",
  "interactivity", "animation", "theme", "dark mode", "mobile", "UX",
  "polished UI", "frontend engineering", "TypeScript component", "form",
  "modal",   "navigation", "design tokens", "Tailwind", "styled components".
---

# Frontend UI Engineering

Construa UI de qualidade de produção: acessível, performática e visualmente
acabada, com aderência real ao design system do projeto. O objetivo é UI que
parece feita por engenheiro com repertório de design, não gerada por IA.

## Arquitetura de componentes

Coloque tudo do componente junto:

```
src/components/
  TaskList/
    TaskList.tsx          # implementação
    TaskList.test.tsx     # testes
    TaskList.stories.tsx  # stories (se houver Storybook)
    use-task-list.ts      # hook (se o estado for complexo)
    types.ts              # tipos do componente (se necessário)
```

**Composição > configuração:**

```tsx
// Bom: composto por partes
<Card>
  <CardHeader><CardTitle>Tasks</CardTitle></CardHeader>
  <CardBody><TaskList tasks={tasks} /></CardBody>
</Card>

// Evite: sobreconfigurado
<Card title="Tasks" headerVariant="large" bodyPadding="md" content={<TaskList tasks={tasks} />} />
```

**Componente focado:** uma responsabilidade. `TaskItem` renderiza um item;
deleção e toggle ficam em props de callback, não no item.

**Separe busca de dados da apresentação:** container cuida de fetching e
estados (loading/error/empty), componente puro cuida do render:

```tsx
export function TaskListContainer() {
  const { tasks, isLoading, error } = useTasks();
  if (isLoading) return <TaskListSkeleton />;
  if (error) return <ErrorState message="Failed to load" retry={refetch} />;
  if (tasks.length === 0) return <EmptyState message="No tasks yet" />;
  return <TaskList tasks={tasks} />;
}

export function TaskList({ tasks }: { tasks: Task[] }) {
  return (
    <ul role="list" className="divide-y">
      {tasks.map(t => <TaskItem key={t.id} task={t} />)}
    </ul>
  );
}
```

## Gestão de estado

Escolha a abordagem mais simples que resolve:

| Estado | Onde |
|---|---|
| UI local do componente | `useState` |
| Compartilhado entre 2-3 irmãos | estado elevado |
| Theme, auth, locale (leitura frequente, escrita rara) | Context |
| Filtros, paginação, estado compartilhável | URL (`searchParams`) |
| Dados remotos com cache | React Query / SWR |
| Estado client complexo, app-wide | Zustand / Redux |

Evite prop drilling acima de 3 níveis: se props atravessam componentes que
não as usam, introduza Context ou reestruture a árvore.

## Design system

**Evite o padrão de estética de IA:**

| Padrão de IA | Produção |
|---|---|
| Roxo/índigo em tudo, gradientes excessivos | paleta e gradientes (ou flat) do design system |
| `rounded-2xl` em tudo | border-radius consistente com o sistema |
| Hero genérico, lorem ipsum, grid uniforme de cards | layout orientado a conteúdo e hierarquia de informação |
| Padding generoso e sombras em camadas | escala de espaçamento e sombras sutis (só se o sistema definir) |

**Espaçamento:** use a escala do projeto (ex.: incrementos de 0.25rem).
Não invente valores (`13px`, `2.3rem` fora da escala).

**Tipografia:** respeite a hierarquia: `h1` por página, `h2` por seção,
`h3` por subseção, `small` para texto auxiliar. Não pule níveis nem use
estilo de heading em conteúdo não-heading.

**Cor:** tokens semânticos (`text-primary`, `bg-surface`,
`border-default`), nunca hex solto. Contraste mínimo 4.5:1 (texto normal)
e 3:1 (texto grande). Nunca transmita informação só por cor: use ícone,
texto ou padrão junto.

## Acessibilidade (WCAG 2.1 AA)

**Teclado:** todo elemento interativo acessível por teclado. `<button>` já
é; `div` com `onClick` não é (e `role="button" tabIndex={0}` é pior que
usar `<button>`).

**ARIA:** rotule elementos interativos sem texto visível
(`<button aria-label="Close dialog">`) e inputs
(`<label htmlFor="email">` ou `aria-label`).

**Foco:** mova o foco quando conteúdo muda (ex.: dialog abre → foca o botão
de fechar) e prenda o foco dentro de dialogs.

**Estados vazios e de erro:** nunca tela em branco. Estado vazio mostra
ícone, explicação e ação (`No tasks yet` + botão `Create Task`); erro
mostra mensagem e retry.

## Responsive

Mobile first, depois expanda:

```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
```

Teste em 320px, 768px, 1024px, 1440px.

## Loading e transições

- Skeleton (não spinner) para conteúdo: blocos com `animate-pulse`,
  `aria-busy="true"` e `aria-label` de loading.
- Atualização otimista para velocidade percebida: mutate no cache local,
  rollback em erro (React Query: `onMutate` com `cancelQueries` +
  `setQueryData`, `onError` restaura o snapshot).
- Code splitting e lazy loading para bundles grandes:
  `lazy(() => import(...))` + `<Suspense>`.

Para requisitos e testes de acessibilidade detalhados, veja
`references/accessibility-checklist.md`.

## Anti-racionalizações

| Racionalização | Realidade |
|---|---|
| "Acessibilidade é nice-to-have" | Exigência legal em várias jurisdições e padrão de qualidade. |
| "Responsivo depois" | Retrofitar responsive é 3x mais caro que construir desde o início. |
| "O design não é final" | Use os defaults do design system; UI sem estilo quebra a 1ª impressão. |
| "É só protótipo" | Protótipo vira código de produção; construa a base certa. |
| "A estética de IA serve por ora" | Sinaliza baixa qualidade; use o design system do projeto desde o começo. |

## Red flags

Componente com mais de 200 linhas (divida); estilo inline ou pixel
arbitrário; estado de erro, loading ou vazio ausente; navegação por
teclado não testada; cor como único indicador; cara de IA (gradiente
roxo, cards gigantes, layout de template).

## Verificação

- [ ] Componente renderiza sem erro no console
- [ ] Todos os interativos navegáveis por teclado (Tab na página toda)
- [ ] Screen reader transmite conteúdo e estrutura
- [ ] Funciona em 320px, 768px, 1024px e 1440px
- [ ] Loading, erro e vazio tratados
- [ ] Aderente ao design system (espaçamento, cor, tipografia)
- [ ] Sem warning de acessibilidade (dev tools ou axe-core)
