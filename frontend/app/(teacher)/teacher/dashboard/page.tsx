import { Header } from "@/components/layout/header"
import { TeacherDashboard } from "@/components/role-zone/role-dashboard"

export default function TeacherDashboardPage() {
  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/teacher", title: "Teacher" },
          { href: "/teacher/dashboard", title: "Dashboard" },
        ]}
      />
      <main className="flex-1 px-4 pt-4 pb-8 sm:px-6">
        <TeacherDashboard />
      </main>
    </div>
  )
}
