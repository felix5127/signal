import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const SystemPageContent = dynamicImport(
  () => import('@/components/admin/system-page-content'),
  { ssr: false }
)

export default function AdminSystemPage() {
  return <SystemPageContent />
}
