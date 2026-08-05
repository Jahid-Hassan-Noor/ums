import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicPageByPath,
  getPublicSchools,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/schools",
    "Schools",
    "Public directory of schools and academic programmes."
  )
}

export default async function SchoolsPage() {
  const [managedPage, schools] = await Promise.all([
    getPublicPageByPath("/schools"),
    getPublicSchools(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/schools", eyebrow: "Schools" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/schools"
      eyebrow="Schools"
      title="Schools"
      description="School records are loaded from the portal database. Publish a CMS page to customize this public route."
      items={schools.map((school) => ({
        title: school.name,
        summary: school.description || school.about || "Published school record.",
        meta: school.code,
        href: school.slug ? `/schools/${school.slug}` : undefined,
      }))}
    />
  )
}
