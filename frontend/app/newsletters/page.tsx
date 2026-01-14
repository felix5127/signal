import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const NewslettersPageContent = dynamicImport(
  () => import('@/components/newsletters-page-content'),
  { ssr: false }
)

export default function NewslettersPage() {
  return <NewslettersPageContent />
}
