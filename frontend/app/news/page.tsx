import { ManagedPublicPage } from "@/components/public/managed-public-page"
import { PublicCmsFallbackPage } from "@/components/public/public-cms-fallback-page"
import {
  generatePublicPageMetadata,
  getPublicAnnouncements,
  getPublicNews,
  getPublicPageByPath,
} from "@/lib/public-api"

export function generateMetadata() {
  return generatePublicPageMetadata(
    "/news",
    "News",
    "Published public news and announcements."
  )
}

export default async function NewsPage() {
  const [managedPage, newsItems, announcements] = await Promise.all([
    getPublicPageByPath("/news"),
    getPublicNews(),
    getPublicAnnouncements(),
  ])

  if (managedPage) {
    return (
      <ManagedPublicPage
        page={managedPage}
        fallback={{ active: "/news", eyebrow: "News" }}
      />
    )
  }

  return (
    <PublicCmsFallbackPage
      active="/news"
      eyebrow="News"
      title="News"
      description="News and public announcements are loaded from CMS records."
      items={[
        ...newsItems.map((item) => ({
          title: item.title,
          summary: item.summary,
          meta: item.date,
          href: item.href,
        })),
        ...announcements.map((item) => ({
          title: item.title,
          summary: item.summary,
        })),
      ]}
    />
  )
}
