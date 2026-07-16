# Kanban Retail

Plataforma profesional de **demanda no atendida** para comercios (single-tenant).

Captura en mostrador → priorización Kanban → catálogo/proveedores → métricas accionables.

## Stack

| Capa | Tecnología |
|------|------------|
| Frontend | Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + dnd-kit + Recharts |
| Backend | FastAPI + SQLModel + Alembic + PostgreSQL |
| Auth | Sesión por cookie firmada + Argon2 + RBAC |
| Deploy | API/DB en Railway · Web en Vercel o Railway |

## Estructura

```
kanban-retail/
  apps/api/     # FastAPI
  apps/web/     # Next.js
  packages/     # contratos OpenAPI tipados
  docs/         # provisioning y migración
```

## Arranque local

### API

```bash
cd apps/api
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\python -m scripts.seed
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Credenciales seed: `admin@tienda.local` / `Admin123!`

Docs: http://localhost:8000/docs

### Web

```bash
cd apps/web
copy .env.example .env.local
npm install
npm run dev
```

App: http://localhost:3000

## Roles

- **OWNER** / **MANAGER**: usuarios, importaciones, borrado
- **OPERATOR**: captura y movimiento de tarjetas
- **VIEWER**: solo lectura

## Máquina de estados

`NUEVA → VALIDANDO → COTIZANDO → POR_PEDIR → EN_CAMINO → DISPONIBLE → CERRADA`

Cualquier estado abierto → `DESCARTADA`.

## CI

GitHub Actions: tests API (pytest) + lint/typecheck/build del frontend.

## Provisioning

Ver [docs/provisioning.md](docs/provisioning.md).
