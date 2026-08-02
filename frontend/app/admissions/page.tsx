import type { Metadata } from "next"
import Link from "next/link"
import {
  ArrowRight,
  CalendarClock,
  FileCheck2,
  GraduationCap,
  MessageSquareText,
} from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { getPublicPageByPath } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Admissions | AIU Portal",
  description:
    "AIU admissions and application pathways for undergraduate and postgraduate applicants.",
}

const steps = [
  {
    title: "Prepare Documents",
    summary:
      "Applicants prepare identity documents, academic transcripts, English proficiency evidence, and scholarship-related documents where relevant.",
    icon: FileCheck2,
  },
  {
    title: "Submit Application",
    summary:
      "Undergraduate and postgraduate applicants continue through local application guidance pages.",
    icon: GraduationCap,
  },
  {
    title: "Scholarship Review",
    summary:
      "Eligible applicants may be invited to scholarship interview and assessment after meeting academic and scholarship criteria.",
    icon: MessageSquareText,
  },
  {
    title: "Intake Timeline",
    summary:
      "The current official undergraduate page highlights the October 2026 intake with a deadline of 31 July 2026.",
    icon: CalendarClock,
  },
]

export default async function AdmissionsPage() {
  const managedPage = await getPublicPageByPath("/admissions")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/admissions",
          eyebrow: "Admissions",
          image: "/images/aiu/campus-welcome.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/admissions"
      hero={
        <PublicHero
          eyebrow="Admissions"
          title="A clear entry point for undergraduate and postgraduate applications."
          description="The replacement site presents admissions guidance and keeps undergraduate, postgraduate, scholarship, and contact routes inside this website."
          image="/images/aiu/campus-welcome.jpg"
          actions={[
            {
              label: "Start Application",
              href: "/apply",
            },
            {
              label: "Applicant Login",
              href: "/login?next=/apply/dashboard",
              variant: "secondary",
            },
          ]}
          stats={[
            { value: "Oct", label: "2026 intake" },
            { value: "31 Jul", label: "Application deadline" },
            { value: "UG", label: "Undergraduate pathway" },
            { value: "PG", label: "Postgraduate pathway" },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Application Flow"
          title="Guide applicants from discovery to submission readiness."
          description="Applicants can check programme, scholarship, and contact details in this website before completing the internal application pathway."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid columns={4} items={steps} />
        </div>
      </PageBand>

      <PageBand tone="muted">
        <div className="grid gap-5 md:grid-cols-2">
          <Link
            href="/apply"
            className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-950"
          >
            <p className="text-sm font-bold tracking-[0.16em] text-teal-700 uppercase dark:text-teal-300">
              Undergraduate Program
            </p>
            <h2 className="mt-3 text-2xl font-semibold text-slate-950 dark:text-white">
              October 2026 intake
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
              The official AIU admissions page lists the October 2026
              undergraduate intake as open with a 31 July 2026 deadline.
            </p>
            <span className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-teal-700 dark:text-teal-300">
              Apply now <ArrowRight className="size-4" />
            </span>
          </Link>
          <Link
            href="/apply"
            className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-950"
          >
            <p className="text-sm font-bold tracking-[0.16em] text-teal-700 uppercase dark:text-teal-300">
              Postgraduate Program
            </p>
            <h2 className="mt-3 text-2xl font-semibold text-slate-950 dark:text-white">
              Research and coursework pathways
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
              Postgraduate applicants can review entry requirements, programmes,
              and CGS guidance before submission.
            </p>
            <span className="mt-6 inline-flex items-center gap-2 text-sm font-bold text-teal-700 dark:text-teal-300">
              Apply now <ArrowRight className="size-4" />
            </span>
          </Link>
        </div>
      </PageBand>
    </PublicPage>
  )
}
