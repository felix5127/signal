/** @type {import('next').NextConfig} */

// 验证生产环境必须设置 INTERNAL_API_URL
if (process.env.NODE_ENV === 'production' && !process.env.INTERNAL_API_URL) {
  console.warn('⚠️ WARNING: INTERNAL_API_URL is not set in production. API requests will fail!')
}

const nextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    // 开发环境默认 localhost:8000，生产环境必须通过环境变量设置
    INTERNAL_API_URL: process.env.INTERNAL_API_URL || 'http://localhost:8000',
  },
  async rewrites() {
    // 暂时禁用代理，让浏览器直接处理 CORS
    return []
  },
}

module.exports = nextConfig
