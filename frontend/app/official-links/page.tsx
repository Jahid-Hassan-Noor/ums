import type { Metadata } from "next"
import { Link2 } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { getPublicOfficialLinks, getPublicPageByPath } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Official Links | AIU Portal",
  description: "Official AIU links and student resources.",
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
        fallback={{
          active: "/official-links",
          eyebrow: "Official Links",
          image: "/images/aiu/campus-social-business.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/official-links"
      hero={
        <PublicHero
          eyebrow="Official Links"
          title="One place for AIU resources and public services."
          description="Applications, library, Student Hub, repository, alumni, convocation, and ACE-SEDI now resolve inside this replacement website."
          image="/images/aiu/campus-social-business.jpg"
          actions={[
            {
              label: "Login",
              href: "/login",
            },
            {
              label: "Services",
              href: "/services",
              variant: "secondary",
            },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Resources"
          title="Current official links, converted to local routes."
          description="These records are ready to become managed content after the admin public-content workflow is connected."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={3}
            items={officialLinks.map((link) => ({
              title: link.title,
              summary: link.summary,
              href: link.href,
              icon: Link2,
            }))}
          />
        </div>
      </PageBand>
    </PublicPage>
  )
}
