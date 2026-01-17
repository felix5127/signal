import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const PromptsPageContent = dynamicImport(
  () => import('@/components/admin/prompts-page-content'),
  { ssr: false }
)

export default function AdminPromptsPage() {
  return <PromptsPageContent />
}
