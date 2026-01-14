import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const StatsPageContent = dynamicImport(
  () => import('@/components/stats-page-content'),
  { ssr: false }
)

export default function StatsPage() {
  return <StatsPageContent />
}
