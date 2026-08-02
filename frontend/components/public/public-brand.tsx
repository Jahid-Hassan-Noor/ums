"use client"

import { useEffect, useState } from "react"
import Image from "next/image"
import Link from "next/link"

import { cn } from "@/lib/utils"
import {
  DEFAULT_UMS_PUBLIC_SETTINGS,
  loadPublicUmsSettings,
} from "@/lib/ums-settings"

export function PublicBrand({
  title,
  subtitle,
  href = "/",
  tone = "default",
  size = "md",
  className,
}: {
  title?: string
  subtitle?: string
  href?: string
  tone?: "default" | "inverse"
  size?: "md" | "lg" | "xl"
  className?: string
}) {
  const [settings, setSettings] = useState(DEFAULT_UMS_PUBLIC_SETTINGS)
  const isInverse = tone === "inverse"
  const isLarge = size === "lg" || size === "xl"
  const displayTitle =
    title ??
    (size === "md"
      ? settings.university.short_name
      : settings.university.name)
  const displaySubtitle = subtitle ?? settings.university.tagline
  const logoSrc = settings.uiCustomization.logo_url || settings.university.logo_url
  const logoAlt =
    settings.uiCustomization.logo_alt_text || `${settings.university.short_name} logo`

  useEffect(() => {
    let ignore = false
    void loadPublicUmsSettings().then((nextSettings) => {
      if (!ignore) setSettings(nextSettings)
    })
    return () => {
      ignore = true
    }
  }, [])

  return (
    <Link
      href={href}
      className={cn(
        "flex min-w-0 items-center gap-3 focus-visible:outline-none",
        className
      )}
    >
      <span
        className={cn(
          "relative flex shrink-0 overflow-hidden rounded-lg bg-white shadow-lg shadow-slate-900/10 ring-1 ring-slate-900/5",
          size === "xl"
            ? "h-14 w-14"
            : isLarge
              ? "h-12 w-12"
              : "h-10 w-10"
        )}
      >
        <Image
          src={logoSrc}
          alt={logoAlt}
          fill
          unoptimized
          sizes={size === "xl" ? "56px" : isLarge ? "48px" : "40px"}
          className="object-contain p-1"
        />
      </span>
      <span className="min-w-0 flex-1">
        <span
          className={cn(
            "block truncate font-display leading-tight font-semibold",
            size === "xl"
              ? "text-2xl"
              : isLarge
                ? "text-lg sm:text-xl"
                : "text-base sm:text-lg",
            isInverse ? "text-white" : "text-slate-950 dark:text-white"
          )}
        >
          {displayTitle}
        </span>
        <span
          className={cn(
            "block truncate text-xs font-semibold uppercase",
            isInverse ? "text-teal-100" : "text-teal-700 dark:text-teal-300"
          )}
        >
          {displaySubtitle}
        </span>
      </span>
    </Link>
  )
}
