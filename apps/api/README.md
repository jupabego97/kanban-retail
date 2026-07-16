# Kanban Retail API — Captura de Demanda Insatisfecha

Backend en **FastAPI + SQLModel** para gestionar la demanda insatisfecha de una tienda
(productos agotados, no manejados o novedades) mediante un tablero Kanban con maquina
de estados estricta. Diseñado como **single-tenant por tienda**.

## Stack

- FastAPI + SQLModel (SQLAlchemy sincrono)
- Alembic para migraciones (portable SQLite / PostgreSQL)
- Pydantic v2 + pydantic-settings
- Argon2 para hashing de contraseñas
- Sesiones por cookie firmada (itsdangerous), `HttpOnly` + `SameSite=lax` (+ `Secure` en produccion)
- pytest

## Estructura

```
apps/api/
  requirements.txt
  alembic.ini
  alembic/                 # migraciones
  app/
    main.py                # creacion de la app + handlers de error
    config.py              # settings desde entorno
    db.py                  # engine y sesiones
    enums.py               # enumeraciones del dominio
    errors.py              # errores de dominio con codigos estables
    state_machine.py       # maquina de estados estricta
    logging_setup.py       # logging JSON
    middleware.py          # security headers + rate limiting
    models/                # modelos SQLModel
    schemas/               # esquemas Pydantic
    api/                   # routers
    services/              # logica de negocio
    security/              # password, sesion, dependencias RBAC
    catalog/               # proveedor de catalogo (CSV manual v1)
  tests/                   # unit + integracion
  scripts/seed.py          # datos de demostracion
  .env.example
```

## Puesta en marcha (Windows PowerShell)

```powershell
cd D:\Desktop\python\kanban-retail\apps\api
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env   # y ajustar valores
```

### Migraciones (PostgreSQL o SQLite)

```powershell
$env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/kanban_retail"
.\.venv\Scripts\alembic upgrade head
```

### Cargar datos de demostracion

```powershell
.\.venv\Scripts\python -m scripts.seed
```

Usuarios creados por el seed:

| Rol      | Email                   | Contraseña     |
|----------|-------------------------|----------------|
| OWNER    | admin@tienda.local      | `Admin123!`    |
| MANAGER  | gerente@tienda.local    | `Manager123!`  |
| OPERATOR | operador@tienda.local   | `Operator123!` |
| VIEWER   | consulta@tienda.local   | `Viewer123!`   |

### Ejecutar el servidor

```powershell
.\.venv\Scripts\uvicorn app.main:app --reload
```

Documentacion interactiva en `http://localhost:8000/docs`.

## Tests

```powershell
$env:DATABASE_URL = "sqlite:///./test.db"
.\.venv\Scripts\python -m pytest -q
```

Los tests de integracion usan SQLite en memoria y no requieren PostgreSQL.

## Maquina de estados

```
NUEVA -> VALIDANDO -> COTIZANDO -> POR_PEDIR -> EN_CAMINO -> DISPONIBLE -> CERRADA
```

Ademas, cualquier estado **abierto** puede pasar a `DESCARTADA`. Los estados
`CERRADA` y `DESCARTADA` son terminales. Cada cambio registra `StatusHistory`.

## Endpoints principales

- `GET /api/health`
- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- `GET/POST/PATCH/DELETE /api/users` (OWNER/MANAGER)
- `GET/POST/PATCH/DELETE /api/suppliers`
- `GET/POST/PATCH/DELETE /api/products` (+ busqueda `?q=`)
- `GET/POST/PATCH/DELETE /api/demands`
  - `GET /api/demands/board` — tablero agrupado por estado
  - `PATCH /api/demands/{id}/status` — cambio de estado con control de version
  - `PATCH /api/demands/reorder` — reordenamiento
  - `POST /api/demands/{id}/consolidate` — consolidar interes de cliente
- `POST /api/imports/preview`, `POST /api/imports/commit` (products/suppliers)
- `GET /api/metrics` — KPIs
- `GET /api/audit` (MANAGER+)

## Seguridad

- Todas las rutas requieren autenticacion salvo `/api/health` y `/api/auth/login`.
- Cookies de sesion firmadas, `HttpOnly`, `SameSite=lax`, `Secure` en produccion.
- RBAC con `require_roles(...)`.
- Cabeceras de seguridad y rate limiting simple en memoria.
- Los errores nunca exponen SQL crudo: se devuelven codigos de error estables.
