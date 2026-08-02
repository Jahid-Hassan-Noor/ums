import type { Metadata } from "next"
import { Network } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { getPublicPageByPath, getPublicUnits } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Units | AIU Portal",
  description: "AIU units directory.",
}

export default async function UnitsPage() {
  const [managedPage, units] = await Promise.all([
    getPublicPageByPath("/units"),
    getPublicUnits(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/directories",
          eyebrow: "Units",
          image: "/images/aiu/campus-3zeros.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/directories"
      hero={
        <PublicHero
          eyebrow="Units"
          title="Operational units for student and university services."
          description="A public directory for units such as admissions, scholarship, international student support, facilities, procurement, and examination records."
          image="/images/aiu/campus-3zeros.jpg"
          actions={[
            {
              label: "Departments",
              href: "/departments",
            },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Unit List"
          title="Service units connected to applications, scholarships, facilities, international students, and records."
          description="Units are now managed records with their parent school or centre and assigned executive staff."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={4}
            items={units.map((unit) => ({
              title: unit.name,
              summary:
                unit.assigned_executives.length > 0
                  ? `${unit.assigned_executives.length} assigned staff. ${unit.description}`
                  : unit.description ||
                    [unit.school_name, unit.center_name, unit.department_name].filter(Boolean).join(" / ") ||
                    "Operational unit supporting AIU service delivery.",
              icon: Network,
            }))}
          />
        </div>
      </PageBand>
    </PublicPage>
  )
}
