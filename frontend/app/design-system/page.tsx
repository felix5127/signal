import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const DesignSystemPageContent = dynamicImport(
  () => import('@/components/design-system-page-content'),
  { ssr: false }
)

export default function DesignSystemPage() {
  return <DesignSystemPageContent />
}
