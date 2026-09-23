---
name: security-and-hardening
description: >
  Use ao lidar com input de usuário, implementar autenticação ou
  autorização, armazenar ou transmitir dados sensíveis, integrar com APIs
  externas, adicionar upload de arquivos, webhooks, callbacks, ou lidar com
  pagamento e PII. Desenvolvimento security-first para web (OWASP Top 10,
  secrets, hardening).
  Triggers: "security",
  "hardening", "OWASP", "XSS", "SQL injection", "CSRF", "input sanitization",
  "authentication", "authorization", "sensitive data", "secrets management",
  "encryption", "vulnerability", "CVE", "rate limiting", "CORS", "CSP",
  "zero-trust", "API security", "JWT", "session management", "penetration
  testing", "threat model", "secure coding".
---

# Security and Hardening

Security-first development for web applications. Treat every external
input as hostile, every secret as sacred, every authorization check as
mandatory. Security is a constraint on every line of code that touches
user data, auth, or external systems — not a final phase.

## The Three-Tier Boundary System

### Always Do (no exceptions)

- **Validate all external input** at the system boundary (API routes, form handlers)
- **Parameterize all database queries** — never concatenate user input into SQL
- **Encode output** to prevent XSS (use framework auto-escaping; don't bypass it)
- **Use HTTPS** for all external communication
- **Hash passwords** with bcrypt/scrypt/argon2 (never plaintext)
- **Set security headers** (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- **Use httpOnly, secure, sameSite cookies** for sessions
- **Run `npm audit`** (or equivalent) before every release

### Ask First (requires human approval)

- New or changed authentication flows
- Storing new categories of sensitive data (PII, payment)
- New external service integrations
- CORS changes
- New file upload handlers
- Rate limiting or throttling changes
- Elevated permissions or roles

### Never Do

- **Never commit secrets** to version control (API keys, passwords, tokens)
- **Never log sensitive data** (passwords, tokens, card numbers)
- **Never trust client-side validation** as a security boundary
- **Never disable security headers** for convenience
- **Never use `eval()` or `innerHTML`** with user-provided data
- **Never store session tokens in client-accessible storage** (localStorage)
- **Never expose stack traces** or internal error details to users

## OWASP Top 10 Patterns

### Injection (SQL, NoSQL, command)

```typescript
// BAD: string concatenation
const query = `SELECT * FROM users WHERE id = '${userId}'`;
// GOOD: parameterized query
const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
```

### Broken authentication

```typescript
const hashedPassword = await hash(plaintext, 12);          // bcrypt, ≥12 rounds
const isValid = await compare(plaintext, hashedPassword);

app.use(session({
  secret: process.env.SESSION_SECRET,   // from environment, not code
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true, secure: true, sameSite: 'lax', maxAge: 24 * 60 * 60 * 1000 },
}));
```

### XSS

```typescript
// BAD: rendering user input as HTML
element.innerHTML = userInput;
// GOOD: framework auto-escaping (React default)
return <div>{userInput}</div>;
// If you MUST render HTML, sanitize first:
const clean = DOMPurify.sanitize(userInput);
```

### Broken access control

Authorization on every endpoint, not just authentication. Check ownership:

```typescript
app.patch('/api/tasks/:id', authenticate, async (req, res) => {
  const task = await taskService.findById(req.params.id);
  if (task.ownerId !== req.user.id) {
    return res.status(403).json({ error: { code: 'FORBIDDEN', message: 'Not authorized' } });
  }
  return res.json(await taskService.update(req.params.id, req.body));
});
```

### Misconfiguration (headers, CORS)

```typescript
app.use(helmet());   // security headers
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"], scriptSrc: ["'self'"],
    styleSrc: ["'self'", "'unsafe-inline'"],
    imgSrc: ["'self'", 'data:', 'https:'], connectSrc: ["'self'"],
  },
}));
app.use(cors({ origin: process.env.ALLOWED_ORIGINS?.split(','), credentials: true }));
```

### Sensitive data exposure

```typescript
function sanitizeUser(user: UserRecord): PublicUser {
  const { passwordHash, resetToken, ...publicFields } = user;
  return publicFields;   // never return sensitive fields in API responses
}
const API_KEY = process.env.STRIPE_API_KEY;
if (!API_KEY) throw new Error('STRIPE_API_KEY not configured');
```

## Input Validation

Validate at the boundary with a schema; the parsed result is typed and
trusted:

```typescript
const CreateTaskSchema = z.object({
  title: z.string().min(1).max(200).trim(),
  description: z.string().max(2000).optional(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  dueDate: z.string().datetime().optional(),
});

app.post('/api/tasks', async (req, res) => {
  const result = CreateTaskSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(422).json({ error: { code: 'VALIDATION_ERROR', details: result.error.flatten() } });
  }
  return res.status(201).json(await taskService.create(result.data));
});
```

File uploads: restrict MIME type and size; don't trust the file extension
(check magic bytes if critical).

```typescript
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_SIZE = 5 * 1024 * 1024; // 5MB
```

## Rate Limiting

```typescript
app.use('/api/', rateLimit({ windowMs: 15 * 60 * 1000, max: 100, standardHeaders: true, legacyHeaders: false }));
// Stricter limit for auth endpoints:
app.use('/api/auth/', rateLimit({ windowMs: 15 * 60 * 1000, max: 10 }));
```

## Secrets Management

```
.env.example → committed (template with placeholders)
.env         → NOT committed (real secrets)
.env.local   → NOT committed (local overrides)

.gitignore must include: .env, .env.local, .env.*.local, *.pem, *.key
```

Before committing:

```bash
git diff --cached | grep -i "password\|secret\|api_key\|token"
```

## Triage npm audit Results

Not all findings need immediate action. Ask, in order:

1. Severity: critical/high → Is the vulnerable code reachable?
   - Reachable → fix now (update, patch, or replace the dependency)
   - Not reachable (dev-only dep, unused path) → fix soon, not a blocker
2. Severity: moderate → reachable in production means next release cycle;
   dev-only means backlog
3. Severity: low → fix during regular dependency updates

When deferring, document the reason and set a review date.

## Security Checklist (run before merge)

**Authentication**
- [ ] Passwords hashed (bcrypt/scrypt/argon2, salt rounds ≥ 12)
- [ ] Session tokens httpOnly, secure, sameSite; reset tokens expire
- [ ] Rate limiting on login

**Authorization**
- [ ] Every endpoint checks permissions; users access only their own resources
- [ ] Admin actions verified by role

**Input**
- [ ] All user input validated at the boundary; SQL parameterized; output encoded

**Data & infrastructure**
- [ ] No secrets in code, config, or git history; PII encrypted at rest
- [ ] Security headers present (verify in DevTools); CORS restricted to known origins
- [ ] `npm audit` clean of critical/high; error responses don't expose internals

For detailed checklists and pre-commit verification steps, see
`references/security-checklist.md`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's an internal tool" | Internal tools get compromised too |
| "We'll add security later" | Retrofitting is 10x harder; build it in now |
| "No one would exploit this" | Automated scanners will find it |
| "The framework handles it" | Frameworks provide tools, not guarantees |
| "It's just a prototype" | Prototypes become production; habits start day one |
