import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicOfficialLinks,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/services",
    "Services",
    "Public service links and portal workflow information."
  )
}

export default async function ServicesPage() {
  const [managedPage, officialLinks] = await Promise.all([
    getPublicPageByPath("/services"),
    getPublicOfficialLinks(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/services", eyebrow: "Services" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/services"
      eyebrow="Services"
      title="Public services"
      description="Service directory content is managed from the public CMS."
      items={officialLinks.map((link) => ({
        title: link.title,
        summary: link.summary || link.url,
        href: link.href,
      }))}
    />
  )
}
