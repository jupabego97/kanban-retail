# Desplegar el frontend (URL de la aplicación) en Railway

Hoy solo tienes la **API**. La URL de la app es otro servicio: **Next.js** en `apps/web`.

## 1. Crear servicio Web

En el mismo proyecto Railway:

1. **+ New** → **GitHub Repo** → `jupabego97/kanban-retail` (o Add service from same repo)
2. Nombre sugerido: `web` o `kanban-retail-web`
3. Settings del servicio **web**:
   - **Root Directory:** vacío / `/`
   - **Config as Code path:** `/apps/web/railway.toml`
4. Variables del servicio **web**:
   - `NEXT_PUBLIC_API_URL` = URL pública de tu API (ej. `https://kanban-retail-production.up.railway.app`) **sin** `/` final
5. Deploy

La URL pública del servicio **web** es la de la aplicación (login, tablero, etc.).

## 2. Actualizar la API (CORS + cookies)

En el servicio **api**, variables:

```text
CORS_ORIGINS=https://TU-FRONTEND.up.railway.app
ENVIRONMENT=production
COOKIE_SECURE=true
COOKIE_SAMESITE=none
```

Con front y API en hosts distintos de Railway, la sesión requiere `SameSite=None` + `Secure`
(si no, el navegador no reenvía la cookie y verás “No autenticado o sesión expirada”).

Redeploy de la API.

## 3. Seed (usuarios demo)

En el servicio API → Shell:

```bash
python -m scripts.seed
```

Login: `admin@tienda.local` / `Admin123!`

## Resumen

| Servicio | Config path | URL típica |
|----------|-------------|------------|
| api | `/railway.toml` | docs, `/api/health` |
| web | `/apps/web/railway.toml` | `/login`, tablero |
| Postgres | plugin | `DATABASE_URL` en api |
