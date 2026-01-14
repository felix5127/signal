import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const SourcesPageContent = dynamicImport(
  () => import('@/components/admin/sources-page-content'),
  { ssr: false }
)

export default function AdminSourcesPage() {
  return <SourcesPageContent />
}
