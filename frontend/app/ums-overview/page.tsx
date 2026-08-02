import type { Metadata } from "next"
import {
  BarChart3,
  BookOpenCheck,
  ClipboardList,
  GraduationCap,
  ShieldCheck,
  Vote,
} from "lucide-react"

import {
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { umsModules } from "@/lib/ums-public-data"
import { getPublicPageByPath } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Portal Overview | AIU Portal",
  description: "Overview of the AIU role-based academic portal.",
}

export default async function UmsOverviewPage() {
  const managedPage = await getPublicPageByPath("/ums-overview")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/ums-overview",
          eyebrow: "Portal Overview",
          image: "/images/aiu/campus-social-business.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/ums-overview"
      hero={
        <PublicHero
          eyebrow="Portal Overview"
          title="A role-based academic operations portal for AIU."
          description="This public page explains what the academic portal does before users log in: course registration, teaching workflows, results, elections, statistics, and administration."
          image="/images/aiu/campus-social-business.jpg"
          actions={[
            { label: "Login", href: "/login" },
            { label: "View Services", href: "/services", variant: "secondary" },
          ]}
          stats={[
            { value: "4", label: "Role dashboards" },
            { value: "8", label: "Core modules" },
            { value: "API", label: "Backend-ready design" },
            { value: "RBAC", label: "Role access control" },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Roles"
          title="Different users need different boundaries."
          description="The portal is designed around clear role ownership so academic records, results, elections, and administration remain protected."
          align="center"
        />
        <div className="mt-6 text-sm text-slate-700 dark:text-slate-300">
          Detailed role-specific operational information is available only inside the authenticated portal. Please log in to view role dashboards and responsibilities.
        </div>
      </PageBand>

      <PageBand tone="muted">
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
          <SectionHeading
            eyebrow="Modules"
            title="The core workflow map for the first release."
            description="These modules are the practical bridge between the public AIU identity and the authenticated academic operation system."
          />
          <div className="grid gap-3 sm:grid-cols-2">
            {umsModules.map((module, index) => {
              const icons = [
                ClipboardList,
                GraduationCap,
                BarChart3,
                BookOpenCheck,
                ShieldCheck,
                Vote,
              ]
              const Icon = icons[index % icons.length]
              return (
                <div
                  key={module}
                  className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-slate-950"
                >
                  <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-teal-100 text-teal-800 dark:bg-teal-300/12 dark:text-teal-200">
                    <Icon className="size-5" />
                  </span>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                    {module}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </PageBand>
    </PublicPage>
  )
}
