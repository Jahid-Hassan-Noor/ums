import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/about",
    "About",
    "Institution profile, mission, leadership, and public information."
  )
}

export default async function AboutPage() {
  const managedPage = await getPublicPageByPath("/about")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/about", eyebrow: "About" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/about"
      eyebrow="About"
      title="About this institution"
      description="Institution profile content is managed from the public CMS."
    />
  )
}
