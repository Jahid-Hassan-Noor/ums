import type {
  PublicContentSection,
  PublicDetailPage,
  PublicStat,
} from "@/lib/ums-public-data"
import type { PublicManagedPage } from "@/lib/public-api"

type ManagedAction = {
  label: string
  href: string
  external?: boolean
  variant?: "primary" | "secondary"
}

type ManagedMetadata = {
  active?: string
  eyebrow?: string
  description?: string
  image?: string
  actions?: ManagedAction[]
  stats?: PublicStat[]
  sections?: PublicContentSection[]
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function textBlocks(value: string) {
  return value
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function metadataFromPage(page: PublicManagedPage): ManagedMetadata {
  return isRecord(page.metadata) ? (page.metadata as ManagedMetadata) : {}
}

export function managedPageToDetailPage(
  page: PublicManagedPage,
  fallback: Partial<PublicDetailPage> = {}
): PublicDetailPage {
  const metadata = metadataFromPage(page)
  const sections = Array.isArray(metadata.sections)
    ? metadata.sections
    : [
        {
          eyebrow: metadata.eyebrow ?? fallback.eyebrow ?? page.section,
          title: page.title,
          body: textBlocks(page.body || page.summary),
        },
      ]

  return {
    path: page.route_path || fallback.path || `/${page.slug}`,
    active: metadata.active ?? fallback.active ?? page.route_path,
    eyebrow: metadata.eyebrow ?? fallback.eyebrow ?? page.section,
    title: page.title,
    description:
      metadata.description ?? page.summary ?? fallback.description ?? page.title,
    image: metadata.image ?? fallback.image,
    stats: metadata.stats ?? fallback.stats,
    sections,
  }
}
