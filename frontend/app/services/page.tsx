import type { Metadata } from "next"
import { ExternalLink, Link2, MonitorCog } from "lucide-react"

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
  title: "Services | AIU Portal",
  description: "AIU official services and portal service directory.",
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
        fallback={{
          active: "/ums-overview",
          eyebrow: "Services",
          image: "/images/aiu/campus-welcome.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/ums-overview"
      hero={
        <PublicHero
          eyebrow="Services"
          title="A single service directory for public pages and portal workflows."
          description="This page keeps AIU's public services visible while clarifying which services move into authenticated role dashboards."
          image="/images/aiu/campus-welcome.jpg"
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Official AIU Systems"
          title="Public services connected inside this website."
          description="These links now resolve to local public pages rather than sending visitors to the current official website."
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

      <PageBand tone="muted">
        <FeatureGrid
          columns={3}
          items={[
            {
              title: "Authenticated Academic Services",
              summary:
                "Course registration, attendance, assignments, results, and elections should live inside the portal.",
              icon: MonitorCog,
            },
            {
              title: "Public Discovery",
              summary:
                "About, programmes, scholarship, directories, news, contact, and services remain public.",
              icon: ExternalLink,
            },
            {
              title: "Future Service Requests",
              summary:
                "The portal can later add support forms for units such as ICT, facilities, records, and student affairs.",
              icon: Link2,
            },
          ]}
        />
      </PageBand>
    </PublicPage>
  )
}
