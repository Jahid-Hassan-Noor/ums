import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicDepartments,
  getPublicPageByPath,
  getPublicUnits,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/directories",
    "Directories",
    "Public directories for departments, units, and institution records."
  )
}

export default async function DirectoriesPage() {
  const [managedPage, directory, units] = await Promise.all([
    getPublicPageByPath("/directories"),
    getPublicDepartments(),
    getPublicUnits(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/directories", eyebrow: "Directories" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/directories"
      eyebrow="Directories"
      title="Public directories"
      description="Directory content is loaded from active department and unit records."
      items={[
        {
          title: "Departments",
          summary: `${directory.departments.length} active department records.`,
          href: "/departments",
        },
        {
          title: "Units",
          summary: `${units.length} active unit records.`,
          href: "/units",
        },
      ]}
    />
  )
}
