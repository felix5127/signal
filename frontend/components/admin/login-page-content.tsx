/**
 * [INPUT]: 环境变量 ADMIN_PASSWORD，Next.js cookies API
 * [OUTPUT]: 对外提供 Admin 登录页面
 * [POS]: admin/ 的登录入口，验证密码后设置 Cookie
 * [PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
 */

'use client'

// 强制动态渲染，禁用静态生成
export const dynamic = 'force-dynamic'

import { useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Lock, AlertCircle, Loader2 } from 'lucide-react'

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })

      const data = await res.json()

      if (data.success) {
        const redirect = searchParams?.get('redirect') || '/admin/sources'
        router.push(redirect)
      } else {
        setError(data.message || '密码错误')
      }
    } catch (e) {
      setError('登录失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[var(--ds-surface)] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 mb-4">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--ds-fg)]">
            Signal Admin
          </h1>
          <p className="text-[var(--ds-muted)] mt-2">
            请输入管理员密码
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-[var(--ds-bg)] rounded-2xl border border-[var(--ds-border)] p-8 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Password Input */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-[var(--ds-fg)] mb-2"
              >
                密码
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="输入管理员密码"
                autoFocus
                className="w-full px-4 py-3 rounded-xl border border-[var(--ds-border)] bg-[var(--ds-surface)] text-[var(--ds-fg)] placeholder:text-[var(--ds-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-center gap-2 text-red-500 text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !password}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium hover:from-indigo-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  验证中...
                </>
              ) : (
                '登录'
              )}
            </button>
          </form>

          {/* Back Link */}
          <div className="mt-6 text-center">
            <a
              href="/"
              className="text-sm text-[var(--ds-muted)] hover:text-[var(--ds-fg)] transition-colors"
            >
              返回首页
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

// 用 Suspense 包裹以支持 useSearchParams
export default function AdminLoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[var(--ds-surface)] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}
