import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const ResearchPageContent = dynamicImport(
  () => import('@/components/research-page-content'),
  { ssr: false }
)

export default function ResearchPage() {
  return <ResearchPageContent />
}
