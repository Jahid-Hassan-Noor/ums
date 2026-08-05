import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/admissions",
    "Admissions",
    "Admissions guidance, application pathways, and applicant resources."
  )
}

export default async function AdmissionsPage() {
  const managedPage = await getPublicPageByPath("/admissions")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/admissions", eyebrow: "Admissions" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/admissions"
      eyebrow="Admissions"
      title="Admissions information"
      description="Admissions copy, deadlines, requirements, and application links are managed from the public CMS."
      items={[
        {
          title: "Start Application",
          summary: "Open the applicant workflow when admissions are enabled.",
          href: "/apply",
        },
        {
          title: "Applicant Login",
          summary: "Continue a submitted or in-progress application.",
          href: "/login?next=/apply/dashboard",
        },
      ]}
    />
  )
}
