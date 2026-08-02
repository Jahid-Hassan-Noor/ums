import type { Metadata } from "next"
import { BookOpen, Home, Newspaper, UsersRound } from "lucide-react"

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
  title: "Student Life | AIU Portal",
  description:
    "AIU student life, facilities, library, student hub, alumni, and campus resources.",
}

export default async function StudentLifePage() {
  const managedPage = await getPublicPageByPath("/student-life")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/student-life",
          eyebrow: "Student Life",
          image: "/images/aiu/campus-welcome.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/student-life"
      hero={
        <PublicHero
          eyebrow="Student Life"
          title="Campus life and student resources in one place."
          description="The current AIU website links students to facilities, library, student news, alumni, repository, and the Student Hub. This page gives those resources a focused portal entry point."
          image="/images/aiu/campus-welcome.jpg"
          actions={[
            {
              label: "Student Hub",
              href: "/student-life/student-hub",
            },
            {
              label: "Library",
              href: "/student-life/library",
              variant: "secondary",
            },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Student Resources"
          title="Official links for current students and campus life."
          description="These pages should stay connected from the public portal while authenticated workflows live inside the role-based dashboards."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={4}
            items={[
              {
                title: "Student Hub",
                summary: "Current student services and resources.",
                href: "/student-life/student-hub",
                icon: UsersRound,
              },
              {
                title: "Library",
                summary:
                  "Library collections, e-resources, operating hours, and services.",
                href: "/student-life/library",
                icon: BookOpen,
              },
              {
                title: "Facilities",
                summary:
                  "Residential and campus life facilities from the AIU public site.",
                href: "/student-life/facilities",
                icon: Home,
              },
              {
                title: "Student News",
                summary:
                  "Latest student activities, events, workshops, and campus updates.",
                href: "/news",
                icon: Newspaper,
              },
            ]}
          />
        </div>
      </PageBand>

      <PageBand tone="muted">
        <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
          <SectionHeading
            eyebrow="Portal Connection"
            title="Public resources and academic services share one entry point."
            description="Student life pages stay public. Once students log in, the portal handles private academic records such as course registration, attendance, assignments, results, and elections."
          />
          <FeatureGrid
            columns={2}
            items={[
              {
                title: "Academic Records",
                summary:
                  "Attendance, assignments, current courses, completed courses, and published results.",
                icon: BookOpen,
              },
              {
                title: "Student Elections",
                summary:
                  "Election participation and published outcomes in the authenticated student area.",
                icon: UsersRound,
              },
            ]}
          />
        </div>
      </PageBand>
    </PublicPage>
  )
}
