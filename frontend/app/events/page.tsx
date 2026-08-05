import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicEvents,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/events",
    "Events",
    "Published public events and calendar items."
  )
}

export default async function EventsPage() {
  const [managedPage, events] = await Promise.all([
    getPublicPageByPath("/events"),
    getPublicEvents(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/events", eyebrow: "Events" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/events"
      eyebrow="Events"
      title="Events"
      description="Event listings are loaded from published CMS records."
      items={events.map((event) => ({
        title: event.title,
        summary: [event.date, event.location, event.summary]
          .filter(Boolean)
          .join(". "),
        href: event.href,
      }))}
    />
  )
}
