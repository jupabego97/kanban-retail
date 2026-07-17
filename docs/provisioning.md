# Provisioning por comercio (single-tenant)

Cada comercio recibe una instalación independiente: API + PostgreSQL en Railway y frontend (Vercel o Railway).

## Importante: Root Directory en Railway

Este repo es un **monorepo**. Si Railway construye desde la raíz detecta Node y falla con `No start command detected`.

Para el servicio de API:

1. Settings → **Root Directory** → `apps/api`
2. Redeploy

Para el frontend (si también va a Railway):

1. Settings → **Root Directory** → `apps/web`
2. Variable: `NEXT_PUBLIC_API_URL=https://tu-api.up.railway.app`

## Checklist

1. Crear proyecto Railway y base PostgreSQL.
2. Desplegar `apps/api` (**Root Directory = apps/api**) con variables:
   - `DATABASE_URL`
   - `SECRET_KEY` (largo, aleatorio)
   - `ENVIRONMENT=production`
   - `CORS_ORIGINS=https://app.cliente.com`
   - `COOKIE_SECURE=true`
   - `OWNER_EMAIL` / `OWNER_PASSWORD` (solo primer seed)
3. Release command: `alembic upgrade head && python -m scripts.seed`
4. Desplegar `apps/web` con `NEXT_PUBLIC_API_URL=https://api.cliente.com`
5. Verificar login owner, captura, drag de estados y métricas.
6. Configurar dominio, backups diarios de PostgreSQL y alertas de health (`/api/health`).

## Migración desde MVP Svelte (`kanban-pedidos`)

Mapa de estados sugerido:

| Antiguo | Nuevo |
|---------|-------|
| solicitudes | NUEVA |
| analisis | VALIDANDO |
| por_pedir | POR_PEDIR |
| en_camino | EN_CAMINO |
| recibido | DISPONIBLE |

Exportar `solicitudes` y `proveedores`, importar proveedores vía CSV y crear demandas con motivo `OUT_OF_STOCK` o `NOT_CARRIED` según exista producto. Registrar `import_source=legacy_kanban_pedidos` en notas/auditoría.

## Piloto

Correr en paralelo 1–2 semanas, comparar tiempos de captura y completitud de motivos. Cortar el MVP solo tras aceptación del piloto.
