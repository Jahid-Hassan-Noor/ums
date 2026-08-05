import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/student-life",
    "Student Life",
    "Student resources, facilities, services, and campus life information."
  )
}

export default async function StudentLifePage() {
  const managedPage = await getPublicPageByPath("/student-life")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/student-life", eyebrow: "Student Life" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/student-life"
      eyebrow="Student Life"
      title="Student life and resources"
      description="Student-facing public resources are managed from the public CMS."
    />
  )
}
