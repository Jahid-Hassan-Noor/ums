import type { Metadata } from "next"
import { BadgeCheck, MessageCircle, Phone, Scale } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import {
  scholarshipContact,
  scholarshipAssessment,
  scholarshipCriteria,
  scholarshipStaff,
} from "@/lib/ums-public-data"
import { getPublicPageByPath } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Scholarship | AIU Portal",
  description:
    "AIU scholarship criteria, assessment areas, and contact information.",
}

export default async function ScholarshipPage() {
  const managedPage = await getPublicPageByPath("/scholarship")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/scholarship",
          eyebrow: "Scholarship",
          image: "/images/aiu/campus-social-business.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/scholarship"
      hero={
        <PublicHero
          eyebrow="Scholarship"
          title="Scholarship guidance designed for clarity and trust."
          description="AIU's scholarship page highlights eligibility criteria, interview assessment areas, and direct scholarship unit contact information."
          image="/images/aiu/campus-social-business.jpg"
          actions={[
            {
              label: "Apply Now",
              href: "/apply",
            },
            {
              label: "Admissions",
              href: "/admissions",
              variant: "secondary",
            },
          ]}
          stats={[
            { value: "40%", label: "Socio economic status" },
            { value: "25%", label: "Communication skills" },
            { value: "20%", label: "Personality and attitude" },
            { value: "15%", label: "Personal statement defence" },
          ]}
        />
      }
    >
      <PageBand>
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <SectionHeading
            eyebrow="Criteria"
            title="Eligibility information visitors can scan quickly."
            description="This page brings the official scholarship criteria, assessment weighting, and contact information into the replacement website."
          />
          <FeatureGrid
            columns={2}
            items={scholarshipCriteria.map((criterion, index) => ({
              title: `Requirement ${index + 1}`,
              summary: criterion,
              icon: BadgeCheck,
            }))}
          />
        </div>
      </PageBand>

      <PageBand tone="muted">
        <SectionHeading
          eyebrow="Assessment"
          title="Scholarship interview assessment areas."
          description="The official AIU scholarship page lists these four weighted areas for applicants called to interview."
          align="center"
        />
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {scholarshipAssessment.map((item) => (
            <div
              key={item.label}
              className="rounded-lg border border-slate-200 bg-white p-5 text-center shadow-sm dark:border-white/10 dark:bg-slate-950"
            >
              <p className="font-display text-4xl font-semibold text-teal-700 dark:text-teal-300">
                {item.value}
              </p>
              <p className="mt-3 text-sm font-semibold text-slate-700 dark:text-slate-200">
                {item.label}
              </p>
            </div>
          ))}
        </div>
      </PageBand>

      <PageBand>
        <FeatureGrid
          columns={3}
          items={[
            {
              title: "Scholarship Unit",
              summary: `Phone: ${scholarshipContact.phone}. Email: ${scholarshipContact.email}.`,
              icon: Phone,
            },
            {
              title: "WhatsApp",
              summary: scholarshipContact.whatsapp,
              icon: MessageCircle,
            },
            {
              title: "Integrity Notice",
              summary:
                "AIU states that fraudulent or plagiarised scholarship applications may be rejected or terminated.",
              icon: Scale,
            },
          ]}
        />
      </PageBand>

      <PageBand tone="muted">
        <SectionHeading
          eyebrow="Members of Staff"
          title="Scholarship Unit staff listed for public contact."
          description="These names are included from the current public scholarship page so the replacement page carries the same service detail."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={4}
            items={scholarshipStaff.map((name) => ({
              title: name,
              summary: "Executive, Scholarship Unit",
              icon: BadgeCheck,
            }))}
          />
        </div>
      </PageBand>
    </PublicPage>
  )
}
