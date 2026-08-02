import { cookies } from "next/headers"

import { Header } from "@/components/layout/header"
import { ExecutiveDashboard } from "@/components/role-zone/role-dashboard"

export default async function ExecutiveDashboardPage() {
  const cookieStore = await cookies()
  const executiveHasAcademicWorkflows =
    cookieStore.get("ums_academic_workflows")?.value !== "0"

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/executive", title: "Executive" },
          { href: "/executive/dashboard", title: "Dashboard" },
        ]}
      />
      <main className="flex-1 px-4 pt-4 pb-8 sm:px-6">
        <ExecutiveDashboard
          executiveHasAcademicWorkflows={executiveHasAcademicWorkflows}
        />
      </main>
    </div>
  )
}
