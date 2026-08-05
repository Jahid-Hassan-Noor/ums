import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicDepartments,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/departments",
    "Departments",
    "Public directory of active departments."
  )
}

export default async function DepartmentsPage() {
  const [managedPage, directory] = await Promise.all([
    getPublicPageByPath("/departments"),
    getPublicDepartments(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/directories", eyebrow: "Departments" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/directories"
      eyebrow="Departments"
      title="Departments"
      description="Department records are loaded from the portal database."
      items={directory.departments.map((department) => ({
        title: department.name,
        summary:
          department.description ||
          [department.school_name, department.center_name]
            .filter(Boolean)
            .join(" / ") ||
          "Published department record.",
        meta: department.code,
      }))}
    />
  )
}
