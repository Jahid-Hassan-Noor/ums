import { Header } from "@/components/layout/header"
import { TechnicianDashboard } from "@/components/role-zone/role-dashboard"

export default function Page() {
  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/technician", title: "Technician" },
          { href: "/technician/dashboard", title: "Dashboard" },
        ]}
      />
      <main className="flex-1 px-4 pb-8 pt-4 sm:px-6">
        <TechnicianDashboard />
      </main>
    </div>
  )
}
