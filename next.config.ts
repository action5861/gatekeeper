import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/reward',
        destination: 'http://localhost:8000/api/payment/reward'
      },
    ];
  },
};

export default nextConfig;
