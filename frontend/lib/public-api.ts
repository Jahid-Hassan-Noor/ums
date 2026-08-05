import "server-only"

import type { Metadata } from "next"
import { headers } from "next/headers"

import { API_BASE } from "@/lib/api-base"
import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  normalizeUmsPublicSettings,
  type UmsPublicSettings,
} from "@/lib/ums-settings"

export type PublicSchool = {
  id: number
  code: string
  slug: string | null
  name: string
  description: string
  about: string
  vision: string
  mission: string[]
  programmes: string[]
  image_url: string
  is_active: boolean
}

export type PublicCentre = {
  id: number
  code: string
  slug: string | null
  name: string
  description: string
  about: string
  offerings: string[]
  image_url: string
  is_active: boolean
  center_type?: string
  academic_calendar_mode?: string
  academic_center?: boolean
  academic_workflows?: boolean
  semester_workflows?: boolean
}

export type PublicDepartment = {
  id: number
  code: string
  name: string
  description: string
  is_active: boolean
  school: number | null
  center: number | null
  school_name: string
  center_name: string
}

export type PublicUnit = {
  id: number
  code: string
  name: string
  unit_type: string
  description: string
  is_active: boolean
  school: number | null
  center: number | null
  department: number | null
  school_name: string
  center_name: string
  department_name: string
  assigned_executives: Array<{
    name: string
    designation: string
  }>
}

export type PublicManagedPage = {
  id: number
  section: string
  slug: string
  route_path: string
  title: string
  summary: string
  body: string
  metadata: Record<string, unknown> | null
  status: string
  sort_order: number
  published_at: string | null
  updated_at: string
}

export type PublicNewsItem = {
  id: number
  title: string
  slug: string
  summary: string
  body: string
  image: string | null
  image_url: string
  status: string
  author: number | null
  published_at: string | null
  created_at: string
  updated_at: string
  href: string
  date: string
  category: string
}

export type PublicEventItem = {
  id: number
  title: string
  slug: string
  description: string
  starts_at: string
  ends_at: string | null
  location: string
  status: string
  published_by: number | null
  created_at: string
  updated_at: string
  href: string
  date: string
  summary: string
}

export type PublicAnnouncementItem = {
  id: number
  title: string
  body: string
  audience: string
  starts_at: string | null
  ends_at: string | null
  is_pinned: boolean
  is_published: boolean
  published_by: number | null
  created_at: string
  updated_at: string
  summary: string
}

export type PublicOfficialLinkItem = {
  id: number
  title: string
  url: string
  category: string
  audience: string
  description: string
  sort_order: number
  is_active: boolean
  updated_at: string
  href: string
  summary: string
}

export type PublicNavGroup = {
  label: string
  href: string
  children?: Array<{
    label: string
    href: string
  }>
}

type PublicSchoolsResponse = {
  schools: PublicSchool[]
}

type PublicCentresResponse = {
  centres: PublicCentre[]
}

type PublicSchoolResponse = {
  school: PublicSchool
}

type PublicCentreResponse = {
  centre: PublicCentre
}

type PublicDepartmentsResponse = {
  departments: PublicDepartment[]
  centres: PublicCentre[]
}

type PublicUnitsResponse = {
  units: PublicUnit[]
}

type PublicPageResponse = {
  page: PublicManagedPage | null
}

type PublicPagesResponse = {
  pages: PublicManagedPage[]
}

type PublicNewsResponse = PublicPageResponse & {
  news: PublicNewsItem[]
  announcements?: PublicAnnouncementItem[]
}

type PublicNewsDetailResponse = {
  news: PublicNewsItem
}

type PublicEventsResponse = PublicPageResponse & {
  events: PublicEventItem[]
}

type PublicEventDetailResponse = {
  event: PublicEventItem
}

type PublicAnnouncementsResponse = PublicPageResponse & {
  announcements: PublicAnnouncementItem[]
}

type PublicOfficialLinksResponse = PublicPageResponse & {
  official_links: PublicOfficialLinkItem[]
}

const SERVER_API_BASE =
  process.env.BACKEND_API_URL ?? process.env.DJANGO_PROXY_TARGET ?? API_BASE

function formatPublicDate(value: string | null | undefined) {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  return date.toLocaleDateString("en", {
    month: "long",
    day: "numeric",
    year: "numeric",
  })
}

function normalizeNewsItem(item: PublicNewsItem): PublicNewsItem {
  return {
    ...item,
    href: `/news/${item.slug}`,
    date: formatPublicDate(item.published_at || item.created_at),
    category: "News",
  }
}

function normalizeEventItem(item: PublicEventItem): PublicEventItem {
  return {
    ...item,
    href: `/events/${item.slug}`,
    date: formatPublicDate(item.starts_at),
    summary: item.description,
  }
}

function normalizeOfficialLink(
  item: PublicOfficialLinkItem
): PublicOfficialLinkItem {
  return {
    ...item,
    href: item.url,
    summary: item.description,
  }
}

function normalizePath(path: string) {
  if (!path.startsWith("/")) {
    return `/${path}`
  }
  return path
}

async function resolveServerBase(): Promise<string> {
  if (/^https?:\/\//i.test(SERVER_API_BASE)) {
    return SERVER_API_BASE.replace(/\/+$/, "")
  }

  const headerList = await headers()
  const host = headerList.get("x-forwarded-host") ?? headerList.get("host")
  const proto = headerList.get("x-forwarded-proto") ?? "http"

  if (!host) {
    return SERVER_API_BASE.replace(/\/+$/, "")
  }

  return `${proto}://${host}${SERVER_API_BASE.replace(/\/+$/, "")}`
}

async function readJson<T>(response: Response): Promise<T> {
  const text = await response.text()
  if (!text) return {} as T
  try {
    return JSON.parse(text) as T
  } catch {
    throw new Error("Server returned invalid JSON.")
  }
}

async function throwIfNotOk(response: Response) {
  if (response.ok) return
  const data = await readJson<{ detail?: string; message?: string }>(response)
  const message = data?.detail || data?.message || "Request failed."
  throw new Error(message)
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const base = await resolveServerBase()
  const responseInit = init?.cache
    ? init
    : {
        next: { revalidate: 300 },
        ...init,
      }
  const response = await fetch(`${base}${normalizePath(path)}`, responseInit)

  await throwIfNotOk(response)

  return readJson<T>(response)
}

async function fetchJsonOrNull<T>(path: string): Promise<T | null> {
  const base = await resolveServerBase()
  const response = await fetch(`${base}${normalizePath(path)}`, {
    next: { revalidate: 300 },
  })

  if (response.status === 404) {
    return null
  }
  await throwIfNotOk(response)

  return readJson<T>(response)
}

export async function getPublicSchools(): Promise<PublicSchool[]> {
  try {
    const data = await fetchJson<PublicSchoolsResponse>("/schools")
    return data.schools ?? []
  } catch {
    return []
  }
}

export async function getPublicSchool(
  slug: string
): Promise<PublicSchool | null> {
  try {
    const data = await fetchJsonOrNull<PublicSchoolResponse>(`/schools/${slug}`)
    return data?.school ?? null
  } catch {
    return null
  }
}

export async function getPublicCentres(): Promise<PublicCentre[]> {
  try {
    const data = await fetchJson<PublicCentresResponse>("/centres")
    return data.centres ?? []
  } catch {
    return []
  }
}

export async function getPublicCentre(
  slug: string
): Promise<PublicCentre | null> {
  try {
    const data = await fetchJsonOrNull<PublicCentreResponse>(`/centres/${slug}`)
    return data?.centre ?? null
  } catch {
    return null
  }
}

export async function getPublicDepartments(): Promise<PublicDepartmentsResponse> {
  try {
    const data = await fetchJson<PublicDepartmentsResponse>("/departments")
    return {
      departments: data.departments ?? [],
      centres: data.centres ?? [],
    }
  } catch {
    return {
      departments: [],
      centres: [],
    }
  }
}

export async function getPublicUnits(): Promise<PublicUnit[]> {
  try {
    const data = await fetchJson<PublicUnitsResponse>("/units")
    return data.units ?? []
  } catch {
    return []
  }
}

function encodePublicRoutePath(routePath: string) {
  const normalized =
    routePath === "/" ? "/" : `/${routePath.replace(/^\/+|\/+$/g, "")}`
  if (normalized === "/") return "/pages?path=/"
  return `/pages${normalized
    .split("/")
    .map((part) => (part ? encodeURIComponent(part) : ""))
    .join("/")}`
}

export async function getPublicPageByPath(
  routePath: string
): Promise<PublicManagedPage | null> {
  try {
    const data = await fetchJsonOrNull<PublicPageResponse>(
      encodePublicRoutePath(routePath)
    )
    return data?.page ?? null
  } catch {
    return null
  }
}

export async function getPublicUmsSettings(): Promise<UmsPublicSettings> {
  try {
    return normalizeUmsPublicSettings(
      await fetchJson("/settings/public", { cache: "no-store" })
    )
  } catch {
    return DEFAULT_UMS_PUBLIC_SETTINGS
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function textValue(value: unknown): string {
  return typeof value === "string" ? value.trim() : ""
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null
}

function routeTitle(settings: UmsPublicSettings, title: string) {
  const brand =
    settings.university.name ||
    settings.uiCustomization.brand_name ||
    DEFAULT_UMS_PUBLIC_SETTINGS.university.name
  return `${title} | ${brand}`
}

function pageMetadata(page: PublicManagedPage | null) {
  const metadata = page?.metadata
  return isRecord(metadata) ? metadata : {}
}

function navigationMetadata(page: PublicManagedPage) {
  const metadata = pageMetadata(page)
  return isRecord(metadata.navigation) ? metadata.navigation : {}
}

function pageNavigationShow(page: PublicManagedPage) {
  const metadata = pageMetadata(page)
  const navigation = navigationMetadata(page)
  const configured =
    booleanValue(navigation.show) ??
    booleanValue(navigation.show_in_navigation) ??
    booleanValue(metadata.show_in_navigation) ??
    booleanValue(metadata.showInNavigation)
  return configured ?? page.route_path !== "/"
}

function pageNavigationOrder(page: PublicManagedPage) {
  const navigation = navigationMetadata(page)
  return numberValue(navigation.order) ?? page.sort_order ?? 0
}

function pageNavigationLabel(page: PublicManagedPage) {
  const metadata = pageMetadata(page)
  const navigation = navigationMetadata(page)
  return (
    textValue(navigation.label) ||
    textValue(metadata.navigation_label) ||
    page.title
  )
}

function pageNavigationParent(page: PublicManagedPage) {
  const metadata = pageMetadata(page)
  const navigation = navigationMetadata(page)
  const parent =
    textValue(navigation.parent) ||
    textValue(navigation.parent_path) ||
    textValue(metadata.parent_path)
  if (!parent) return ""
  return parent.startsWith("/") ? parent : `/${parent}`
}

function pageNavigationParentLabel(page: PublicManagedPage) {
  const navigation = navigationMetadata(page)
  return textValue(navigation.parent_label) || textValue(navigation.parentLabel)
}

export async function getPublicPages(): Promise<PublicManagedPage[]> {
  try {
    const data = await fetchJson<PublicPagesResponse>("/pages/navigation")
    return data.pages ?? []
  } catch {
    return []
  }
}

export async function getPublicNavigation(): Promise<PublicNavGroup[]> {
  const pages = await getPublicPages()
  const visiblePages = pages
    .filter((page) => page.route_path && pageNavigationShow(page))
    .sort((a, b) => {
      const order = pageNavigationOrder(a) - pageNavigationOrder(b)
      if (order !== 0) return order
      return pageNavigationLabel(a).localeCompare(pageNavigationLabel(b))
    })

  const pageByPath = new Map(visiblePages.map((page) => [page.route_path, page]))
  const groups = new Map<string, PublicNavGroup>()

  for (const page of visiblePages) {
    const href = page.route_path
    const label = pageNavigationLabel(page)
    const parent = pageNavigationParent(page)

    if (parent && parent !== href) {
      const parentPage = pageByPath.get(parent)
      const parentLabel =
        pageNavigationParentLabel(page) ||
        (parentPage ? pageNavigationLabel(parentPage) : "")

      if (!groups.has(parent)) {
        groups.set(parent, {
          label: parentLabel || label,
          href: parent,
          children: [],
        })
      }
      groups.get(parent)?.children?.push({ label, href })
      continue
    }

    const existing = groups.get(href)
    groups.set(href, {
      label,
      href,
      children: existing?.children,
    })
  }

  return Array.from(groups.values())
}

export async function generatePublicPageMetadata(
  routePath: string,
  fallbackTitle: string,
  fallbackDescription = "Public information managed by the university portal."
): Promise<Metadata> {
  const [page, settings] = await Promise.all([
    getPublicPageByPath(routePath),
    getPublicUmsSettings(),
  ])
  const metadata = pageMetadata(page)
  const title =
    textValue(metadata.seo_title) ||
    textValue(metadata.title) ||
    page?.title ||
    fallbackTitle
  const description =
    textValue(metadata.seo_description) ||
    textValue(metadata.description) ||
    page?.summary ||
    fallbackDescription

  return {
    title: routeTitle(settings, title),
    description,
  }
}

export async function getPublicNews(): Promise<PublicNewsItem[]> {
  try {
    const data = await fetchJson<PublicNewsResponse>("/news")
    return (data.news ?? []).map(normalizeNewsItem)
  } catch {
    return []
  }
}

export async function getPublicNewsItem(
  slug: string
): Promise<PublicNewsItem | null> {
  try {
    const data = await fetchJsonOrNull<PublicNewsDetailResponse>(
      `/news/${slug}`
    )
    return data?.news ? normalizeNewsItem(data.news) : null
  } catch {
    return null
  }
}

export async function getPublicEvents(): Promise<PublicEventItem[]> {
  try {
    const data = await fetchJson<PublicEventsResponse>("/events")
    return (data.events ?? []).map(normalizeEventItem)
  } catch {
    return []
  }
}

export async function getPublicEvent(
  slug: string
): Promise<PublicEventItem | null> {
  try {
    const data = await fetchJsonOrNull<PublicEventDetailResponse>(
      `/events/${slug}`
    )
    return data?.event ? normalizeEventItem(data.event) : null
  } catch {
    return null
  }
}

export async function getPublicAnnouncements(): Promise<
  PublicAnnouncementItem[]
> {
  try {
    const data = await fetchJson<PublicAnnouncementsResponse>("/announcements")
    return (data.announcements ?? []).map((item) => ({
      ...item,
      summary: item.body,
    }))
  } catch {
    return []
  }
}

export async function getPublicOfficialLinks(): Promise<
  PublicOfficialLinkItem[]
> {
  try {
    const data = await fetchJson<PublicOfficialLinksResponse>("/official-links")
    return (data.official_links ?? []).map(normalizeOfficialLink)
  } catch {
    return []
  }
}
