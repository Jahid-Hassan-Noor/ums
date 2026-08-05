import Image from "next/image"
import Link from "next/link"
import type { ComponentType, ReactNode } from "react"
import {
  ChevronDown,
  ExternalLink,
  FileText,
  Mail,
  MapPin,
  Phone,
} from "lucide-react"

import { PublicBrand } from "@/components/public/public-brand"
import { PublicHeaderActions } from "@/components/public/public-header-actions"
import {
  getPublicNavigation,
  getPublicOfficialLinks,
  getPublicUmsSettings,
  type PublicNavGroup,
} from "@/lib/public-api"
import { cn } from "@/lib/utils"

export { PublicBrand } from "@/components/public/public-brand"

export type PublicAction = {
  label: string
  href: string
  external?: boolean
  variant?: "primary" | "secondary"
}

export type PublicStat = {
  value: string
  label: string
}

export type PublicIcon = ComponentType<{ className?: string }>

export function ExternalAwareLink({
  href,
  children,
  className,
  external = false,
}: {
  href: string
  children: ReactNode
  className?: string
  external?: boolean
}) {
  if (external) {
    return (
      <a href={href} target="_blank" rel="noreferrer" className={className}>
        {children}
      </a>
    )
  }

  return (
    <Link href={href} className={className}>
      {children}
    </Link>
  )
}

function isNavGroupActive(group: PublicNavGroup, active?: string) {
  return (
    active === group.href ||
    Boolean(group.children?.some((child) => active === child.href))
  )
}

function DesktopPublicNav({
  active,
  navGroups,
}: {
  active?: string
  navGroups: PublicNavGroup[]
}) {
  const primaryGroups = navGroups.slice(0, 5)
  const moreGroups = navGroups.slice(5)
  const moreActive = moreGroups.some((group) => isNavGroupActive(group, active))

  if (!navGroups.length) return null

  return (
    <nav className="hidden items-center gap-1 rounded-xl border border-slate-200/70 bg-slate-50/80 px-2 py-1 text-sm font-medium text-slate-600 dark:border-white/10 dark:bg-white/6 dark:text-slate-300 lg:flex">
      {primaryGroups.map((group) => {
        const hasChildren = Boolean(group.children?.length)
        const isActive = isNavGroupActive(group, active)

        return (
          <div key={group.href} className="group/nav relative">
            <Link
              href={group.href}
              className={cn(
                "inline-flex h-9 items-center gap-1 rounded-lg px-3 text-sm font-semibold transition hover:bg-white hover:text-slate-950 dark:hover:bg-white/10 dark:hover:text-white",
                isActive &&
                  "bg-white text-teal-800 shadow-sm dark:bg-white/10 dark:text-teal-200"
              )}
            >
              {group.label}
              {hasChildren ? <ChevronDown className="size-3.5" /> : null}
            </Link>
            {hasChildren ? (
              <div className="invisible absolute top-full left-0 w-72 translate-y-2 rounded-xl border border-slate-200/70 bg-white/95 p-2 opacity-0 shadow-xl shadow-slate-950/10 backdrop-blur transition group-hover/nav:visible group-hover/nav:translate-y-1 group-hover/nav:opacity-100 dark:border-white/10 dark:bg-slate-950/95">
                {group.children?.map((child) => (
                  <Link
                    key={child.href}
                    href={child.href}
                    className="block rounded-lg px-3 py-2 text-sm leading-5 font-medium text-slate-600 transition hover:bg-teal-50 hover:text-teal-900 dark:text-slate-300 dark:hover:bg-teal-300/10 dark:hover:text-teal-100"
                  >
                    {child.label}
                  </Link>
                ))}
              </div>
            ) : null}
          </div>
        )
      })}
      {moreGroups.length ? (
        <div className="group/nav relative">
          <button
            type="button"
            className={cn(
              "inline-flex h-9 items-center gap-1 rounded-lg px-3 text-sm font-semibold transition hover:bg-white hover:text-slate-950 dark:hover:bg-white/10 dark:hover:text-white",
              moreActive &&
                "bg-white text-teal-800 shadow-sm dark:bg-white/10 dark:text-teal-200"
            )}
          >
            More
            <ChevronDown className="size-3.5" />
          </button>
          <div className="invisible absolute top-full right-0 w-80 translate-y-2 rounded-xl border border-slate-200/70 bg-white/95 p-2 opacity-0 shadow-xl shadow-slate-950/10 backdrop-blur transition group-hover/nav:visible group-hover/nav:translate-y-1 group-hover/nav:opacity-100 dark:border-white/10 dark:bg-slate-950/95">
            {moreGroups.map((group) => (
              <div key={group.href} className="py-1">
                <Link
                  href={group.href}
                  className="block rounded-lg px-3 py-2 text-sm font-bold text-slate-800 transition hover:bg-teal-50 hover:text-teal-900 dark:text-slate-100 dark:hover:bg-teal-300/10 dark:hover:text-teal-100"
                >
                  {group.label}
                </Link>
                {group.children?.slice(0, 4).map((child) => (
                  <Link
                    key={child.href}
                    href={child.href}
                    className="block rounded-lg px-6 py-1.5 text-sm leading-5 font-medium text-slate-500 transition hover:bg-teal-50 hover:text-teal-900 dark:text-slate-400 dark:hover:bg-teal-300/10 dark:hover:text-teal-100"
                  >
                    {child.label}
                  </Link>
                ))}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </nav>
  )
}

async function PublicTopbar({ active }: { active?: string }) {
  const navGroups = await getPublicNavigation()

  return (
    <header className="fixed top-3 left-1/2 z-50 flex w-[calc(100%-1rem)] max-w-7xl -translate-x-1/2 items-center justify-between gap-3 rounded-2xl border border-slate-200/70 bg-white/90 px-3 py-3 text-slate-950 shadow-lg shadow-slate-900/10 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/82 dark:text-white dark:shadow-black/30 sm:w-[calc(100%-2rem)] sm:px-5">
      <PublicBrand
        className="min-w-0 flex-1 lg:flex-none"
      />
      <DesktopPublicNav active={active} navGroups={navGroups} />
      <PublicHeaderActions navGroups={navGroups} />
    </header>
  )
}

export function PublicHeader({ active }: { active?: string }) {
  return <PublicTopbar active={active} />
}

export function PublicLandingHeader() {
  return <PublicTopbar active="/" />
}

export function PublicHero({
  eyebrow,
  title,
  description,
  image,
  actions = [],
  stats = [],
}: {
  eyebrow: string
  title: string
  description: string
  image?: string
  actions?: PublicAction[]
  stats?: PublicStat[]
}) {
  return (
    <section className="relative overflow-hidden bg-slate-950 text-white">
      <div className="absolute inset-0">
        {image ? (
          <>
            <Image
              src={image}
              alt=""
              fill
              priority
              sizes="100vw"
              className="object-cover"
            />
            <div className="absolute inset-0 bg-slate-950/68" />
          </>
        ) : null}
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(2,6,23,0.96),rgba(15,23,42,0.86),rgba(15,118,110,0.42))]" />
      </div>
      <div className="relative mx-auto max-w-7xl px-4 pt-28 pb-16 sm:px-6 sm:pt-32 sm:pb-24 lg:px-8">
        <div className="max-w-3xl">
          <p className="text-xs font-bold tracking-[0.2em] text-teal-200 uppercase">
            {eyebrow}
          </p>
          <h1 className="mt-4 break-words font-display text-3xl leading-tight font-semibold sm:text-5xl lg:text-6xl">
            {title}
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-white/78">
            {description}
          </p>
          {actions.length ? (
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              {actions.map((action) => (
                <ExternalAwareLink
                  key={action.label}
                  href={action.href}
                  external={action.external}
                  className={cn(
                    "inline-flex h-11 items-center justify-center gap-2 rounded-lg px-4 text-sm font-bold transition",
                    action.variant === "secondary"
                      ? "border border-white/20 bg-white/10 text-white hover:bg-white/18"
                      : "bg-teal-300 text-slate-950 hover:bg-teal-200"
                  )}
                >
                  {action.label}
                  {action.external ? <ExternalLink className="size-4" /> : null}
                </ExternalAwareLink>
              ))}
            </div>
          ) : null}
        </div>
        {stats.length ? (
          <div className="mt-12 grid gap-2 border-y border-white/14 bg-white/8 py-4 backdrop-blur sm:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="px-2 py-2 sm:px-4">
                <p className="font-display text-3xl font-semibold">
                  {stat.value}
                </p>
                <p className="mt-1 text-sm font-medium text-white/64">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  )
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  align = "left",
  inverse = false,
}: {
  eyebrow: string
  title: string
  description: string
  align?: "left" | "center"
  inverse?: boolean
}) {
  return (
    <div
      className={cn("max-w-3xl", align === "center" && "mx-auto text-center")}
    >
      <p
        className={cn(
          "text-xs font-bold tracking-[0.18em] uppercase",
          inverse ? "text-teal-200" : "text-teal-700 dark:text-teal-300"
        )}
      >
        {eyebrow}
      </p>
      <h2
        className={cn(
          "mt-3 font-display text-3xl leading-tight font-semibold sm:text-4xl",
          inverse ? "text-white" : "text-slate-950 dark:text-white"
        )}
      >
        {title}
      </h2>
      <p
        className={cn(
          "mt-4 text-base leading-7",
          inverse ? "text-white/72" : "text-slate-600 dark:text-slate-300"
        )}
      >
        {description}
      </p>
    </div>
  )
}

export function PageBand({
  children,
  tone = "white",
}: {
  children: ReactNode
  tone?: "white" | "muted" | "dark"
}) {
  return (
    <section
      className={cn(
        "px-4 py-16 sm:px-6 sm:py-20 lg:px-8",
        tone === "white" && "bg-white dark:bg-slate-950",
        tone === "muted" && "bg-slate-50 dark:bg-slate-900",
        tone === "dark" && "bg-[#0b3f43] text-white"
      )}
    >
      <div className="mx-auto max-w-7xl">{children}</div>
    </section>
  )
}

export function FeatureGrid({
  items,
  columns = 3,
}: {
  items: Array<{
    title: string
    summary: string
    icon?: PublicIcon
    meta?: string
    href?: string
    external?: boolean
  }>
  columns?: 2 | 3 | 4
}) {
  return (
    <div
      className={cn(
        "grid gap-4",
        columns === 2 && "md:grid-cols-2",
        columns === 3 && "md:grid-cols-2 lg:grid-cols-3",
        columns === 4 && "sm:grid-cols-2 lg:grid-cols-4"
      )}
    >
      {items.map((item) => {
        const Icon = item.icon
        const content = (
          <>
            <div className="flex items-start justify-between gap-4">
              <span className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-teal-100 text-teal-800 dark:bg-teal-300/12 dark:text-teal-200">
                {Icon ? (
                  <Icon className="size-5" />
                ) : (
                  <FileText className="size-5" />
                )}
              </span>
              {item.meta ? (
                <span className="rounded-lg bg-amber-100 px-2 py-1 text-xs font-bold text-amber-900 dark:bg-amber-300/15 dark:text-amber-100">
                  {item.meta}
                </span>
              ) : item.href ? (
                <ExternalLink className="size-4 text-slate-400" />
              ) : null}
            </div>
            <h3 className="mt-5 text-lg font-semibold text-slate-950 dark:text-white">
              {item.title}
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
              {item.summary}
            </p>
          </>
        )

        const className =
          "block rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-300 hover:shadow-md dark:border-white/10 dark:bg-slate-950"

        return item.href ? (
          <ExternalAwareLink
            key={item.title}
            href={item.href}
            external={item.external}
            className={className}
          >
            {content}
          </ExternalAwareLink>
        ) : (
          <div key={item.title} className={className}>
            {content}
          </div>
        )
      })}
    </div>
  )
}

export async function PublicFooter() {
  const [settings, navGroups, officialLinks] = await Promise.all([
    getPublicUmsSettings(),
    getPublicNavigation(),
    getPublicOfficialLinks(),
  ])
  const university = settings.university
  const universityLinks = navGroups.slice(0, 6)
  const quickLinks = navGroups
    .flatMap((group) => group.children ?? [])
    .slice(0, 6)

  return (
    <footer className="border-t border-slate-200 bg-slate-950 px-4 py-10 text-white sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1.2fr_0.8fr_0.8fr]">
        <div>
          <PublicBrand tone="inverse" size="lg" />
          <div className="mt-6 space-y-3 text-sm text-white/68">
            <p className="flex gap-3">
              <MapPin className="mt-0.5 size-4 shrink-0 text-teal-200" />
              <span>{university.address}</span>
            </p>
            <p className="flex gap-3">
              <Phone className="mt-0.5 size-4 shrink-0 text-teal-200" />
              <span>{university.phone}</span>
            </p>
            <p className="flex gap-3">
              <Mail className="mt-0.5 size-4 shrink-0 text-teal-200" />
              <span>{university.email}</span>
            </p>
          </div>
        </div>
        <div>
          <p className="text-sm font-bold tracking-[0.16em] text-white/80 uppercase">
            University
          </p>
          <div className="mt-4 grid gap-2">
            {universityLinks.length ? universityLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm text-white/64 hover:text-white"
              >
                {link.label}
              </Link>
            )) : (
              <span className="text-sm text-white/48">
                No public navigation links are published.
              </span>
            )}
          </div>
        </div>
        <div>
          <p className="text-sm font-bold tracking-[0.16em] text-white/80 uppercase">
            Quick Link
          </p>
          <div className="mt-4 grid gap-2">
            {quickLinks.length ? quickLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm text-white/64 hover:text-white"
              >
                {link.label}
              </Link>
            )) : (
              <span className="text-sm text-white/48">
                No secondary links are published.
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="mx-auto mt-10 flex max-w-7xl flex-col gap-3 border-t border-white/10 pt-6 text-xs text-white/48 sm:flex-row sm:items-center sm:justify-between">
        <p>Copyright {university.legal_name || university.name}.</p>
        <div className="flex flex-wrap gap-3">
          {officialLinks.slice(0, 4).map((link, i) => (
            <Link
              key={`${link.title ?? ""}-${link.href ?? ""}-${i}`}
              href={link.href ?? "/"}
              className="hover:text-white"
            >
              {link.title}
            </Link>
          ))}
        </div>
      </div>
    </footer>
  )
}

export function PublicPage({
  active,
  hero,
  children,
}: {
  active?: string
  hero: ReactNode
  children: ReactNode
}) {
  return (
    <main className="min-h-screen overflow-x-clip bg-white text-slate-950 dark:bg-slate-950 dark:text-white">
      <PublicHeader active={active} />
      {hero}
      {children}
      <PublicFooter />
    </main>
  )
}
