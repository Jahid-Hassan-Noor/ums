import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicOfficialLinks,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/official-links",
    "Official Links",
    "Official public links and service destinations."
  )
}

export default async function OfficialLinksPage() {
  const [managedPage, officialLinks] = await Promise.all([
    getPublicPageByPath("/official-links"),
    getPublicOfficialLinks(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/official-links", eyebrow: "Official Links" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/official-links"
      eyebrow="Official Links"
      title="Official links"
      description="Public official links are managed from the admin CMS."
      items={officialLinks.map((link) => ({
        title: link.title,
        summary: link.summary || link.url,
        meta: link.category,
        href: link.href,
      }))}
    />
  )
}
