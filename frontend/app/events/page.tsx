import type { Metadata } from "next"
import { CalendarDays, Megaphone, Newspaper } from "lucide-react"

import {
  FeatureGrid,
  PageBand,
  PublicHero,
  PublicPage,
  SectionHeading,
} from "@/components/public/public-site"
import { getPublicEvents, getPublicNews } from "@/lib/public-api"

export const metadata: Metadata = {
  title: "Events | AIU Portal",
  description: "AIU events and calendar highlights placeholder.",
}

export default async function EventsPage() {
  const [events, news] = await Promise.all([getPublicEvents(), getPublicNews()])

  return (
    <PublicPage
      active="/events"
      hero={
        <PublicHero
          eyebrow="Events"
          title="AIU events, highlights, and academic notices."
          description="A public event feed for campus highlights, student activities, academic notices, and monthly AIUNIQUE updates."
          image="/images/aiu/campus-3zeros.jpg"
          actions={[
            {
              label: "News",
              href: "/news",
            },
            {
              label: "Portal Overview",
              href: "/ums-overview",
              variant: "secondary",
            },
          ]}
        />
      }
    >
      <PageBand>
        <SectionHeading
          eyebrow="Planned Module"
          title="Recent campus activity and monthly highlights."
          description="These entries now resolve inside this website and can later be powered by backend-managed public event records."
          align="center"
        />
        <div className="mt-10">
          <FeatureGrid
            columns={3}
            items={[
              ...events.slice(0, 6).map((event) => ({
                title: event.title,
                summary: `${event.date || "Published event"}${
                  event.location ? ` · ${event.location}` : ""
                }. ${event.summary}`,
                href: event.href,
                icon: CalendarDays,
              })),
              {
                title: "Recent News",
                summary:
                  news[0]?.title ?? "Recent public news and campus activity.",
                href: news[0]?.href ?? "/news",
                icon: Megaphone,
              },
              ...(events.length
                ? []
                : [
                    {
                      title: "Events",
                      summary:
                        "Published public events will appear here after admins add them.",
                      icon: Newspaper,
                    },
                  ]),
            ]}
          />
        </div>
      </PageBand>
    </PublicPage>
  )
}
