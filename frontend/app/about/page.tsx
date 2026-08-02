import type { Metadata } from "next"
import {
  HandHeart,
  Landmark,
  Lightbulb,
  Sprout,
  UsersRound,
} from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { umsValues } from "@/lib/ums-public-data"
import { getPublicPageByPath } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "About AIU | AIU Portal",
  description:
    "About Albukhary International University, its mission, vision, and 5A core values.",
}

export default async function AboutPage() {
  const managedPage = await getPublicPageByPath("/about")
  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/about",
          eyebrow: "About AIU",
          image: "/images/aiu/campus-welcome.jpg",
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/about"
      hero={
        <PublicHero
          eyebrow="About AIU"
          title="A residential university built around dignity, diversity, and service."
          description="Albukhary International University is a private nonprofit university in Alor Setar with a holistic learning environment shaped by social business, global understanding, and the 5A core values."
          image="/images/aiu/campus-welcome.jpg"
          actions={[
            { label: "Explore Programmes", href: "/programmes" },
            {
              label: "Meet Leadership",
              href: "/about/pro-chancellor",
              variant: "secondary",
            },
          ]}
          stats={[
            { value: "45", label: "Acre campus" },
            { value: "60+", label: "Nationalities" },
            { value: "5A", label: "Core values" },
            { value: "3", label: "Zeros mission" },
          ]}
        />
      }
    >
      <PageBand>
        <div className="grid gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
          <SectionHeading
            eyebrow="Who We Are"
            title="A campus designed for self-discovery and global understanding."
            description="AIU combines academic learning with social engagement so students can grow through study, service, relationships, and exposure to real community challenges."
          />
          <FeatureGrid
            columns={2}
            items={[
              {
                title: "Mission",
                summary:
                  "Provide opportunity to serve humanity through social business in a redesigned learning environment.",
                icon: HandHeart,
              },
              {
                title: "Vision",
                summary:
                  "Innovate solutions that promote the convergence of ideas towards a sustainable world.",
                icon: Lightbulb,
              },
              {
                title: "Residential Learning",
                summary:
                  "A fully residential campus experience that supports learning, belonging, and cross-cultural growth.",
                icon: Landmark,
              },
              {
                title: "Social Business",
                summary:
                  "A university identity linked to sustainable impact, poverty reduction, employment, and environmental care.",
                icon: Sprout,
              },
            ]}
          />
        </div>
      </PageBand>

      <PageBand tone="muted">
        <SectionHeading
          eyebrow="5A Core Values"
          title="Values that shape the academic and student experience."
          description="The portal keeps these values visible while making day-to-day academic services easier to access."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={3}
            items={umsValues.map((value) => ({
              title: value.title,
              summary: value.summary,
              icon: UsersRound,
            }))}
          />
        </div>
      </PageBand>

      <PageBand>
        <SectionHeading
          eyebrow="Governance"
          title="Leadership pages from the official public structure."
          description="The replacement site keeps AIU's governance pages local so visitors can move through the complete public information architecture without leaving this website."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={3}
            items={[
              {
                title: "Pro-Chancellor",
                summary:
                  "Sonny Bill Williams and AIU's values-driven leadership profile.",
                href: "/about/pro-chancellor",
                icon: UsersRound,
              },
              {
                title: "Board of Governors",
                summary:
                  "Strategic oversight, university mission, constitution, rules, and policy governance.",
                href: "/about/board-of-governors",
                icon: Landmark,
              },
              {
                title: "Senate",
                summary:
                  "Academic governance through university leaders, deans, directors, and ex-officio members.",
                href: "/about/senate",
                icon: Lightbulb,
              },
              {
                title: "University Management Committee",
                summary:
                  "Senior operational leadership across registry, finance, ICT, and planning.",
                href: "/about/university-management-committee",
                icon: HandHeart,
              },
              {
                title: "Senior Management Committee",
                summary:
                  "Executive, academic, centre, quality, research, library, and service leadership.",
                href: "/about/senior-management-committee",
                icon: Sprout,
              },
            ]}
          />
        </div>
      </PageBand>
    </PublicPage>
  )
}
