import Image from "next/image"
import Link from "next/link"
import type { ComponentType } from "react"
import {
  ArrowRight,
  BarChart3,
  CalendarCheck2,
  CheckCircle2,
  ClipboardList,
  GraduationCap,
  LibraryBig,
  Network,
  UsersRound,
  Vote,
} from "lucide-react"

import {
  ExternalAwareLink,
  PublicFooter,
  PublicLandingHeader,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { Badge } from "@/components/ui/badge"
import { intakeNotice } from "@/lib/ums-public-data"
import {
  getPublicCentres,
  getPublicEvents,
  getPublicNews,
  getPublicPageByPath,
  getPublicSchools,
} from "@/lib/public-api"

type Icon = ComponentType<{ className?: string }>

type QuickLink = {
  label: string
  href: string
  external?: boolean
}

type WorkflowStep = {
  title: string
  summary: string
  icon: Icon
}

/* role details removed from public homepage */

  const workflowSteps: WorkflowStep[] = [
    {
      title: "Semester Setup",
      summary:
        "Admins maintain schools, centres, semesters, and account access from one governed source.",
      icon: CalendarCheck2,
    },
  {
    title: "Course Operations",
    summary:
      "Executives offer courses and assign teachers while students register during admin-defined periods.",
    icon: ClipboardList,
  },
  {
    title: "Teaching Activity",
    summary:
      "Teachers manage attendance, assignments, feedback, and draft result submissions.",
    icon: UsersRound,
  },
  {
    title: "Review and Publish",
    summary:
      "Executives verify academic outcomes before students see published results.",
    icon: CheckCircle2,
  },
]

const serviceLinks: QuickLink[] = [
  { label: "Apply Now", href: "/apply" },
  { label: "Applicant Login", href: "/login?next=/apply/dashboard" },
  { label: "Student Handbook", href: "/students/student-handbook" },
  { label: "Departments", href: "/departments" },
  { label: "Units", href: "/units" },
  { label: "ACE-SEDI", href: "/ace-sedi" },
]

export default async function HomePage() {
  const [managedPage, schools, centres, newsItems, eventItems] = await Promise.all([
    getPublicPageByPath("/"),
    getPublicSchools(),
    getPublicCentres(),
    getPublicNews(),
    getPublicEvents(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/",
          eyebrow: "AIU",
          image: "/images/aiu/campus-welcome.jpg",
        }}
      />
    )
  }

  const heroStats = [
    { value: String(schools.length), label: "Schools" },
    { value: String(centres.length), label: "Centres" },
    { value: "1", label: "Academic workspace" },
  ]

  const academicUnits = schools.map((school) => {
    const programmeCount = school.programmes?.length ?? 0
    return {
      code: school.code,
      title: school.name,
      summary: school.description,
      programmes: `${programmeCount} programme${programmeCount === 1 ? "" : "s"}`,
      href: `/schools/${school.slug}`,
      image: school.image_url || "/images/aiu/campus-3zeros.jpg",
    }
  })

  const centreNames = centres.map((centre) => centre.name)

  return (
    <main className="min-h-screen overflow-x-clip bg-white text-slate-950 dark:bg-slate-950 dark:text-white">
      <section className="relative min-h-[88svh] overflow-hidden text-white sm:min-h-[86svh]">
        <Image
          src="/images/aiu/campus-welcome.jpg"
          alt="Albukhary International University campus"
          fill
          priority
          sizes="100vw"
          className="object-cover"
        />
        <div className="absolute inset-0 bg-slate-950/58" />
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(2,6,23,0.86)_0%,rgba(2,6,23,0.58)_48%,rgba(2,6,23,0.22)_100%)]" />

        <PublicLandingHeader />

        <div className="relative z-10 mx-auto flex min-h-[calc(88svh-5rem)] w-full max-w-7xl flex-col justify-center px-4 pt-28 pb-10 sm:min-h-[calc(86svh-5rem)] sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <Badge className="h-7 rounded-lg border-white/20 bg-white/12 px-3 text-white shadow-none backdrop-blur">
              Inspiring Minds
            </Badge>
            <h1 className="mt-6 break-words font-display text-4xl leading-tight font-semibold text-white sm:text-6xl lg:text-7xl">
              Albukhary International University
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-white/82 sm:text-xl">
              A private nonprofit university in Alor Setar built around social
              business, global diversity, residential learning, and the 5A core
              values.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/apply"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-teal-400 px-5 text-sm font-bold text-slate-950 shadow-xl shadow-teal-950/30 transition hover:bg-teal-300"
              >
                <GraduationCap className="size-4" />
                Apply Now
              </Link>
              <Link
                href="/programmes"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-lg border border-white/24 bg-white/10 px-5 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/18"
              >
                Academic Programmes
                <ArrowRight className="size-4" />
              </Link>
            </div>
          </div>

          <div className="mt-10 grid gap-2 border-y border-white/16 bg-slate-950/24 py-4 backdrop-blur sm:grid-cols-4">
            {heroStats.map((stat) => (
              <div key={stat.label} className="px-2 py-2 sm:px-4">
                <p className="font-display text-3xl font-semibold text-white">
                  {stat.value}
                </p>
                <p className="mt-1 text-sm font-medium text-white/68">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-slate-200 bg-white px-4 py-6 sm:px-6 lg:px-8 dark:border-white/10 dark:bg-slate-950">
        <div className="mx-auto grid max-w-7xl gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              icon: Network,
              label: "Academic structure",
              value: "Schools, centres, programmes",
            },
            {
              icon: Vote,
              label: "Student voice",
              value: "Election-ready portal flow",
            },
            {
              icon: BarChart3,
              label: "Executive oversight",
              value: "Statistics and approvals",
            },
            {
              icon: LibraryBig,
              label: "Public services",
              value: "Student Hub, Library, Admissions",
            },
          ].map((item) => {
            const IconComponent = item.icon
            return (
              <div
                key={item.label}
                className="flex items-start gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5"
              >
                <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-teal-100 text-teal-800 dark:bg-teal-300/15 dark:text-teal-200">
                  <IconComponent className="size-5" />
                </span>
                <div className="min-w-0">
                  <p className="font-semibold text-slate-950 dark:text-white">
                    {item.label}
                  </p>
                  <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {item.value}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      <section className="bg-slate-50 px-4 py-20 sm:px-6 lg:px-8 dark:bg-slate-900">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-end">
            <SectionHeading
              eyebrow="AIU Portal"
              title="Public information and academic operations, together."
              description="The new site keeps AIU's official public information visible while giving each role a focused operational entry point."
            />
            <div className="mt-6 text-sm text-slate-600 dark:text-slate-300">
              Detailed role-specific operational information is only available inside the authenticated portal. Please log in to access role dashboards and workflows.
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white px-4 py-20 sm:px-6 lg:px-8 dark:bg-slate-950">
        <div className="mx-auto max-w-7xl">
          <SectionHeading
            eyebrow="Academics"
            title="Structured around AIU's schools and centres."
            description="The portal foundation follows the current AIU academic model, so public information and internal operations can speak the same language."
            align="center"
          />

          <div className="mt-10 grid gap-5 lg:grid-cols-3">
            {academicUnits.map((unit) => (
              <Link
                key={unit.code}
                href={unit.href}
                className="group overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-900"
              >
                <div className="relative aspect-[16/10]">
                  <Image
                    src={unit.image}
                    alt={unit.title}
                    fill
                    sizes="(max-width: 1024px) 100vw, 33vw"
                    className="object-cover transition duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-slate-950/28" />
                  <span className="absolute top-4 left-4 rounded-lg bg-white px-3 py-1 text-sm font-bold text-slate-950 shadow">
                    {unit.code}
                  </span>
                </div>
                <div className="p-5">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold tracking-[0.14em] text-teal-700 uppercase dark:text-teal-300">
                      {unit.programmes}
                    </p>
                    <ArrowRight className="size-4 text-slate-400 group-hover:translate-x-1 group-hover:text-teal-700 dark:text-slate-500 dark:group-hover:text-teal-300" />
                  </div>
                  <h3 className="mt-3 text-xl leading-snug font-semibold text-slate-950 dark:text-white">
                    {unit.title}
                  </h3>
                  <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {unit.summary}
                  </p>
                </div>
              </Link>
            ))}
          </div>

          <div className="mt-8 rounded-lg border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-white/5">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div className="max-w-2xl">
                <p className="text-sm font-semibold tracking-[0.16em] text-teal-700 uppercase dark:text-teal-300">
                  Centres
                </p>
                <h3 className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                  Foundation, graduate studies, academic excellence, and
                  language development.
                </h3>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 lg:min-w-[32rem]">
                {centreNames.map((centre) => (
                  <div
                    key={centre}
                    className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 dark:border-white/10 dark:bg-slate-950 dark:text-slate-200"
                  >
                    {centre}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-[#0b3f43] px-4 py-20 text-white sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
            <SectionHeading
              eyebrow="Academic Flow"
              title="From setup to publication, every action has an owner."
              description="The homepage introduces the same governance model the application will enforce inside the authenticated portal."
              inverse
            />
            <div className="grid gap-3 sm:grid-cols-2">
              {workflowSteps.map((step, index) => {
                const IconComponent = step.icon
                return (
                  <div
                    key={step.title}
                    className="rounded-lg border border-white/14 bg-white/8 p-5"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <span className="flex size-11 items-center justify-center rounded-lg bg-teal-300 text-slate-950">
                        <IconComponent className="size-5" />
                      </span>
                      <span className="font-display text-3xl font-semibold text-white/28">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                    </div>
                    <h3 className="mt-5 text-lg font-semibold">{step.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-white/72">
                      {step.summary}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white px-4 py-20 sm:px-6 lg:px-8 dark:bg-slate-950">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1fr_1fr] lg:items-center">
          <div>
            <SectionHeading
              eyebrow="Quick Links"
              title="Fast access to AIU public services."
              description="Admissions, scholarship, library, student resources, departments, and specialist centres now resolve inside this website."
            />
            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {serviceLinks.map((link) => (
                <ExternalAwareLink
                  key={link.label}
                  href={link.href}
                  external={link.external}
                  className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-800 transition hover:border-teal-300 hover:bg-teal-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-teal-300/10"
                >
                  <span>{link.label}</span>
                  <ArrowRight className="size-4 shrink-0 text-slate-400" />
                </ExternalAwareLink>
              ))}
            </div>
          </div>

          <div className="relative min-h-[28rem] overflow-hidden rounded-lg border border-slate-200 bg-slate-100 dark:border-white/10 dark:bg-slate-900">
            <Image
              src="/images/aiu/campus-3zeros.jpg"
              alt="AIU 3 Zeros campus initiative"
              fill
              sizes="(max-width: 1024px) 100vw, 50vw"
              className="object-cover"
            />
            <div className="absolute inset-0 bg-slate-950/48" />
            <div className="absolute inset-x-0 bottom-0 p-6">
              <div className="max-w-md">
                <p className="text-sm font-semibold tracking-[0.16em] text-teal-200 uppercase">
                  AIU Identity
                </p>
                <h3 className="mt-3 font-display text-3xl font-semibold text-white">
                  Social Business, 3 Zeros, and the 5A core values.
                </h3>
                <p className="mt-3 text-sm leading-6 text-white/76">
                  The portal design keeps AIU&apos;s institutional identity
                  visible while prioritising everyday academic work.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-slate-50 px-4 py-20 sm:px-6 lg:px-8 dark:bg-slate-900">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <SectionHeading
              eyebrow="Admissions"
              title={intakeNotice.intake}
              description={`${intakeNotice.status}. The current public notice lists ${intakeNotice.deadline} as the application deadline.`}
            />
            <Link
              href="/apply"
              className="mt-8 inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 text-sm font-bold text-white transition hover:bg-teal-800 dark:bg-teal-300 dark:text-slate-950"
            >
              Apply Now
              <ArrowRight className="size-4" />
            </Link>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {newsItems.slice(0, 4).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-950"
              >
                <p className="text-xs font-bold tracking-[0.16em] text-teal-700 uppercase dark:text-teal-300">
                  {item.date}
                </p>
                <h3 className="mt-3 text-lg leading-snug font-semibold text-slate-950 dark:text-white">
                  {item.title}
                </h3>
                <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {item.summary}
                </p>
              </Link>
            ))}
            {eventItems.slice(0, 2).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-lg border border-teal-200 bg-teal-50 p-5 shadow-sm transition hover:border-teal-400 hover:bg-white dark:border-teal-300/20 dark:bg-teal-300/10 dark:hover:bg-slate-950"
              >
                <p className="text-xs font-bold tracking-[0.16em] text-teal-700 uppercase dark:text-teal-300">
                  {item.date || "Public Event"}
                </p>
                <h3 className="mt-3 text-lg leading-snug font-semibold text-slate-950 dark:text-white">
                  {item.title}
                </h3>
                <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {item.summary}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <PublicFooter />
    </main>
  )
}
