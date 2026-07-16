import type { NextConfig } from "next";
import path from "node:path";

/** Raíz del monorepo donde npm workspaces hoistea node_modules */
const monorepoRoot = path.join(__dirname, "../..");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  turbopack: {
    root: monorepoRoot,
  },
};

export default nextConfig;
