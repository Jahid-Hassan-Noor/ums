import type { Metadata } from "next"
import Image from "next/image"
import Link from "next/link"
import { ArrowRight, GraduationCap } from "lucide-react"

import {
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { getPublicPageByPath, getPublicSchools } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Schools | AIU Portal",
  description: "AIU schools and their academic programmes.",
}

const fallbackImage = "/images/aiu/campus-3zeros.jpg"

export default async function SchoolsPage() {
  const [managedPage, schools] = await Promise.all([
    getPublicPageByPath("/schools"),
    getPublicSchools(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/schools",
          eyebrow: "Schools",
          image: "/images/aiu/campus-3zeros.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/schools"
      hero={
        <PublicHero
          eyebrow="Schools"
          title="Three schools carrying AIU's core academic portfolio."
          description="Explore the schools that anchor AIU's academic delivery and connect students to undergraduate and postgraduate pathways."
          image="/images/aiu/campus-3zeros.jpg"
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Academic Schools"
          title="Programme ownership with clear academic identity."
          description="Each school page reflects the live data maintained by the admin team."
          align="center"
        />
        <div className="mt-10 grid gap-6 lg:grid-cols-3">
          {schools.map((school) => (
            <Link
              key={school.code}
              href={`/schools/${school.slug}`}
              className="group overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-950"
            >
              <div className="relative aspect-[16/10]">
                <Image
                  src={school.image_url || fallbackImage}
                  alt={school.name}
                  fill
                  sizes="(max-width: 1024px) 100vw, 33vw"
                  className="object-cover transition duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-slate-950/30" />
                <span className="absolute top-4 left-4 rounded-lg bg-white px-3 py-1 text-sm font-bold text-slate-950">
                  {school.code}
                </span>
              </div>
              <div className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <h2 className="text-xl leading-snug font-semibold text-slate-950 dark:text-white">
                    {school.name}
                  </h2>
                  <ArrowRight className="mt-1 size-4 shrink-0 text-slate-400 group-hover:translate-x-1 group-hover:text-teal-700" />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {school.description}
                </p>
                <p className="mt-5 flex items-center gap-2 text-sm font-bold text-teal-700 dark:text-teal-300">
                  <GraduationCap className="size-4" />
                  {school.programmes?.length ?? 0} programmes
                </p>
              </div>
            </Link>
          ))}
        </div>
      </PageBand>
    </PublicPage>
  )
}
