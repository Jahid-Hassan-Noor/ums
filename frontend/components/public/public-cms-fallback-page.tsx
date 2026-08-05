import Link from "next/link"
import { ArrowRight, FileText } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"

type PublicCmsFallbackItem = {
  title: string
  summary: string
  meta?: string
  href?: string
}

export function PublicCmsFallbackPage({
  active,
  eyebrow,
  title,
  description = "This public page is ready for CMS-managed content.",
  items = [],
  emptyTitle = "Content has not been published yet.",
  emptyDescription = "Content will appear here once it is published.",
}: {
  active: string
  eyebrow: string
  title: string
  description?: string
  items?: PublicCmsFallbackItem[]
  emptyTitle?: string
  emptyDescription?: string
}) {
  return (
    <PublicPage
      active={active}
      hero={
        <PublicHero
          eyebrow={eyebrow}
          title={title}
          description={description}
        />
      }
    >
      <PageBand>
        {items.length ? (
          <>
            <SectionHeading
              eyebrow={eyebrow}
              title="Published records"
              description="These records are loaded from the portal database."
              align="center"
            />
            <div className="mt-10">
              <FeatureGrid
                columns={items.length > 3 ? 3 : 2}
                items={items.map((item) => ({
                  ...item,
                  icon: FileText,
                }))}
              />
            </div>
          </>
        ) : (
          <div className="mx-auto max-w-3xl rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center dark:border-white/15 dark:bg-white/5">
            <FileText className="mx-auto size-8 text-teal-700 dark:text-teal-300" />
            <h2 className="mt-4 text-2xl font-semibold text-slate-950 dark:text-white">
              {emptyTitle}
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-600 dark:text-slate-300">
              {emptyDescription}
            </p>
            <Link
              href="/"
              className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-teal-700 hover:text-teal-900 dark:text-teal-300 dark:hover:text-teal-100"
            >
              Back to homepage
              <ArrowRight className="size-4" />
            </Link>
          </div>
        )}
      </PageBand>
    </PublicPage>
  )
}
