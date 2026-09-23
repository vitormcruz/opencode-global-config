---
name: performance-optimization
description: >
  Use quando houver requisito de performance na spec, usuarios ou
  monitoramento reportarem lentidão, Core Web Vitals abaixo do limiar,
  suspeita de regressão, ou ao construir feature com grande volume de dados
  ou tráfego. Mede antes de otimizar e corrige gargalos comprovados.
  Triggers: "performance", "optimization", "Core Web Vitals",
  "LCP", "FCP", "CLS", "TTI", "slow", "bottleneck", "profiling", "benchmark",
  "response time SLA", "load time", "bundle size", "lazy loading", "caching",
  "memoization", "performance regression", "throughput", "N+1 query",
  "memory leak", "render blocking", "lighthouse score".
---

# Performance Optimization

Meça antes de otimizar. Performance sem medição é chute, e chute gera
otimização prematura que adiciona complexidade sem melhorar o que importa.
Perfil primeiro, ache o gargalo real, corrija, meça de novo. Otimize só o
que a medição prova que importa.

**Quando não usar:** sem evidência de problema, não otimize. Otimização
prematura custa mais que a performance que ganha.

## Core Web Vitals (alvos)

| Métrica | Bom | Precisa melhorar | Ruim |
|---|---|---|---|
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | ≤ 200ms | ≤ 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | ≤ 0.25 | > 0.25 |

## Workflow

```
1. MEASURE  → baseline com dados reais
2. IDENTIFY → gargalo real (não presumido)
3. FIX      → o gargalo específico
4. VERIFY   → medir de novo, confirmar ganho
5. GUARD    → monitoramento ou teste contra regressão
```

### Medir

Duas abordagens complementares, use as duas:

- **Sintética** (Lighthouse, aba Performance do DevTools): condições
  controladas e reproduzíveis; melhor para detectar regressão em CI e
  isolar problema.
- **RUM** (`web-vitals`, CrUX): dados de usuários reais; necessário para
  confirmar que o fix melhorou a experiência.

```ts
import { onLCP, onINP, onCLS } from 'web-vitals';
onLCP(console.log); onINP(console.log); onCLS(console.log);
```

Backend: log de tempo de resposta, APM, log de query com timing
(`console.time`/`console.timeEnd`).

### Por onde começar (sintoma → medição)

```
Load inicial lento?
├── Bundle grande?          → medir tamanho, checar code splitting
├── Resposta do server?     → TTFB no waterfall de rede
│   ├── DNS longo?          → dns-prefetch / preconnect dos origins
│   ├── TCP/TLS longo?      → HTTP/2, edge, keep-alive
│   └── Waiting longo?      → profile do backend, queries, cache
└── Recursos render-blocking? → waterfall: CSS/JS bloqueando

Interação lenta?
├── UI congela no clique?   → main thread, long tasks (>50ms)
├── Input com lag?          → re-renders, overhead de controlled input
└── Animação engasga?       → layout thrashing, reflow forçado

Pós-navegação lenta?
├── Carregando dados?       → tempo de API, waterfalls
└── Render no client?       → tempo de render, N+1 de fetch

Backend lento?
├── Um endpoint?            → profile de queries, índices
├── Todos os endpoints?     → connection pool, memória, CPU
└── Intermitente?           → lock contention, pausas de GC, deps externas
```

### Identificar gargalos

**Frontend:**

| Sintoma | Causa provável | Investigação |
|---|---|---|
| LCP lento | imagem grande, recursos render-blocking, server lento | waterfall, tamanho de imagens |
| CLS alto | imagem sem dimensões, conteúdo tardio, font shift | layout shift attribution |
| INP ruim | JS pesado na main thread, DOM grande | long tasks no trace |
| Load inicial lento | bundle grande, requests demais | tamanho de bundle, code splitting |

**Backend:**

| Sintoma | Causa provável | Investigação |
|---|---|---|
| API lenta | N+1, índice faltando, query ruim | log de queries do banco |
| Memória crescente | referências vazadas, cache sem limite, payload grande | heap snapshot |
| CPU em pico | computação pesada síncrona, regex backtracking | CPU profiling |
| Latência alta | cache faltando, recomputação, saltos de rede | trace da request na stack |

### Corrigir anti-padrões comuns

**N+1 queries** (uma query por item do loop):

```ts
// Ruim: N+1
for (const task of tasks) {
  task.owner = await db.users.findUnique({ where: { id: task.ownerId } });
}
// Bom: uma query com include
const tasks = await db.tasks.findMany({ include: { owner: true } });
```

**Busca sem limite:** sempre paginar (`take`/`skip` + `orderBy`), nunca
`findMany()` sem limite em endpoint de lista.

**Imagens:** sempre `width`/`height` (evita CLS), formato moderno
(AVIF/WebP), LCP image com `fetchpriority="high"`, below-the-fold com
`loading="lazy" decoding="async"`, art direction com `<picture>`
(`media` + `srcset`/`sizes`) quando o crop varia por breakpoint.

**Re-render desnecessário (React):** referência estável para objetos/arrays
passados como props (constant fora do componente), `React.memo` para
componente caro, `useMemo` para computação cara. Sem exagerar: memo em
tudo é tão ruim quanto nada.

**Bundle grande:** dynamic import para feature pesada de uso raro e
route-level code splitting com `<Suspense>`. Bundlers modernos fazem
tree-shaking de named imports se o pacote é ESM com
`sideEffects: false`: profile antes de trocar estilo de import.

**Cache ausente (backend):** cache de config e dado lido com frequência e
mudado raramente (TTL explícito); headers HTTP para assets estáticos
(`max-age` longo + `immutable` com filename hasheado);
`Cache-Control: public, max-age=300` para resposta de API cacheável.

## Performance budget

Defina orçamento e imponha:

```
JS bundle: < 200KB gzipped (initial load)
CSS: < 50KB gzipped
Imagens: < 200KB por imagem (above the fold)
Fontes: < 100KB total
API response: < 200ms (p95)
Time to Interactive: < 3.5s em 4G
Lighthouse Performance: ≥ 90
```

CI: `npx bundlesize --config bundlesize.config.json` e
`npx lhci autorun`.

Checklists detalhados, comandos de otimização e referência de
anti-padrões: `references/performance-checklist.md`.

## Anti-racionalizações

| Racionalização | Realidade |
|---|---|
| "Otimizo depois" | Dívida de performance compõe; resolva anti-padrão óbvio agora, micro-otimização depois. |
| "No meu computador é rápido" | Sua máquina não é a do usuário; profile em hardware e rede representativos. |
| "Essa otimização é óbvia" | Se não mediu, não sabe. Profile primeiro. |
| "Usuário não nota 100ms" | Pesquisa mostra impacto de 100ms em conversão; usuário nota mais do que parece. |
| "O framework resolve" | Framework previne alguns problemas; não resolve N+1 nem bundle gigante. |

## Red flags

Otimização sem dado de profile que a justifique; N+1 no fetching; endpoint
de lista sem paginação; imagem sem dimensões, lazy loading ou tamanho
responsivo; bundle crescendo sem review; sem monitoramento de performance
em produção; `React.memo`/`useMemo` em tudo.

## Verificação

- [ ] Medição antes e depois com números específicos
- [ ] Gargalo identificado e endereçado
- [ ] Core Web Vitals dentro de "Bom"
- [ ] Bundle não cresceu de forma relevante
- [ ] Sem N+1 no código novo de fetching
- [ ] Performance budget passa no CI (se configurado)
- [ ] Testes existentes passam (a otimização não quebrou comportamento)
