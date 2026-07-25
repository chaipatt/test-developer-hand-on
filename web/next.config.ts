import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output keeps the runtime image small (server.js + minimal deps).
  output: "standalone",
};

export default nextConfig;
