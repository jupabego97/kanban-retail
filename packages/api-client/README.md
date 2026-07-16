# api-client

Cliente TypeScript generado desde el OpenAPI de FastAPI.

## Generar

Con la API corriendo en `http://localhost:8000`:

```bash
# desde apps/web o raíz
npx openapi-typescript http://localhost:8000/openapi.json -o ../../packages/api-client/schema.d.ts
```

Los tipos de dominio también viven en `apps/web/src/lib/types.ts` para uso inmediato en la UI.
