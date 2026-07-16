/**
 * Descarga OpenAPI de la API local y genera tipos TypeScript.
 * Uso: node scripts/generate-openapi.mjs
 */
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const url = process.env.OPENAPI_URL ?? "http://localhost:8000/openapi.json";
const outJson = join(root, "packages/api-client/openapi.json");

mkdirSync(dirname(outJson), { recursive: true });

const res = await fetch(url);
if (!res.ok) {
  console.error(`No se pudo obtener OpenAPI desde ${url}: ${res.status}`);
  process.exit(1);
}
const json = await res.json();
writeFileSync(outJson, JSON.stringify(json, null, 2));
console.log(`OpenAPI guardado en ${outJson}`);
console.log("Genere tipos con: npx openapi-typescript packages/api-client/openapi.json -o packages/api-client/schema.d.ts");
