import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicPageByPath,
  getPublicUnits,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/units",
    "Units",
    "Public directory of active units."
  )
}

export default async function UnitsPage() {
  const [managedPage, units] = await Promise.all([
    getPublicPageByPath("/units"),
    getPublicUnits(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/directories", eyebrow: "Units" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/directories"
      eyebrow="Units"
      title="Units"
      description="Unit records are loaded from the portal database."
      items={units.map((unit) => ({
        title: unit.name,
        summary:
          unit.description ||
          [unit.school_name, unit.center_name, unit.department_name]
            .filter(Boolean)
            .join(" / ") ||
          "Published unit record.",
        meta: unit.code,
      }))}
    />
  )
}
