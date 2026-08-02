import type { Metadata } from "next"
import Link from "next/link"
import { CalendarDays, GraduationCap, School } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import {
  getPublicCentres,
  getPublicPageByPath,
  getPublicSchools,
} from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Academic Programmes | AIU Portal",
  description: "Academic programmes by AIU schools and centres.",
}

export default async function ProgrammesPage() {
  const [managedPage, schools, centres] = await Promise.all([
    getPublicPageByPath("/programmes"),
    getPublicSchools(),
    getPublicCentres(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/programmes",
          eyebrow: "Academic Programmes",
          image: "/images/aiu/campus-social-business.jpg",
        }}
      />
    )
  }

  const totalProgrammes = schools.reduce(
    (count, school) => count + (school.programmes?.length ?? 0),
    0
  )
  const totalOfferings = centres.reduce(
    (count, centre) => count + (centre.offerings?.length ?? 0),
    0
  )
  const totalPathways = totalProgrammes + totalOfferings

  return (
    <PublicPage
      active="/programmes"
      hero={
        <PublicHero
          eyebrow="Academic Programmes"
          title="Schools, centres, and programmes in one clear academic directory."
          description="Browse AIU's current programme structure across business, social sciences, education, computing, foundation, graduate studies, and language learning."
          image="/images/aiu/campus-social-business.jpg"
          actions={[
            { label: "View Schools", href: "/schools" },
            {
              label: "Academic Calendar",
              href: "/academic-programmes",
              variant: "secondary",
            },
          ]}
          stats={[
            { value: String(schools.length), label: "Schools" },
            { value: String(centres.length), label: "Centres" },
            {
              value: totalPathways ? String(totalPathways) : "0",
              label: "Programmes and pathways",
            },
            { value: "2025/26", label: "Academic calendar" },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Schools"
          title="Undergraduate and postgraduate programmes by school."
          description="The portal will use this same structure for programme records, course offerings, staff assignments, and student dashboards."
          align="center"
        />
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
            {schools.map((school) => (
              <section
                key={school.code}
                className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-slate-950"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="rounded-lg bg-teal-100 px-3 py-1 text-sm font-bold text-teal-900 dark:bg-teal-300/15 dark:text-teal-100">
                    {school.code}
                  </span>
                  <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">
                    {school.programmes?.length ?? 0} programmes
                  </span>
                </div>
                <h2 className="mt-4 text-xl font-semibold text-slate-950 dark:text-white">
                  {school.name}
                </h2>
                <ul className="mt-5 space-y-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {(school.programmes ?? []).map((programme) => (
                    <li key={programme} className="flex gap-2">
                      <GraduationCap className="mt-1 size-4 shrink-0 text-teal-700 dark:text-teal-300" />
                      <span>{programme}</span>
                    </li>
                  ))}
              </ul>
            </section>
          ))}
        </div>
      </PageBand>

      <PageBand tone="muted">
        <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
          <SectionHeading
            eyebrow="Centres"
            title="Foundation, graduate studies, academic excellence, and language pathways."
            description="Centres support pre-university, postgraduate, language, teaching excellence, and academic quality activities."
          />
          <FeatureGrid
            columns={2}
            items={centres.map((centre) => ({
              title: centre.name,
              summary: centre.description,
              meta: centre.code,
              href: `/centres/${centre.slug}`,
              icon: School,
            }))}
          />
        </div>
      </PageBand>

      <PageBand>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 dark:border-white/10 dark:bg-white/5">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="max-w-2xl">
              <p className="flex items-center gap-2 text-sm font-bold tracking-[0.16em] text-teal-700 uppercase dark:text-teal-300">
                <CalendarDays className="size-4" />
                Academic Calendar
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                Foundation and undergraduate calendars are linked from
                AIU&apos;s official programme page.
              </h2>
            </div>
            <Link
              href="/academic-programmes"
              className="inline-flex h-11 items-center justify-center rounded-lg bg-slate-950 px-4 text-sm font-bold text-white hover:bg-teal-800 dark:bg-teal-300 dark:text-slate-950"
            >
              View Calendar
            </Link>
          </div>
        </div>
      </PageBand>
    </PublicPage>
  )
}
