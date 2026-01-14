import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const LoginPageContent = dynamicImport(
  () => import('@/components/admin/login-page-content'),
  { ssr: false }
)

export default function AdminLoginPage() {
  return <LoginPageContent />
}
