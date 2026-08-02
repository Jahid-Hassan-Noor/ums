import Link from "next/link"
import { ArrowRight, FileText } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import type { PublicDetailPage } from "@/lib/ums-public-data"
import { managedPageToDetailPage } from "@/lib/public-page-rendering"
import type { PublicManagedPage } from "@/lib/public-api"

export function ManagedPublicPage({
  page,
  fallback,
}: {
  page: PublicManagedPage
  fallback?: Partial<PublicDetailPage>
}) {
  const detail = managedPageToDetailPage(page, fallback)

  return (
    <PublicPage
      active={detail.active}
      hero={
        <PublicHero
          eyebrow={detail.eyebrow}
          title={detail.title}
          description={detail.description}
          image={detail.image}
          stats={detail.stats}
        />
      }
    >
      {detail.sections.map((section, index) => (
        <PageBand
          key={`${section.title}-${index}`}
          tone={index % 2 ? "muted" : "white"}
        >
          <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
            <SectionHeading
              eyebrow={section.eyebrow ?? detail.eyebrow}
              title={section.title}
              description={
                section.body?.[0] ??
                "Public information managed from the admin portal."
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
