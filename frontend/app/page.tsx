import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicCentres,
  getPublicEvents,
  getPublicNews,
  getPublicOfficialLinks,
  getPublicPageByPath,
  getPublicSchools,
  getPublicUmsSettings,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/",
    "Home",
    "Public homepage managed by the university CMS."
  )
}

export default async function HomePage() {
  const [managedPage, settings, schools, centres, news, events, links] =
    await Promise.all([
      getPublicPageByPath("/"),
      getPublicUmsSettings(),
      getPublicSchools(),
      getPublicCentres(),
      getPublicNews(),
      getPublicEvents(),
      getPublicOfficialLinks(),
    ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{
          active: "/",
          eyebrow: settings.university.short_name || "Home",
          image: settings.university.public_hero_image_url,
        }}
      />
    )
  }

  const items = [
    {
      title: "Schools",
      summary: `${schools.length} active school records.`,
      href: "/schools",
    },
    {
      title: "Centres",
      summary: `${centres.length} active centre records.`,
      href: "/centres",
    },
    {
      title: "News",
      summary: news[0]?.title || `${news.length} published news records.`,
      href: "/news",
    },
    {
      title: "Events",
      summary: events[0]?.title || `${events.length} published event records.`,
      href: "/events",
    },
    {
      title: "Official Links",
      summary: `${links.length} active public link records.`,
      href: "/official-links",
    },
  ]

  return (
    <PublicCmsFallbackPage
      active="/"
      eyebrow={settings.university.short_name || "Home"}
      title={settings.university.name}
      description={
        settings.university.description ||
        "Publish the home route from the public CMS to customize this homepage."
      }
      items={items}
    />
  )
}
