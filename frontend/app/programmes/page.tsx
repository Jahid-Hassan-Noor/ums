import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicCentres,
  getPublicPageByPath,
  getPublicSchools,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/programmes",
    "Academic Programmes",
    "Public directory of programmes and academic pathways."
  )
}

export default async function ProgrammesPage() {
  const [managedPage, schools, centres] = await Promise.all([
    getPublicPageByPath("/programmes"),
    getPublicSchools(),
    getPublicCentres(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/programmes",
          eyebrow: "Academic Programmes",
        }}
      />
    )
  }

  const programmeItems = [
    ...schools.flatMap((school) =>
      (school.programmes ?? []).map((programme) => ({
        title: programme,
        summary: school.name,
        meta: school.code,
        href: school.slug ? `/schools/${school.slug}` : undefined,
      }))
    ),
    ...centres.flatMap((centre) =>
      (centre.offerings ?? []).map((offering) => ({
        title: offering,
        summary: centre.name,
        meta: centre.code,
        href: centre.slug ? `/centres/${centre.slug}` : undefined,
      }))
    ),
  ]

  return (
    <PublicCmsFallbackPage
      active="/programmes"
      eyebrow="Academic Programmes"
      title="Academic programmes"
      description="Programme information is loaded from active school and centre records."
      items={programmeItems}
    />
  )
}
