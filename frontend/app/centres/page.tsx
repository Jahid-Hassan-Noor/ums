import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicCentres,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/centres",
    "Centres",
    "Public directory of centres, services, and academic support units."
  )
}

export default async function CentresPage() {
  const [managedPage, centres] = await Promise.all([
    getPublicPageByPath("/centres"),
    getPublicCentres(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/centres", eyebrow: "Centres" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/centres"
      eyebrow="Centres"
      title="Centres"
      description="Centre records are loaded from the portal database. Publish a CMS page to customize this public route."
      items={centres.map((centre) => ({
        title: centre.name,
        summary: centre.description || centre.about || "Published centre record.",
        meta: centre.code,
        href: centre.slug ? `/centres/${centre.slug}` : undefined,
      }))}
    />
  )
}
