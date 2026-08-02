import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowRight, FileText } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import {
  getPublicDetailPage,
  publicDetailPages,
  type PublicDetailPage,
} from "@/lib/ums-public-data"
import {
  getPublicCentre,
  getPublicCentres,
  getPublicEvent,
  getPublicNewsItem,
  getPublicPageByPath,
  getPublicSchool,
  getPublicSchools,
} from "@/lib/public-api"
import { managedPageToDetailPage } from "@/lib/public-page-rendering"

type PageProps = {
  params: Promise<{ slug: string[] }>
}

export function generateStaticParams() {
  return publicDetailPages
    .filter((page) => {
      if (page.path.startsWith("/schools/")) return false
      if (page.path.startsWith("/centres/")) return false
      if (page.path.startsWith("/centers/")) return false
      if (page.path === "/academics") return false
      if (page.path === "/academic-programmes") return false
      return true
    })
    .map((page) => ({
      slug: page.path.replace(/^\/+/, "").split("/"),
    }))
}

const fallbackHeroImage = "/images/aiu/campus-welcome.jpg"

function buildSchoolDetailPage(school: Awaited<ReturnType<typeof getPublicSchool>>) {
  if (!school) return null

  const missionItems = school.mission ?? []
  const visionBody = [
    ...(school.vision ? [school.vision] : []),
    ...missionItems,
  ]

  return {
    path: `/schools/${school.slug ?? ""}`,
    active: "/schools",
    eyebrow: school.code,
    title: school.name,
    description: school.about || school.description,
    image: school.image_url || fallbackHeroImage,
    stats: [
      { value: school.code, label: "School code" },
      { value: String(school.programmes?.length ?? 0), label: "Programmes" },
      { value: "5A", label: "Core values" },
      { value: "AIU", label: "Academic school" },
    ],
    sections: [
      {
        eyebrow: "About",
        title: "Academic identity",
        body: [school.about || school.description || ""].filter(Boolean),
      },
      {
        eyebrow: "Vision",
        title: school.vision || "Vision & Mission",
        body: visionBody,
      },
      {
        eyebrow: "Programmes Offered",
        title: "Programmes under this school",
        items: (school.programmes ?? []).map((programme) => ({
          title: programme,
          summary: "Programme listed under the current AIU academic structure.",
          href: "/programmes",
        })),
      },
    ],
  } satisfies PublicDetailPage
}

function buildCentreDetailPage(
  centre: Awaited<ReturnType<typeof getPublicCentre>>
) {
  if (!centre) return null

  return {
    path: `/centres/${centre.slug ?? ""}`,
    active: "/centres",
    eyebrow: centre.code,
    title: centre.name,
    description: centre.about || centre.description,
    image: centre.image_url || fallbackHeroImage,
    stats: [
      { value: centre.code, label: "Centre code" },
      { value: String(centre.offerings?.length ?? 0), label: "Key services" },
      { value: "AIU", label: "Academic support" },
      { value: "5A", label: "Core values" },
    ],
    sections: [
      {
        eyebrow: "About",
        title: "Centre overview",
        body: [centre.about || centre.description || ""].filter(Boolean),
      },
      {
        eyebrow: "Programmes and Services",
        title: "What this centre supports",
        items: (centre.offerings ?? []).map((offering) => ({
          title: offering,
          summary:
            "Service, programme, or learning support area listed for this AIU centre.",
        })),
      },
      {
        eyebrow: "Related",
        title: "Academic directory connection",
        links: [
          { label: "All Centres", href: "/centres" },
          { label: "Academic Programmes", href: "/programmes" },
        ],
      },
    ],
  } satisfies PublicDetailPage
}

function buildNewsDetailPage(
  news: Awaited<ReturnType<typeof getPublicNewsItem>>
) {
  if (!news) return null

  return {
    path: news.href,
    active: "/news",
    eyebrow: news.category || "News",
    title: news.title,
    description: news.summary,
    image: news.image_url || "/images/aiu/campus-3zeros.jpg",
    stats: [
      { value: "AIU", label: "News" },
      { value: news.date || "Published", label: "Date" },
      { value: "Public", label: "Audience" },
      { value: "Admin", label: "Managed by" },
    ],
    sections: [
      {
        eyebrow: news.date || "Published news",
        title: "News details",
        body: [news.body || news.summary].filter(Boolean),
        links: [
          { label: "All News", href: "/news" },
          { label: "Events", href: "/events" },
        ],
      },
    ],
  } satisfies PublicDetailPage
}

function buildEventDetailPage(
  event: Awaited<ReturnType<typeof getPublicEvent>>
) {
  if (!event) return null

  return {
    path: event.href,
    active: "/events",
    eyebrow: "Event",
    title: event.title,
    description: event.summary,
    image: "/images/aiu/campus-3zeros.jpg",
    stats: [
      { value: event.date || "Scheduled", label: "Date" },
      { value: event.location || "AIU", label: "Location" },
      { value: "Public", label: "Audience" },
      { value: "Admin", label: "Managed by" },
    ],
    sections: [
      {
        eyebrow: event.date || "Event details",
        title: event.location || "Campus event",
        body: [event.description].filter(Boolean),
        links: [
          { label: "All Events", href: "/events" },
          { label: "News", href: "/news" },
        ],
      },
    ],
  } satisfies PublicDetailPage
}

function buildAcademicsPage(
  schools: Awaited<ReturnType<typeof getPublicSchools>>,
  centres: Awaited<ReturnType<typeof getPublicCentres>>
) {
  return {
    path: "/academics",
    active: "/programmes",
    eyebrow: "Academics",
    title: "Schools and academic centres across AIU.",
    description:
      "AIU's academic structure is organised around schools and specialist centres for foundation, graduate studies, academic excellence, and language learning.",
    image: "/images/aiu/campus-social-business.jpg",
    sections: [
      {
        eyebrow: "Schools",
        title: "Academic schools",
        items: schools.map((school) => ({
          title: school.name,
          summary: school.description,
          meta: school.code,
          href: `/schools/${school.slug}`,
        })),
      },
      {
        eyebrow: "Centres",
        title: "Academic and support centres",
        items: centres.map((centre) => ({
          title: centre.name,
          summary: centre.description,
          meta: centre.code,
          href: `/centres/${centre.slug}`,
        })),
      },
    ],
  } satisfies PublicDetailPage
}

function buildAcademicProgrammesPage(
  schools: Awaited<ReturnType<typeof getPublicSchools>>,
  centres: Awaited<ReturnType<typeof getPublicCentres>>
) {
  const programmeItems = [
    ...schools.flatMap((school) =>
      (school.programmes ?? []).map((programme) => ({
        title: programme,
        summary: school.name,
        meta: school.code,
        href: `/schools/${school.slug}`,
      }))
    ),
    ...centres.flatMap((centre) =>
      (centre.offerings ?? []).map((offering) => ({
        title: offering,
        summary: centre.name,
        meta: centre.code,
        href: `/centres/${centre.slug}`,
      }))
    ),
  ]

  return {
    path: "/academic-programmes",
    active: "/programmes",
    eyebrow: "Academic Programmes",
    title: "Lists of programmes and academic calendars.",
    description:
      "The programme directory follows AIU's current public structure for schools, foundation studies, and academic calendar references.",
    image: "/images/aiu/campus-welcome.jpg",
    sections: [
      {
        eyebrow: "Programmes",
        title: "Programmes by school and centre",
        items: programmeItems,
      },
      {
        eyebrow: "Academic Calendar",
        title: "Session 2025/2026 references",
        body: [
          "Foundation Studies Programme calendar: Centre for Foundation and General Studies.",
          "Undergraduate Programmes calendar: School of Business and Social Sciences, School of Education and Human Sciences, and School of Computing and Informatics.",
        ],
      },
    ],
  } satisfies PublicDetailPage
}

async function resolvePublicPage(
  slug: string[]
): Promise<PublicDetailPage | null> {
  if (slug[0] === "schools" && slug[1]) {
    const school = await getPublicSchool(slug[1])
    return buildSchoolDetailPage(school)
  }

  if ((slug[0] === "centres" || slug[0] === "centers") && slug[1]) {
    const centre = await getPublicCentre(slug[1])
    return buildCentreDetailPage(centre)
  }

  if (slug[0] === "news" && slug[1]) {
    const news = await getPublicNewsItem(slug[1])
    return buildNewsDetailPage(news)
  }

  if (slug[0] === "events" && slug[1]) {
    const event = await getPublicEvent(slug[1])
    return buildEventDetailPage(event)
  }

  if (slug[0] === "academics") {
    const [schools, centres] = await Promise.all([
      getPublicSchools(),
      getPublicCentres(),
    ])
    return buildAcademicsPage(schools, centres)
  }

  if (slug[0] === "academic-programmes") {
    const [schools, centres] = await Promise.all([
      getPublicSchools(),
      getPublicCentres(),
    ])
    return buildAcademicProgrammesPage(schools, centres)
  }

  const managedPage = await getPublicPageByPath(`/${slug.join("/")}`)
  if (managedPage) {
    return managedPageToDetailPage(managedPage)
  }

  return getPublicDetailPage(slug) ?? null
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params
  const page = await resolvePublicPage(slug)

  if (!page) {
    return {
      title: "Page Not Found | Albukhary International University",
    }
  }

  return {
    title: `${page.title} | Albukhary International University`,
    description: page.description,
  }
}

export default async function PublicDetailRoute({ params }: PageProps) {
  const { slug } = await params
  const page = await resolvePublicPage(slug)

  if (!page) {
    notFound()
  }

  return (
    <PublicPage
      active={page.active}
      hero={
        <PublicHero
          eyebrow={page.eyebrow}
          title={page.title}
          description={page.description}
          image={page.image}
          stats={page.stats}
        />
      }
    >
      {page.sections.map((section, index) => (
        <PageBand
          key={`${section.title}-${index}`}
          tone={index % 2 ? "muted" : "white"}
        >
          <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
            <SectionHeading
              eyebrow={section.eyebrow ?? page.eyebrow}
              title={section.title}
              description={
                section.body?.[0] ??
                "Public information from the AIU site structure, prepared for local content management."
              }
            />
            <div className="space-y-5">
              {section.body?.slice(1).map((paragraph) => (
                <p
                  key={paragraph}
                  className="rounded-lg border border-slate-200 bg-white p-5 text-sm leading-7 text-slate-600 shadow-sm dark:border-white/10 dark:bg-slate-950 dark:text-slate-300"
                >
                  {paragraph}
                </p>
              ))}
              {section.items?.length ? (
                <FeatureGrid
                  columns={section.items.length > 3 ? 3 : 2}
                  items={section.items.map((item) => ({
                    title: item.title,
                    summary: item.summary,
                    meta: item.meta,
                    href: item.href,
                    icon: FileText,
                  }))}
                />
              ) : null}
              {section.links?.length ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  {section.links.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-800 shadow-sm transition hover:border-teal-300 hover:bg-teal-50 dark:border-white/10 dark:bg-slate-950 dark:text-slate-100 dark:hover:bg-teal-300/10"
                    >
                      {link.label}
                      <ArrowRight className="size-4 text-slate-400" />
                    </Link>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </PageBand>
      ))}
    </PublicPage>
  )
}
