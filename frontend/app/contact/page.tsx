import type { Metadata } from "next"
import { Mail, MapPin, Phone } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { getPublicPageByPath, getPublicUmsSettings } from "@/lib/public-api"

export async function generateMetadata(): Promise<Metadata> {
  const settings = await getPublicUmsSettings()
  const university = settings.university
  return {
    title: `Contact | ${university.short_name || university.name}`,
    description: `Contact ${university.name}.`,
  }
}

export default async function ContactPage() {
  const [managedPage, settings] = await Promise.all([
    getPublicPageByPath("/contact"),
    getPublicUmsSettings(),
  ])
  const university = settings.university
  const contactChannels = [
    {
      title: "General enquiries",
      summary: university.email,
    },
    {
      title: "Admissions",
      summary: university.admissions_email,
    },
    {
      title: "Website",
      summary: university.website_url,
    },
  ].filter((channel) => channel.summary)

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/contact",
          eyebrow: "Contact",
          image: university.social_image_url,
        }}
      />
    )
  }

  return (
    <PublicPage
      active="/contact"
      hero={
        <PublicHero
          eyebrow="Contact"
          title={`Reach ${university.name}.`}
          description="Public contact information and official service destinations for applicants, students, staff, and visitors."
          image={university.social_image_url}
          actions={[
            {
              label: "Admissions",
              href: "/apply",
            },
            { label: "Login to UMS", href: "/login", variant: "secondary" },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Contact Details"
          title={`${university.short_name || university.name} main location and general contact channels.`}
          description={`For official enquiries, use ${university.short_name || university.name}'s published contact details and service-specific channels where available.`}
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={3}
            items={[
              {
                title: "Location",
                summary: university.address,
                icon: MapPin,
              },
              {
                title: "Phone",
                summary: university.phone,
                icon: Phone,
              },
              {
                title: "Email",
                summary: university.email,
                icon: Mail,
              },
            ]}
          />
        </div>
      </PageBand>

      <PageBand tone="muted">
        <SectionHeading
          eyebrow="Email Directory"
          title="Service-specific contact channels."
          description="The public contact page includes dedicated email addresses for general enquiries, applications, student pass matters, scholarship, and admissions."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={3}
            items={contactChannels.map((channel) => ({
              ...channel,
              icon: Mail,
            }))}
          />
        </div>
      </PageBand>
    </PublicPage>
  )
}
