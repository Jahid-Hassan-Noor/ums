import { Header } from "@/components/layout/header"
import { LibrarianDashboard } from "@/components/role-zone/role-dashboard"

export function LibrarianDashboardPage() {
  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/librarian", title: "Librarian" }, { href: "/librarian/dashboard", title: "Dashboard" }]} />
      <main className="flex-1 px-4 pb-8 pt-4 sm:px-6">
        <LibrarianDashboard />
      </main>
    </div>
  )
}
