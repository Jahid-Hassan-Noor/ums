import type { Metadata } from "next"
import Link from "next/link"
import { ArrowRight, CalendarDays, Newspaper } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { getPublicAnnouncements, getPublicNews } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "News and Events | AIU Portal",
  description: "Latest AIU news and events highlights.",
}

export default async function NewsPage() {
  const [newsItems, announcements] = await Promise.all([
    getPublicNews(),
    getPublicAnnouncements(),
  ])

  return (
    <PublicPage
      active="/news"
      hero={
        <PublicHero
          eyebrow="News and Events"
          title="A cleaner window into AIU activities and campus updates."
          description="The current AIU homepage highlights news, events, and monthly event highlights. This portal page structures the latest items for fast scanning."
          image="/images/aiu/campus-3zeros.jpg"
          actions={[
            {
              label: "All News",
              href: "/news",
            },
            {
              label: "Monthly Highlights",
              href: "/aiunique",
              variant: "secondary",
            },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Latest"
          title="Recent news listed on the current AIU homepage."
          description="Recent items now resolve to local detail pages, ready for backend-managed editorial content later."
          align="center"
        />
        <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {newsItems.map((item) => (
            <Link
              key={item.title}
              href={item.href}
              className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-950"
            >
              <div className="flex items-center justify-between gap-4">
                <span className="flex size-11 items-center justify-center rounded-lg bg-teal-100 text-teal-800 dark:bg-teal-300/12 dark:text-teal-200">
                  <Newspaper className="size-5" />
                </span>
                <ArrowRight className="size-4 text-slate-400 group-hover:translate-x-1 group-hover:text-teal-700" />
              </div>
              <h2 className="mt-5 text-lg leading-snug font-semibold text-slate-950 dark:text-white">
                {item.title}
              </h2>
              <p className="mt-4 flex items-center gap-2 text-sm font-semibold text-slate-500 dark:text-slate-400">
                <CalendarDays className="size-4" />
                {item.date}
              </p>
              <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                {item.summary}
              </p>
            </Link>
          ))}
        </div>
      </PageBand>

      <PageBand tone="muted">
        <FeatureGrid
          columns={2}
          items={[
            {
              title: "Events",
              summary:
                "Browse published events and campus highlights managed from the admin portal.",
              href: "/events",
              icon: CalendarDays,
            },
            ...(announcements.length
              ? announcements.slice(0, 3).map((item) => ({
                  title: item.title,
                  summary: item.summary,
                  icon: Newspaper,
                }))
              : [
                  {
                    title: "Portal Announcements",
                    summary:
                      "Published public announcements will appear here after admins add them.",
                    icon: Newspaper,
                  },
                ]),
          ]}
        />
      </PageBand>
    </PublicPage>
  )
}
