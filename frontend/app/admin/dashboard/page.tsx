import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const DashboardPageContent = dynamicImport(
  () => import('@/components/admin/dashboard-page-content'),
  { ssr: false }
)

export default function AdminDashboardPage() {
  return <DashboardPageContent />
}
