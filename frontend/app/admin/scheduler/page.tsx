import dynamicImport from 'next/dynamic'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const SchedulerPageContent = dynamicImport(
  () => import('@/components/admin/scheduler-page-content'),
  { ssr: false }
)

export default function AdminSchedulerPage() {
  return <SchedulerPageContent />
}
