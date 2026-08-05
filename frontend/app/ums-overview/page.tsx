import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/ums-overview",
    "Portal Overview",
    "Overview of authenticated portal workflows and role-based services."
  )
}

export default async function UmsOverviewPage() {
  const managedPage = await getPublicPageByPath("/ums-overview")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/ums-overview", eyebrow: "Portal Overview" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/ums-overview"
      eyebrow="Portal Overview"
      title="Portal overview"
      description="Publish this page from the CMS to explain authenticated student, staff, and administrative workflows."
      items={[
        {
          title: "Login",
          summary: "Open the authenticated portal.",
          href: "/login",
        },
        {
          title: "Services",
          summary: "Review public service links and resources.",
          href: "/services",
        },
      ]}
    />
  )
}
