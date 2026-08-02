import { Header } from "@/components/layout/header"
import { StudentDashboardPage as StudentDashboardContent } from "@/components/student/student-dashboard-page"

export default function StudentDashboardPage() {
  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/student", title: "Student" },
          { href: "/student/dashboard", title: "Dashboard" },
        ]}
      />
      <main className="flex-1 px-4 pt-4 pb-8 sm:px-6">
        <StudentDashboardContent />
      </main>
    </div>
  )
}
