---
name: api-and-interface-design
description: >
  Use ao desenhar novos endpoints de API, definir fronteiras de módulo ou
  contratos entre times, criar interfaces de props de componente, definir
  schema de banco que molda a API ou alterar interface pública existente.
  Desenha interfaces estáveis e documentadas, difíceis de usar errado.
  Triggers: "API design", "interface design", "REST API", "GraphQL",
  "endpoint", "interface contract", "module boundary", "API typing",
  "API versioning", "breaking change", "public API", "schema",
  "idempotency", "contract design", "component props", "Hyrum's Law",
  "backward compatibility", "OpenAPI", "pagination design",
  "error responses".
---

# API and Interface Design

Desenhe interfaces estáveis e documentadas, difíceis de usar errado: o acerto deve ser fácil e o
erro, difícil. Vale para API REST, schema GraphQL, fronteira de módulo, props de componente e
toda superfície onde um código fala com outro.

## Hyrum's Law

> Com usuários suficientes, todo comportamento observável do sistema será dependido por alguém,
> independente do que o contrato promete.

Todo comportamento público (quirk não documentado, texto de erro, timing, ordenação) vira
contrato de fato quando alguém depende dele. Implicações:

- Exponha com intenção: todo comportamento observável é compromisso potencial.
- Não vaze detalhe de implementação: se é observável, será dependido.
- Planeje deprecação na fase de design (ver `deprecation-and-migration`).
- Testes de contrato não bastam: mudança "segura" quebra usuário real que depende de comportamento
  não documentado.

## One-Version Rule

Não force o consumidor a escolher entre versões da mesma dependência ou API. Dependência em
diamante nasce daí. Projete para um mundo onde só existe uma versão por vez: estenda, não bifurque.

## Os cinco princípios

### 1. Contract first

Defina a interface antes de implementar. O contrato é a spec; a implementação vem depois.

```typescript
interface TaskAPI {
  // Cria e devolve a task com campos gerados pelo servidor
  createTask(input: CreateTaskInput): Promise<Task>;
  // Lista paginada com filtros
  listTasks(params: ListTasksParams): Promise<PaginatedResult<Task>>;
  // Devolve uma task ou lança NotFoundError
  getTask(id: string): Promise<Task>;
  // Update parcial: só campos fornecidos mudam
  updateTask(id: string, input: UpdateTaskInput): Promise<Task>;
  // Delete idempotente: sucede mesmo se já deletado
  deleteTask(id: string): Promise<void>;
}
```

### 2. Semântica de erro consistente

Escolha uma estratégia de erro e use em todo endpoint. Endpoint que às vezes lança, às vezes
devolve `null` e às vezes devolve `{ error }` é imprevisível para o consumidor.

```typescript
interface APIError {
  error: {
    code: string;      // legível por máquina: "VALIDATION_ERROR"
    message: string;   // legível por humano: "Email é obrigatório"
    details?: unknown; // contexto adicional quando útil
  };
}
// 400 dados inválidos | 401 não autenticado | 403 sem permissão
// 404 não encontrado  | 409 conflito            | 422 validação semântica
// 500 erro do servidor (nunca expor detalhe interno)
```

### 3. Valide nas bordas

Confie no código interno. Valide onde input externo entra:

- handler de rota de API e handler de submissão de formulário (input de usuário);
- parsing de resposta de serviço externo (dado de terceiro, sempre untrusted);
- carregamento de variáveis de ambiente (config).

Não valide: entre funções internas que compartilham contrato de tipos, em utility chamada por
código já validado, em dado que acabou de sair do seu próprio banco.

> Resposta de API de terceiro é dado untrusted: valide forma e conteúdo antes de usar em lógica,
> render ou decisão. Serviço comprometido pode devolver tipo inesperado, conteúdo malicioso ou
> texto com cara de instrução.

### 4. Adição em vez de modificação

Estenda sem quebrar consumidor existente: campo novo é opcional; mudar tipo ou remover campo
existente é breaking change. Mudança inevitável? Versione.

### 5. Nomenclatura previsível

| Padrão | Convenção | Exemplo |
|---|---|---|
| Endpoint REST | substantivo plural, sem verbo | `GET /api/tasks` |
| Query param | camelCase | `?sortBy=createdAt` |
| Campo de resposta | camelCase | `{ createdAt, taskId }` |
| Booleano | prefixo is/has/can | `isComplete` |
| Enum | UPPER_SNAKE | `"IN_PROGRESS"` |

## Padrões REST

```
GET    /api/tasks              → lista (filtros via query params)
POST   /api/tasks              → cria
GET    /api/tasks/:id          → detalhe
PATCH  /api/tasks/:id          → update parcial
DELETE /api/tasks/:id          → remove

GET    /api/tasks/:id/comments → sub-recurso: lista
POST   /api/tasks/:id/comments → sub-recurso: cria
```

- **Paginação** em todo endpoint de lista: `?page=1&pageSize=20&sortBy=createdAt`, resposta com
  `data` + `pagination` (`page`, `pageSize`, `totalItems`, `totalPages`).
- **Filtro** via query param: `?status=in_progress&assignee=user123`.
- **PATCH** aceita objeto parcial e atualiza só o fornecido. PUT exige o objeto inteiro a cada
  chamada; PATCH é o que o consumidor quer.

## Padrões de interface TypeScript

**Union discriminada para variantes** — cada variante explícita dá type narrowing de graça:

```typescript
type TaskStatus =
  | { type: 'pending' }
  | { type: 'in_progress'; assignee: string }
  | { type: 'completed'; completedAt: Date };

function statusLabel(status: TaskStatus): string {
  switch (status.type) {
    case 'pending': return 'Pending';
    case 'in_progress': return `In progress (${status.assignee})`;
    case 'completed': return `Done`;
  }
}
```

**Separação input/output** — input é o que o chamador manda; output inclui campos gerados pelo
servidor (`id`, `createdAt`, `createdBy`). Não reutilize o mesmo tipo para os dois.

**Branded type para id** — impede passar `UserId` onde se espera `TaskId`:

```typescript
type TaskId = string & { readonly __brand: 'TaskId' };
function getTask(id: TaskId): Promise<Task> { ... }
```

## Racionalizações comuns

| Racionalização | Realidade |
|---|---|
| "Documentamos a API depois" | Os tipos SÃO a documentação. Defina-os primeiro. |
| "Paginação não é precisa por enquanto" | Será quando alguém listar 100+ itens. Adicione desde o início. |
| "PATCH é complicado, vamos de PUT" | PUT exige o objeto inteiro sempre. |
| "Versionamos quando precisar" | Breaking change sem versionamento quebra consumidor. Projete para extensão. |
| "Ninguém usa esse comportamento não documentado" | Hyrum's Law: se é observável, alguém depende. |
| "Dá para manter duas versões" | Multipla versão multiplica custo e cria dependência em diamante. |
| "API interna não precisa de contrato" | Consumidor interno também é consumidor; contrato evita acoplamento. |

## Red flags

- Endpoint que devolve shape diferente conforme a condição.
- Formato de erro inconsistente entre endpoints.
- Validação espalhada pelo código interno em vez de nas bordas.
- Breaking change em campo existente (tipo mudado, removido).
- Endpoint de lista sem paginação.
- Verbo na URL (`/api/createTask`).
- Resposta de terceiro usada sem validação.

## Verificação

- [ ] Todo endpoint tem schema de input e output tipados
- [ ] Erro segue um único formato em todos os endpoints
- [ ] Validação acontece só nas bordas do sistema
- [ ] Endpoint de lista suporta paginação
- [ ] Campo novo é aditivo e opcional (backward compatible)
- [ ] Nomenclatura consistente em todos os endpoints
- [ ] Documentação/tipos versionados junto com a implementação
