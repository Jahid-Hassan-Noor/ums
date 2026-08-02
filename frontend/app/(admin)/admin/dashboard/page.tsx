import { Header } from "@/components/layout/header"
import { AdminDashboard } from "@/components/role-zone/role-dashboard"

export default function AdminDashboardPage() {
  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/dashboard", title: "Dashboard" },
        ]}
      />
      <main className="flex-1 px-4 pt-4 pb-8 sm:px-6">
        <AdminDashboard />
      </main>
    </div>
  )
}
