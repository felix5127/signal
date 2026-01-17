import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const ReviewPageContent = dynamicImport(
  () => import('@/components/admin/review-page-content'),
  { ssr: false }
)

export default function AdminReviewPage() {
  return <ReviewPageContent />
}
