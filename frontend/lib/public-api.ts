import "server-only"

import { headers } from "next/headers"

import { API_BASE } from "@/lib/api-base"
import {
  centres as fallbackCentres,
  departments as fallbackDepartmentNames,
  latestNews as fallbackNews,
  monthlyHighlights as fallbackHighlights,
  officialLinks as fallbackOfficialLinks,
  schools as fallbackSchools,
  units as fallbackUnitNames,
} from "@/lib/ums-public-data"
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
  academic_workflows?: boolean
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

function slugFromHref(href: string): string | null {
  return href.replace(/\/+$/, "").split("/").filter(Boolean).at(-1) ?? null
}

const fallbackPublicSchools: PublicSchool[] = fallbackSchools.map(
  (school, index) => ({
    id: index + 1,
    code: school.code,
    slug: slugFromHref(school.href),
    name: school.title,
    description: school.summary,
    about: school.about,
    vision: school.vision,
    mission: school.mission,
    programmes: school.programmes,
    image_url: school.image,
    is_active: true,
  })
)

const fallbackPublicCentres: PublicCentre[] = fallbackCentres.map(
  (centre, index) => ({
    id: index + 1,
    code: centre.code,
    slug: slugFromHref(centre.href),
    name: centre.title,
    description: centre.summary,
    about: centre.about,
    offerings: centre.offerings,
    image_url: centre.image,
    is_active: true,
  })
)

const fallbackPublicDepartments: PublicDepartment[] =
  fallbackDepartmentNames.map((department, index) => ({
    id: index + 1,
    code: `D${String(index + 1).padStart(2, "0")}`,
    name: department,
    description: "Department record for AIU public directory.",
    is_active: true,
    school: null,
    center: null,
    school_name: "",
    center_name: "",
  }))

const fallbackPublicUnits: PublicUnit[] = fallbackUnitNames.map(
  (unit, index) => ({
    id: index + 1,
    code: `U${String(index + 1).padStart(2, "0")}`,
    name: unit,
    unit_type: "service",
    description: "Operational unit supporting AIU service delivery.",
    is_active: true,
    school: null,
    center: null,
    department: null,
    school_name: "",
    center_name: "",
    department_name: "",
    assigned_executives: [],
  })
)

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

function fallbackPublicNews(): PublicNewsItem[] {
  return fallbackNews.map((item, index) => ({
    id: index + 1,
    title: item.title,
    slug: slugFromHref(item.href) ?? `news-${index + 1}`,
    summary: item.summary,
    body: item.summary,
    image: null,
    image_url: "",
    status: "published",
    author: null,
    published_at: null,
    created_at: item.date,
    updated_at: item.date,
    href: item.href,
    date: item.date,
    category: item.category,
  }))
}

function fallbackPublicEvents(): PublicEventItem[] {
  return fallbackHighlights.map((item, index) => ({
    id: index + 1,
    title: item.title,
    slug: slugFromHref(item.href) ?? `event-${index + 1}`,
    description: item.summary,
    starts_at: "",
    ends_at: null,
    location: "AIU",
    status: "published",
    published_by: null,
    created_at: "",
    updated_at: "",
    href: item.href,
    date: "Monthly Highlights",
    summary: item.summary,
  }))
}

function fallbackLinks(): PublicOfficialLinkItem[] {
  return fallbackOfficialLinks.map((item, index) => ({
    id: index + 1,
    title: item.title,
    url: item.href ?? "/",
    category: "Public",
    audience: "public",
    description: item.summary,
    sort_order: index,
    is_active: true,
    updated_at: "",
    href: item.href ?? "/",
    summary: item.summary,
  }))
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
    return fallbackPublicSchools
  }
}

export async function getPublicSchool(
  slug: string
): Promise<PublicSchool | null> {
  try {
    const data = await fetchJsonOrNull<PublicSchoolResponse>(`/schools/${slug}`)
    return data?.school ?? null
  } catch {
    return fallbackPublicSchools.find((school) => school.slug === slug) ?? null
  }
}

export async function getPublicCentres(): Promise<PublicCentre[]> {
  try {
    const data = await fetchJson<PublicCentresResponse>("/centres")
    return data.centres ?? []
  } catch {
    return fallbackPublicCentres
  }
}

export async function getPublicCentre(
  slug: string
): Promise<PublicCentre | null> {
  try {
    const data = await fetchJsonOrNull<PublicCentreResponse>(`/centres/${slug}`)
    return data?.centre ?? null
  } catch {
    return fallbackPublicCentres.find((centre) => centre.slug === slug) ?? null
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
      departments: fallbackPublicDepartments,
      centres: fallbackPublicCentres,
    }
  }
}

export async function getPublicUnits(): Promise<PublicUnit[]> {
  try {
    const data = await fetchJson<PublicUnitsResponse>("/units")
    return data.units ?? []
  } catch {
    return fallbackPublicUnits
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

export async function getPublicNews(): Promise<PublicNewsItem[]> {
  try {
    const data = await fetchJson<PublicNewsResponse>("/news")
    const news = (data.news ?? []).map(normalizeNewsItem)
    return news.length ? news : fallbackPublicNews()
  } catch {
    return fallbackPublicNews()
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
    return fallbackPublicNews().find((item) => item.slug === slug) ?? null
  }
}

export async function getPublicEvents(): Promise<PublicEventItem[]> {
  try {
    const data = await fetchJson<PublicEventsResponse>("/events")
    const events = (data.events ?? []).map(normalizeEventItem)
    return events.length ? events : fallbackPublicEvents()
  } catch {
    return fallbackPublicEvents()
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
    return fallbackPublicEvents().find((item) => item.slug === slug) ?? null
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
    const links = (data.official_links ?? []).map(normalizeOfficialLink)
    return links.length ? links : fallbackLinks()
  } catch {
    return fallbackLinks()
  }
}
