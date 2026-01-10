/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  basePath: process.env.NODE_ENV === 'development' ? '' : '/',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    INTERNAL_API_URL: process.env.INTERNAL_API_URL || (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : 'http://backend:8000'),
  },
  async rewrites() {
    // 暂时禁用代理，让浏览器直接处理 CORS
    return []
  },
}

module.exports = nextConfig
