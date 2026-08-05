import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/scholarship",
    "Scholarship",
    "Scholarship criteria, assessment, and contact information."
  )
}

export default async function ScholarshipPage() {
  const managedPage = await getPublicPageByPath("/scholarship")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/scholarship", eyebrow: "Scholarship" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/scholarship"
      eyebrow="Scholarship"
      title="Scholarship information"
      description="Scholarship criteria, timelines, assessment details, and contact channels are managed from the public CMS."
      items={[
        {
          title: "Admissions",
          summary: "Review admissions guidance before starting an application.",
          href: "/admissions",
        },
        {
          title: "Apply",
          summary: "Open the applicant workflow when ready to apply.",
          href: "/apply",
        },
      ]}
    />
  )
}
