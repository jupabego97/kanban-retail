import type { NextConfig } from "next";
import fs from "node:fs";
import path from "node:path";

/**
 * En local (monorepo) el root de tracing es la raíz del repo.
 * En Docker standalone (WORKDIR = apps/web) el root es este directorio.
 */
const monorepoRoot = path.join(__dirname, "../..");
const tracingRoot = fs.existsSync(path.join(monorepoRoot, "package.json"))
  ? monorepoRoot
  : __dirname;

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: "standalone",
  outputFileTracingRoot: tracingRoot,
};

export default nextConfig;
