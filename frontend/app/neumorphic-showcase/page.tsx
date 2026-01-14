import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const NeumorphicShowcasePageContent = dynamicImport(
  () => import('@/components/neumorphic-showcase-page-content'),
  { ssr: false }
)

export default function NeumorphicShowcasePage() {
  return <NeumorphicShowcasePageContent />
}
