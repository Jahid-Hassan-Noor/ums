import { API_BASE } from "@/lib/api-base"
import {
  DEFAULT_UMS_LOADER_SIZE,
  DEFAULT_UMS_LOADER_SPINNER,
  normalizeUmsLoaderSize,
  normalizeUmsLoaderSpinner,
  type UmsLoaderSpinner,
} from "@/lib/loader-settings"
import type { UmsNavItem } from "@/lib/ums-roles"

export type OptionalFeatureKey =
  | "venue_booking"
  | "canteen"
  | "library"
  | "library_laptops"
  | "library_rooms"
  | "ict_helpdesk"
  | "hostel"
  | "elections"
  | "fines"
  | "quizzes"

export type UmsPublicSettings = {
  maintenance: {
    enabled: boolean
  }
  university: {
    name: string
    short_name: string
    legal_name: string
    tagline: string
    description: string
    address: string
    phone: string
    email: string
    admissions_email: string
    website_url: string
    logo_url: string
    public_hero_image_url: string
    social_image_url: string
  }
  uiCustomization: {
    brand_name: string
    sidebar_label: string
    logo_url: string
    logo_alt_text: string
    default_avatar_url: string
    loading_spinner: UmsLoaderSpinner
    loading_spinner_size: number
    card_density: "comfortable" | "compact"
    show_scope_badge: boolean
    show_link_descriptions: boolean
    primary_text_color: string
    secondary_text_color: string
    background_color: string
    font_family: string
    font_size_base: string
    dashboard_background_image_url: string
    button_color: string
    button_text_color: string
    secondary_button_color: string
    secondary_button_text_color: string
    button_border_radius: string
    icon_color: string
    icon_size: string
    dark_primary_text_color: string
    dark_secondary_text_color: string
    dark_background_color: string
    dark_button_color: string
    dark_button_text_color: string
    dark_secondary_button_color: string
    dark_secondary_button_text_color: string
    dark_accent_color: string
    dark_icon_color: string
    sidebar_font_size: string
    sidebar_font_weight: string
    sidebar_icon_size: string
    sidebar_width: string
    sidebar_collapsed_by_default: boolean
    sticky_header: boolean
    show_breadcrumbs: boolean
    show_footer: boolean
    card_border_radius: string
    card_shadow: string
    card_background_color: string
    avatar_shape: string
    avatar_size: string
    table_stripe_color: string
    modal_overlay_opacity: number
  }
  features: Record<OptionalFeatureKey, boolean>
  library_services: {
    books_enabled: boolean
    laptops_enabled: boolean
    rooms_enabled: boolean
  }
}

export const DEFAULT_UMS_PUBLIC_SETTINGS: UmsPublicSettings = {
  maintenance: {
    enabled: false,
  },
  university: {
    name: "Your University",
    short_name: "UMS",
    legal_name: "Your University",
    tagline: "University Management System",
    description: "A configurable university profile powered by UMS.",
    address: "University address",
    phone: "+604 774 7300",
    email: "info@example.edu",
    admissions_email: "admissions@example.edu",
    website_url: "https://example.edu",
    logo_url: "/images/ums/ums-logo.svg",
    public_hero_image_url: "/images/login_image.jpg",
    social_image_url: "/images/login_image.jpg",
  },
  uiCustomization: {
    brand_name: "University Management System",
    sidebar_label: "University Management System",
    logo_url: "/images/ums/ums-logo.svg",
    logo_alt_text: "University logo",
    default_avatar_url: "/images/avatar.png",
    loading_spinner: DEFAULT_UMS_LOADER_SPINNER,
    loading_spinner_size: DEFAULT_UMS_LOADER_SIZE,
    card_density: "comfortable",
    show_scope_badge: true,
    show_link_descriptions: true,
    primary_text_color: "#09090b",
    secondary_text_color: "#71717a",
    background_color: "#ffffff",
    font_family: "Inter",
    font_size_base: "16",
    dashboard_background_image_url: "",
    button_color: "#18181b",
    button_text_color: "#fafafa",
    secondary_button_color: "#f4f4f5",
    secondary_button_text_color: "#18181b",
    button_border_radius: "0.5rem",
    icon_color: "#09090b",
    icon_size: "16px",
    dark_primary_text_color: "#fafafa",
    dark_secondary_text_color: "#a1a1aa",
    dark_background_color: "#09090b",
    dark_button_color: "#fafafa",
    dark_button_text_color: "#18181b",
    dark_secondary_button_color: "#27272a",
    dark_secondary_button_text_color: "#fafafa",
    dark_accent_color: "#fafafa",
    dark_icon_color: "#fafafa",
    sidebar_font_size: "14px",
    sidebar_font_weight: "medium",
    sidebar_icon_size: "16px",
    sidebar_width: "16rem",
    sidebar_collapsed_by_default: false,
    sticky_header: true,
    show_breadcrumbs: true,
    show_footer: true,
    card_border_radius: "0.5rem",
    card_shadow: "default",
    card_background_color: "#ffffff",
    avatar_shape: "circle",
    avatar_size: "md",
    table_stripe_color: "",
    modal_overlay_opacity: 50,
  },
  features: {
    venue_booking: true,
    canteen: true,
    library: true,
    library_laptops: true,
    library_rooms: true,
    ict_helpdesk: true,
    hostel: true,
    elections: true,
    fines: true,
    quizzes: true,
  },
  library_services: {
    books_enabled: true,
    laptops_enabled: true,
    rooms_enabled: true,
  },
}

const FEATURE_PATH_RULES: Array<{
  features: OptionalFeatureKey[]
  prefixes: string[]
}> = [
  {
    features: ["venue_booking"],
    prefixes: [
      "/admin/venues",
      "/technician/venue-bookings",
      "/student/venue-bookings",
      "/teacher/venue-bookings",
    ],
  },
  {
    features: ["canteen"],
    prefixes: ["/accountant/canteen", "/student/canteen", "/caterer"],
  },
  {
    features: ["library"],
    prefixes: ["/student/library", "/librarian"],
  },
  {
    features: ["ict_helpdesk"],
    prefixes: ["/student/ict-helpdesk", "/technician/helpdesk"],
  },
  {
    features: ["hostel"],
    prefixes: ["/admin/hostels", "/student/warden-schedule"],
  },
  {
    features: ["elections"],
    prefixes: ["/technician/elections", "/student/elections"],
  },
  {
    features: ["fines"],
    prefixes: ["/accountant/fines", "/student/fines"],
  },
  {
    features: ["quizzes"],
    prefixes: ["/student/quizzes", "/teacher/quizzes"],
  },
]

function text(value: unknown, fallback: string) {
  return typeof value === "string" && value.trim() ? value : fallback
}

function bool(value: unknown, fallback: boolean) {
  return typeof value === "boolean" ? value : fallback
}

function featureFlags(value: unknown): Record<OptionalFeatureKey, boolean> {
  const incoming =
    value && typeof value === "object"
      ? (value as Partial<Record<OptionalFeatureKey, unknown>>)
      : {}
  return Object.fromEntries(
    Object.entries(DEFAULT_UMS_PUBLIC_SETTINGS.features).map(([key, fallback]) => [
      key,
      bool(incoming[key as OptionalFeatureKey], fallback),
    ])
  ) as Record<OptionalFeatureKey, boolean>
}

function navItemEnabledForFeatures(
  item: UmsNavItem,
  features: Record<OptionalFeatureKey, boolean>
) {
  return isUmsFeaturePathEnabled(item.url, features)
}

export function normalizeUmsPublicSettings(value: unknown): UmsPublicSettings {
  const incoming =
    value && typeof value === "object"
      ? (value as Partial<UmsPublicSettings>)
      : {}
  const incomingCustomization = incoming as Partial<UmsPublicSettings> & {
    ui_customization?: Partial<UmsPublicSettings["uiCustomization"]>
    uiCustomization?: Partial<UmsPublicSettings["uiCustomization"]>
  }
  const university =
    (incoming.university ?? {}) as Partial<UmsPublicSettings["university"]>
  const uiCustomization =
    (incomingCustomization.ui_customization ?? incomingCustomization.uiCustomization ?? {}) as Partial<UmsPublicSettings["uiCustomization"]>
  const maintenance =
    (incoming.maintenance ?? {}) as Partial<UmsPublicSettings["maintenance"]>

  return {
    maintenance: {
      enabled: bool(
        maintenance.enabled,
        DEFAULT_UMS_PUBLIC_SETTINGS.maintenance.enabled
      ),
    },
    university: {
      name: text(university.name, DEFAULT_UMS_PUBLIC_SETTINGS.university.name),
      short_name: text(university.short_name, DEFAULT_UMS_PUBLIC_SETTINGS.university.short_name),
      legal_name: text(university.legal_name, DEFAULT_UMS_PUBLIC_SETTINGS.university.legal_name),
      tagline: text(university.tagline, DEFAULT_UMS_PUBLIC_SETTINGS.university.tagline),
      description: text(university.description, DEFAULT_UMS_PUBLIC_SETTINGS.university.description),
      address: text(university.address, DEFAULT_UMS_PUBLIC_SETTINGS.university.address),
      phone: text(university.phone, DEFAULT_UMS_PUBLIC_SETTINGS.university.phone),
      email: text(university.email, DEFAULT_UMS_PUBLIC_SETTINGS.university.email),
      admissions_email: text(
        university.admissions_email,
        DEFAULT_UMS_PUBLIC_SETTINGS.university.admissions_email
      ),
      website_url: text(
        university.website_url,
        DEFAULT_UMS_PUBLIC_SETTINGS.university.website_url
      ),
      logo_url: text(university.logo_url, DEFAULT_UMS_PUBLIC_SETTINGS.university.logo_url),
      public_hero_image_url: text(
        university.public_hero_image_url,
        DEFAULT_UMS_PUBLIC_SETTINGS.university.public_hero_image_url
      ),
      social_image_url: text(
        university.social_image_url,
        DEFAULT_UMS_PUBLIC_SETTINGS.university.social_image_url
      ),
    },
    uiCustomization: {
      brand_name: text(uiCustomization.brand_name, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.brand_name),
      sidebar_label: text(
        uiCustomization.sidebar_label,
        DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.sidebar_label
      ),
      logo_url: text(uiCustomization.logo_url, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.logo_url),
      logo_alt_text: text(
        uiCustomization.logo_alt_text,
        DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.logo_alt_text
      ),
      default_avatar_url: text(
        uiCustomization.default_avatar_url,
        DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.default_avatar_url
      ),
      loading_spinner: normalizeUmsLoaderSpinner(uiCustomization.loading_spinner),
      loading_spinner_size: normalizeUmsLoaderSize(uiCustomization.loading_spinner_size),
      card_density: uiCustomization.card_density === "compact" ? "compact" : "comfortable",
      show_scope_badge: bool(
        uiCustomization.show_scope_badge,
        DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.show_scope_badge
      ),
      show_link_descriptions: bool(
        uiCustomization.show_link_descriptions,
        DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.show_link_descriptions
      ),
      primary_text_color: text(uiCustomization.primary_text_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.primary_text_color),
      secondary_text_color: text(uiCustomization.secondary_text_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.secondary_text_color),
      background_color: text(uiCustomization.background_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.background_color),
      font_family: text(uiCustomization.font_family, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.font_family),
      font_size_base: text(uiCustomization.font_size_base, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.font_size_base),
      dashboard_background_image_url: text(uiCustomization.dashboard_background_image_url, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dashboard_background_image_url),
      button_color: text(uiCustomization.button_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.button_color),
      button_text_color: text(uiCustomization.button_text_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.button_text_color),
      secondary_button_color: text(uiCustomization.secondary_button_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.secondary_button_color),
      secondary_button_text_color: text(uiCustomization.secondary_button_text_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.secondary_button_text_color),
      button_border_radius: text(uiCustomization.button_border_radius, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.button_border_radius),
      icon_color: text(uiCustomization.icon_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.icon_color),
      icon_size: text(uiCustomization.icon_size, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.icon_size),
      dark_primary_text_color: text(uiCustomization.dark_primary_text_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dark_primary_text_color),
      dark_secondary_text_color: text(uiCustomization.dark_secondary_text_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dark_secondary_text_color),
      dark_background_color: text(uiCustomization.dark_background_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dark_background_color),
      dark_button_color: text(uiCustomization.dark_button_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dark_button_color),
      dark_button_text_color: text(uiCustomization.dark_button_text_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dark_button_text_color),
      dark_secondary_button_color: text(uiCustomization.dark_secondary_button_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dark_secondary_button_color),
      dark_secondary_button_text_color: text(uiCustomization.dark_secondary_button_text_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dark_secondary_button_text_color),
      dark_accent_color: text(uiCustomization.dark_accent_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dark_accent_color),
      dark_icon_color: text(uiCustomization.dark_icon_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.dark_icon_color),
      sidebar_font_size: text(uiCustomization.sidebar_font_size, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.sidebar_font_size),
      sidebar_font_weight: text(uiCustomization.sidebar_font_weight, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.sidebar_font_weight),
      sidebar_icon_size: text(uiCustomization.sidebar_icon_size, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.sidebar_icon_size),
      sidebar_width: text(uiCustomization.sidebar_width, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.sidebar_width),
      sidebar_collapsed_by_default: bool(uiCustomization.sidebar_collapsed_by_default, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.sidebar_collapsed_by_default),
      sticky_header: bool(uiCustomization.sticky_header, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.sticky_header),
      show_breadcrumbs: bool(uiCustomization.show_breadcrumbs, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.show_breadcrumbs),
      show_footer: bool(uiCustomization.show_footer, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.show_footer),
      card_border_radius: text(uiCustomization.card_border_radius, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.card_border_radius),
      card_shadow: text(uiCustomization.card_shadow, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.card_shadow),
      card_background_color: text(uiCustomization.card_background_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.card_background_color),
      avatar_shape: text(uiCustomization.avatar_shape, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.avatar_shape),
      avatar_size: text(uiCustomization.avatar_size, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.avatar_size),
      table_stripe_color: text(uiCustomization.table_stripe_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.table_stripe_color),
      modal_overlay_opacity: typeof uiCustomization.modal_overlay_opacity === "number" ? uiCustomization.modal_overlay_opacity : DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.modal_overlay_opacity,
    },
    features: featureFlags(incoming.features),
    library_services: {
      books_enabled: bool(
        (incoming as Record<string, unknown>).library_services &&
          typeof (incoming as Record<string, unknown>).library_services === "object"
            ? ((incoming as Record<string, unknown>).library_services as Record<string, unknown>).books_enabled
            : undefined,
        DEFAULT_UMS_PUBLIC_SETTINGS.library_services.books_enabled
      ),
      laptops_enabled: bool(
        (incoming as Record<string, unknown>).library_services &&
          typeof (incoming as Record<string, unknown>).library_services === "object"
            ? ((incoming as Record<string, unknown>).library_services as Record<string, unknown>).laptops_enabled
            : undefined,
        DEFAULT_UMS_PUBLIC_SETTINGS.library_services.laptops_enabled
      ),
      rooms_enabled: bool(
        (incoming as Record<string, unknown>).library_services &&
          typeof (incoming as Record<string, unknown>).library_services === "object"
            ? ((incoming as Record<string, unknown>).library_services as Record<string, unknown>).rooms_enabled
            : undefined,
        DEFAULT_UMS_PUBLIC_SETTINGS.library_services.rooms_enabled
      ),
    },
  }
}

export async function loadPublicUmsSettings(
  init?: RequestInit
): Promise<UmsPublicSettings> {
  try {
    const response = await fetch(`${API_BASE}/settings/public`, {
      cache: "no-store",
      ...init,
    })
    if (!response.ok) return DEFAULT_UMS_PUBLIC_SETTINGS
    return normalizeUmsPublicSettings(await response.json())
  } catch {
    return DEFAULT_UMS_PUBLIC_SETTINGS
  }
}

export function isUmsFeaturePathEnabled(
  pathname: string,
  features: Record<OptionalFeatureKey, boolean>
) {
  const path = pathname.replace(/\/+$/, "") || "/"
  const rule = FEATURE_PATH_RULES.find((candidate) =>
    candidate.prefixes.some(
      (prefix) => path === prefix || path.startsWith(`${prefix}/`)
    )
  )
  if (!rule) return true
  return rule.features.some((feature) => features[feature] !== false)
}

export function filterUmsNavItemsByFeatures(
  items: UmsNavItem[],
  features: Record<OptionalFeatureKey, boolean>,
  libraryServices?: { books_enabled: boolean; laptops_enabled: boolean; rooms_enabled: boolean }
): UmsNavItem[] {
  return items
    .filter((item) => navItemEnabledForFeatures(item, features))
    .map((item) => ({
      ...item,
      items: item.items?.filter((child) => {
        if (!isUmsFeaturePathEnabled(child.url, features)) return false
        if (libraryServices) {
          if (child.url.includes("/library/laptops") && !libraryServices.laptops_enabled) return false
          if (child.url.includes("/library/rooms") && !libraryServices.rooms_enabled) return false
        }
        return true
      }),
    }))
    .filter((item) => !item.items || item.items.length > 0)
}
