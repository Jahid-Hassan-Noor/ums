import type { Metadata } from "next"
import { Building2, Network } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { departments, units } from "@/lib/ums-public-data"
import { getPublicPageByPath } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Directories | AIU Portal",
  description: "AIU departments and units directory.",
}

export default async function DirectoriesPage() {
  const managedPage = await getPublicPageByPath("/directories")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/directories",
          eyebrow: "Directories",
          image: "/images/aiu/campus-welcome.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/directories"
      hero={
        <PublicHero
          eyebrow="Directories"
          title="Departments and units organised for public discovery and portal setup."
          description="The current AIU site separates departments and units. This portal brings both into a cleaner directory view and prepares them as managed organizational records."
          image="/images/aiu/campus-welcome.jpg"
          actions={[
            { label: "Departments", href: "/departments" },
            { label: "Units", href: "/units", variant: "secondary" },
          ]}
          stats={[
            { value: String(departments.length), label: "Departments" },
            { value: String(units.length), label: "Units" },
            { value: "ICT", label: "Digital services" },
            { value: "CSAA", label: "Student affairs" },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Departments"
          title="University departments in the current public directory."
          description="These should later connect to staff profiles, responsibilities, contact details, and portal permissions."
        />
        <div className="mt-8">
          <FeatureGrid
            columns={3}
            items={departments.slice(0, 6).map((department) => ({
              title: department,
              summary:
                "Department record for public directory and internal portal administration.",
              icon: Building2,
            }))}
          />
        </div>
      </PageBand>

      <PageBand tone="muted">
        <SectionHeading
          eyebrow="Units"
          title="Operational units supporting students, facilities, admissions, and records."
          description="Units should become editable records in the portal so services can be linked to workflows and staff."
        />
        <div className="mt-8">
          <FeatureGrid
            columns={4}
            items={units.map((unit) => ({
              title: unit,
              summary:
                "Operational unit connected to service delivery and student support.",
              icon: Network,
            }))}
          />
        </div>
      </PageBand>
    </PublicPage>
  )
}
