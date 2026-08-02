import type { Metadata } from "next"
import { Building2 } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { getPublicDepartments, getPublicPageByPath } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Departments | AIU Portal",
  description: "AIU departments directory.",
}

export default async function DepartmentsPage() {
  const [managedPage, directory] = await Promise.all([
    getPublicPageByPath("/departments"),
    getPublicDepartments(),
  ])
  const { departments, centres } = directory

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/directories",
          eyebrow: "Departments",
          image: "/images/aiu/campus-social-business.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/directories"
      hero={
        <PublicHero
          eyebrow="Departments"
          title="AIU departments directory."
          description="A cleaner public-facing department directory based on the current AIU website structure."
          image="/images/aiu/campus-social-business.jpg"
          actions={[
            {
              label: "Units",
              href: "/units",
            },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Department List"
          title="Governance, academic administration, finance, human resource, and university offices."
          description="Departments are grouped under their current school or centre parent where available."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={3}
            items={departments.map((department) => ({
              title: department.name,
              summary:
                department.description ||
                [department.school_name, department.center_name].filter(Boolean).join(" / ") ||
                "Department record for AIU public directory and internal administration.",
              icon: Building2,
            }))}
          />
        </div>
      </PageBand>

      <PageBand tone="muted">
        <SectionHeading
          eyebrow="Centres Listed With Departments"
          title="Specialist centres are organised as centre records in the portal."
          description="The official departments directory includes several centre-type entities; the portal keeps those as centres so executives and public pages use the right parent model."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={3}
            items={centres.map((centre) => ({
              title: centre.name,
              summary: centre.description || centre.offerings?.join(", ") || "AIU centre.",
              icon: Building2,
            }))}
          />
        </div>
      </PageBand>
    </PublicPage>
  )
}
