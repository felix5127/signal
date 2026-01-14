import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const FeedsPageContent = dynamicImport(
  () => import('@/components/feeds-page-content'),
  { ssr: false }
)

export default function FeedsPage() {
  return <FeedsPageContent />
}
