import type { Metadata } from "next"
import Image from "next/image"
import Link from "next/link"
import { ArrowRight, Sparkles } from "lucide-react"

import {
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { getPublicCentres, getPublicPageByPath } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Centres | AIU Portal",
  description:
    "AIU centres for foundation, graduate studies, language learning, and academic excellence.",
}

const fallbackImage = "/images/aiu/campus-welcome.jpg"

export default async function CentresPage() {
  const [managedPage, centres] = await Promise.all([
    getPublicPageByPath("/centres"),
    getPublicCentres(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/centres",
          eyebrow: "Centres",
          image: "/images/aiu/campus-social-business.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/centres"
      hero={
        <PublicHero
          eyebrow="Centres"
          title="Specialist centres that support learning across the university."
          description="AIU centres connect foundation pathways, graduate research, teaching excellence, language learning, and academic quality services."
          image="/images/aiu/campus-social-business.jpg"
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Academic and Support Centres"
          title="Programmes, services, and learning support beyond school boundaries."
          description="These centres reflect the live data maintained by the admin team."
          align="center"
        />
        <div className="mt-10 grid gap-5 md:grid-cols-2">
          {centres.map((centre) => (
            <Link
              key={centre.code}
              href={`/centres/${centre.slug}`}
              className="group overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-950"
            >
              <div className="relative h-56">
                <Image
                  src={centre.image_url || fallbackImage}
                  alt={centre.name}
                  fill
                  sizes="(max-width: 1024px) 100vw, 50vw"
                  className="object-cover transition duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-slate-950/34" />
                <span className="absolute top-4 left-4 rounded-lg bg-white px-3 py-1 text-sm font-bold text-slate-950">
                  {centre.code}
                </span>
              </div>
              <div className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <h2 className="text-xl leading-snug font-semibold text-slate-950 dark:text-white">
                    {centre.name}
                  </h2>
                  <ArrowRight className="mt-1 size-4 shrink-0 text-slate-400 group-hover:translate-x-1 group-hover:text-teal-700" />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {centre.description}
                </p>
                <div className="mt-5 flex flex-wrap gap-2">
                  {(centre.offerings ?? []).slice(0, 4).map((offering) => (
                    <span
                      key={offering}
                      className="inline-flex items-center gap-1 rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:bg-white/8 dark:text-slate-200"
                    >
                      <Sparkles className="size-3" />
                      {offering}
                    </span>
                  ))}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </PageBand>
    </PublicPage>
  )
}
