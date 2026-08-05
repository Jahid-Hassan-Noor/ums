import { API_BASE } from "@/lib/api-base"
import {
  DEFAULT_UMS_LOADER_SIZE,
  DEFAULT_UMS_LOADER_SPINNER,
  normalizeUmsLoaderSize,
  normalizeUmsLoaderSpinner,
  type UmsLoaderSpinner,
} from "@/lib/loader-settings"
import {
  ROLE_ZONES,
  UMS_ROLES,
  type UmsNavItem,
  type UmsZone,
  type UserRole,
} from "@/lib/ums-roles"

export type OptionalFeatureKey =
  | "admissions"
  | "public_website"
  | "venue_booking"
  | "canteen"
  | "library"
  | "library_laptops"
  | "library_rooms"
  | "ict_helpdesk"
  | "hostel"
  | "elections"
  | "finance"
  | "attendance"
  | "evaluations"
  | "leave"
  | "notifications"
  | "fines"
  | "quizzes"

export type UmsRoleSetting = {
  label: string
  short_label: string
  description: string
}

export type UmsRoleSettings = Record<UserRole, UmsRoleSetting>
export type UmsModuleLabels = Record<OptionalFeatureKey, string>
export type UmsModulePermissions = Record<UserRole, OptionalFeatureKey[]>
export type UmsRouteModuleRule = {
  features: OptionalFeatureKey[]
  labelFeatures?: OptionalFeatureKey[]
  exactPaths?: string[]
  prefixes?: string[]
}

export type UmsPublicSettings = {
  maintenance: {
    enabled: boolean
  }
  general: {
    portal_name: string
    support_email: string
    support_phone: string
    maintenance_banner: string
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
    login_image_url: string
    favicon_url: string
  }
  localization: {
    timezone: string
    locale: string
    currency_code: string
    currency_symbol: string
    number_format: string
    date_format: string
    time_format: string
  }
  terminology: {
    school_label: string
    center_label: string
    centre_label: string
    department_label: string
    unit_label: string
    program_label: string
    programme_label: string
    course_label: string
    semester_label: string
    academic_year_label: string
    student_id_label: string
    staff_id_label: string
    applicant_label: string
  }
  branding: {
    primary_color: string
    secondary_color: string
    accent_color: string
    logo_url: string
    public_hero_image_url: string
    login_image_url: string
    favicon_url: string
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
    accent_color: string
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
  roles: UmsRoleSettings
  module_labels: UmsModuleLabels
  module_permissions: UmsModulePermissions
  library_services: {
    books_enabled: boolean
    laptops_enabled: boolean
    rooms_enabled: boolean
  }
  policies: {
    password: {
      min_length: number
      max_length: number
      require_uppercase: boolean
      require_number: boolean
    }
    uploads: {
      default_limit_mb: number
      default_allowed_file_extensions: string
      applicant_max_upload_mb: number
      applicant_allowed_file_extensions: string
    }
    venue_booking: {
      enabled: boolean
      label: string
      requester_roles: string[]
      approval_mode: string
      reviewer_role: string
      min_duration_minutes: number
      max_duration_hours: number
      venue_categories: Array<{ value: string; label: string }>
      required_fields: Record<"event" | "personal", string[]>
      blackout_ranges: Array<{ start: string; end: string }>
    }
    dining: {
      enabled: boolean
      label: string
      monthly_allowance_amount: string
      allowance_reset_timezone: string
      allowance_reset_day: number
      allowance_reset_hour: number
      eligible_enrollment_statuses: string
      ineligible_enrollment_status_markers: string
      require_scholarship: boolean
      eligible_program_codes: string
      eligible_cohort_codes: string
      sync_balance_to_student_profile: boolean
    }
    attendance_threshold_percent: number
    leave_notice_period_days: number
    default_academic_calendar_type: string
    default_application_number_prefix: string
    default_payment_gateway_provider: string
    payment_reference_prefix: string
  }
  setup: {
    complete: boolean
    completed: number
    total: number
    items: Array<{
      key: string
      section: string
      field: string
      label: string
      complete: boolean
    }>
  }
}

const DEFAULT_ROLE_SETTINGS: UmsRoleSettings = {
  applicant: {
    label: "Applicant",
    short_label: "Applicant",
    description: "Admissions applicant workspace.",
  },
  student: {
    label: "Student",
    short_label: "Student",
    description: "Learner workspace for academic and campus services.",
  },
  teacher: {
    label: "Teacher",
    short_label: "Teacher",
    description: "Teaching workspace for courses, attendance, and assessments.",
  },
  executive: {
    label: "Executive",
    short_label: "Executive",
    description: "Academic or administrative owner workspace.",
  },
  librarian: {
    label: "Librarian",
    short_label: "Library",
    description: "Library operations and circulation workspace.",
  },
  caterer: {
    label: "Caterer",
    short_label: "Dining",
    description: "Dining or canteen checkout workspace.",
  },
  technician: {
    label: "Technician",
    short_label: "Support",
    description: "Service desk and technical operations workspace.",
  },
  accountant: {
    label: "Accountant",
    short_label: "Finance",
    description: "Finance, billing, and payment operations workspace.",
  },
  hr: {
    label: "Human Resources",
    short_label: "HR",
    description: "Human resources and staff operations workspace.",
  },
  admin: {
    label: "Admin",
    short_label: "Admin",
    description: "Platform administration workspace.",
  },
}

const DEFAULT_MODULE_LABELS: UmsModuleLabels = {
  admissions: "Admissions",
  public_website: "Public Website",
  venue_booking: "Venue Booking",
  canteen: "Dining",
  library: "Library",
  library_laptops: "Library Laptops",
  library_rooms: "Library Rooms",
  ict_helpdesk: "Service Desk",
  hostel: "Hostel",
  elections: "Elections",
  finance: "Finance",
  attendance: "Attendance",
  evaluations: "Evaluations",
  leave: "Leave",
  notifications: "Notifications",
  fines: "Fines",
  quizzes: "Quizzes",
}

const allOptionalFeatures = Object.keys(DEFAULT_MODULE_LABELS) as OptionalFeatureKey[]

const DEFAULT_MODULE_PERMISSIONS: UmsModulePermissions = {
  applicant: ["admissions", "notifications"],
  student: [
    "venue_booking",
    "canteen",
    "library",
    "library_laptops",
    "library_rooms",
    "ict_helpdesk",
    "hostel",
    "elections",
    "finance",
    "attendance",
    "evaluations",
    "leave",
    "notifications",
    "fines",
    "quizzes",
  ],
  teacher: [
    "finance",
    "venue_booking",
    "attendance",
    "evaluations",
    "leave",
    "notifications",
    "quizzes",
  ],
  executive: [
    "venue_booking",
    "elections",
    "finance",
    "attendance",
    "evaluations",
    "notifications",
  ],
  librarian: ["finance", "library", "library_laptops", "library_rooms", "notifications"],
  caterer: ["finance", "canteen", "notifications"],
  technician: ["finance", "ict_helpdesk", "venue_booking", "elections", "notifications"],
  accountant: ["finance", "canteen", "fines", "notifications"],
  hr: ["finance", "notifications"],
  admin: allOptionalFeatures,
}

export const DEFAULT_UMS_PUBLIC_SETTINGS: UmsPublicSettings = {
  maintenance: {
    enabled: false,
  },
  general: {
    portal_name: "University Portal",
    support_email: "support@example.edu",
    support_phone: "+00 000 000 0000",
    maintenance_banner: "",
  },
  university: {
    name: "Your University",
    short_name: "UNI",
    legal_name: "Your University",
    tagline: "Configurable university portal",
    description: "A configurable institution profile powered by the university portal.",
    address: "University address",
    phone: "+00 000 000 0000",
    email: "info@example.edu",
    admissions_email: "admissions@example.edu",
    website_url: "https://example.edu",
    logo_url: "/images/ums/ums-logo.svg",
    public_hero_image_url: "",
    social_image_url: "",
    login_image_url: "",
    favicon_url: "",
  },
  localization: {
    timezone: "UTC",
    locale: "en-US",
    currency_code: "USD",
    currency_symbol: "$",
    number_format: "1,234.56",
    date_format: "YYYY-MM-DD",
    time_format: "HH:mm",
  },
  terminology: {
    school_label: "School",
    center_label: "Center",
    centre_label: "Center",
    department_label: "Department",
    unit_label: "Unit",
    program_label: "Program",
    programme_label: "Program",
    course_label: "Course",
    semester_label: "Semester",
    academic_year_label: "Academic Year",
    student_id_label: "Student ID",
    staff_id_label: "Staff ID",
    applicant_label: "Applicant",
  },
  branding: {
    primary_color: "#18181b",
    secondary_color: "#f4f4f5",
    accent_color: "#0f766e",
    logo_url: "/images/ums/ums-logo.svg",
    public_hero_image_url: "",
    login_image_url: "",
    favicon_url: "",
    social_image_url: "",
  },
  uiCustomization: {
    brand_name: "University Portal",
    sidebar_label: "University Portal",
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
    accent_color: "#0f766e",
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
    admissions: true,
    public_website: true,
    venue_booking: true,
    canteen: true,
    library: true,
    library_laptops: true,
    library_rooms: true,
    ict_helpdesk: true,
    hostel: true,
    elections: true,
    finance: true,
    attendance: true,
    evaluations: true,
    leave: true,
    notifications: true,
    fines: true,
    quizzes: true,
  },
  roles: DEFAULT_ROLE_SETTINGS,
  module_labels: DEFAULT_MODULE_LABELS,
  module_permissions: DEFAULT_MODULE_PERMISSIONS,
  library_services: {
    books_enabled: true,
    laptops_enabled: true,
    rooms_enabled: true,
  },
  policies: {
    password: {
      min_length: 8,
      max_length: 20,
      require_uppercase: false,
      require_number: true,
    },
    uploads: {
      default_limit_mb: 10,
      default_allowed_file_extensions: "pdf,jpg,jpeg,png,webp",
      applicant_max_upload_mb: 5,
      applicant_allowed_file_extensions: "pdf,jpg,jpeg,png,webp,heic,heif",
    },
    venue_booking: {
      enabled: true,
      label: "Venue Booking",
      requester_roles: ["student", "teacher"],
      approval_mode: "manual",
      reviewer_role: "technician",
      min_duration_minutes: 30,
      max_duration_hours: 8,
      venue_categories: [
        { value: "classroom", label: "Classroom" },
        { value: "lecture_hall", label: "Lecture hall" },
        { value: "laboratory", label: "Laboratory" },
        { value: "auditorium", label: "Auditorium" },
        { value: "meeting_room", label: "Meeting room" },
        { value: "sports", label: "Sports facility" },
        { value: "other", label: "Other venue" },
      ],
      required_fields: {
        event: ["purpose", "explanation"],
        personal: ["purpose", "explanation"],
      },
      blackout_ranges: [],
    },
    dining: {
      enabled: true,
      label: "Dining",
      monthly_allowance_amount: "50.00",
      allowance_reset_timezone: "",
      allowance_reset_day: 1,
      allowance_reset_hour: 8,
      eligible_enrollment_statuses: "",
      ineligible_enrollment_status_markers:
        "terminated,graduat,dropout,drop out,withdraw,internship,intern",
      require_scholarship: false,
      eligible_program_codes: "",
      eligible_cohort_codes: "",
      sync_balance_to_student_profile: true,
    },
    attendance_threshold_percent: 80,
    leave_notice_period_days: 0,
    default_academic_calendar_type: "semester",
    default_application_number_prefix: "APP",
    default_payment_gateway_provider: "manual",
    payment_reference_prefix: "PORTAL",
  },
  setup: {
    complete: false,
    completed: 0,
    total: 0,
    items: [],
  },
}

export const UMS_ROUTE_MODULE_REGISTRY: UmsRouteModuleRule[] = [
  {
    features: ["public_website"],
    labelFeatures: [],
    exactPaths: ["/"],
    prefixes: [
      "/about",
      "/centers",
      "/centres",
      "/contact",
      "/departments",
      "/directories",
      "/events",
      "/news",
      "/official-links",
      "/programmes",
      "/programs",
      "/scholarship",
      "/schools",
      "/services",
      "/student-life",
      "/ums-overview",
      "/units",
      "/admin/public-content",
    ],
  },
  {
    features: ["admissions"],
    labelFeatures: [],
    prefixes: ["/apply"],
  },
  {
    features: ["admissions"],
    prefixes: ["/admissions", "/admin/manage/applicants"],
  },
  {
    features: ["venue_booking"],
    prefixes: [
      "/admin/venues",
      "/admin/venue-bookings",
      "/technician/venue-bookings",
      "/student/venue-bookings",
      "/teacher/venue-bookings",
    ],
  },
  {
    features: ["canteen"],
    labelFeatures: [],
    prefixes: ["/caterer"],
  },
  {
    features: ["canteen"],
    prefixes: [
      "/accountant/canteen",
      "/student/canteen",
      "/admin/create-account/caterer",
      "/admin/manage/caterers",
    ],
  },
  {
    features: ["library"],
    labelFeatures: [],
    prefixes: ["/librarian"],
  },
  {
    features: ["library"],
    prefixes: [
      "/student/library",
      "/admin/create-account/librarian",
      "/admin/manage/librarians",
    ],
  },
  {
    features: ["library_laptops"],
    prefixes: ["/student/library/laptops", "/librarian/laptops"],
  },
  {
    features: ["library_rooms"],
    prefixes: ["/student/library/rooms", "/librarian/rooms"],
  },
  {
    features: ["ict_helpdesk"],
    prefixes: [
      "/student/ict-helpdesk",
      "/technician/helpdesk",
      "/admin/create-account/technician",
      "/admin/manage/technicians",
    ],
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
    features: ["finance"],
    labelFeatures: [],
    prefixes: ["/accountant"],
  },
  {
    features: ["finance"],
    prefixes: [
      "/admin/create-account/accountant",
      "/admin/manage/accountants",
      "/admin/subscriptions",
      "/caterer/subscriptions",
      "/executive/subscriptions",
      "/hr/subscriptions",
      "/librarian/subscriptions",
      "/payment-return",
      "/student/subscriptions",
      "/teacher/subscriptions",
      "/technician/subscriptions",
    ],
  },
  {
    features: ["attendance"],
    prefixes: ["/student/attendance", "/teacher/attendance"],
  },
  {
    features: ["evaluations"],
    prefixes: ["/student/evaluations", "/teacher/evaluations", "/executive/evaluations"],
  },
  {
    features: ["leave"],
    prefixes: ["/student/leave", "/teacher/leave-requests"],
  },
  {
    features: ["notifications"],
    prefixes: [
      "/notifications",
      "/admin/notifications",
      "/applicant/notifications",
      "/apply/notifications",
      "/caterer/notifications",
      "/executive/notifications",
      "/hr/notifications",
      "/librarian/notifications",
      "/student/notifications",
      "/teacher/notifications",
      "/technician/notifications",
      "/accountant/notifications",
    ],
  },
  {
    features: ["fines"],
    prefixes: ["/accountant/fines", "/accountant/ledger/fines", "/student/fines"],
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

function numberValue(value: unknown, fallback: number) {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : fallback
}

function textArray(value: unknown, fallback: string[], allowEmpty = false) {
  if (!Array.isArray(value)) return fallback
  const items = value.filter((item): item is string => typeof item === "string" && Boolean(item.trim()))
  return items.length || allowEmpty ? Array.from(new Set(items)) : fallback
}

function optionArray(
  value: unknown,
  fallback: Array<{ value: string; label: string }>
) {
  if (!Array.isArray(value)) return fallback
  const options = value
    .map((item) => {
      const raw =
        item && typeof item === "object"
          ? (item as Record<string, unknown>)
          : {}
      return {
        value: text(raw.value, ""),
        label: text(raw.label, ""),
      }
    })
    .filter((item) => item.value && item.label)
  return options.length ? options : fallback
}

function venueRequiredFields(
  value: unknown,
  fallback: Record<"event" | "personal", string[]>
) {
  const incoming =
    value && typeof value === "object"
      ? (value as Partial<Record<"event" | "personal", unknown>>)
      : {}
  return {
    event: textArray(incoming.event, fallback.event, true),
    personal: textArray(incoming.personal, fallback.personal, true),
  }
}

function blackoutRangeArray(
  value: unknown,
  fallback: Array<{ start: string; end: string }>
) {
  if (!Array.isArray(value)) return fallback
  const ranges = value
    .map((item) => {
      const raw =
        item && typeof item === "object"
          ? (item as Record<string, unknown>)
          : {}
      return {
        start: text(raw.start, ""),
        end: text(raw.end, ""),
      }
    })
    .filter((item) => item.start && item.end)
  return ranges.length ? ranges : fallback
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

export function isOptionalFeatureKey(value: string): value is OptionalFeatureKey {
  return allOptionalFeatures.includes(value as OptionalFeatureKey)
}

function roleSettings(value: unknown): UmsRoleSettings {
  const incoming =
    value && typeof value === "object"
      ? (value as Partial<Record<UserRole, Partial<UmsRoleSetting>>>)
      : {}
  return Object.fromEntries(
    UMS_ROLES.map((role) => {
      const roleConfig = incoming[role] ?? {}
      const fallback = DEFAULT_ROLE_SETTINGS[role]
      return [
        role,
        {
          label: text(roleConfig.label, fallback.label),
          short_label: text(roleConfig.short_label, fallback.short_label),
          description: text(roleConfig.description, fallback.description),
        },
      ]
    })
  ) as UmsRoleSettings
}

function moduleLabels(value: unknown): UmsModuleLabels {
  const incoming =
    value && typeof value === "object"
      ? (value as Partial<Record<OptionalFeatureKey, unknown>>)
      : {}
  return Object.fromEntries(
    allOptionalFeatures.map((feature) => [
      feature,
      text(incoming[feature], DEFAULT_MODULE_LABELS[feature]),
    ])
  ) as UmsModuleLabels
}

function modulePermissions(value: unknown): UmsModulePermissions {
  const incoming =
    value && typeof value === "object"
      ? (value as Partial<Record<UserRole, unknown>>)
      : {}
  return Object.fromEntries(
    UMS_ROLES.map((role) => {
      const raw = incoming[role]
      const modules = Array.isArray(raw)
        ? raw.filter(
            (item): item is OptionalFeatureKey =>
              typeof item === "string" && isOptionalFeatureKey(item)
          )
        : DEFAULT_MODULE_PERMISSIONS[role]
      return [role, modules.length ? Array.from(new Set(modules)) : DEFAULT_MODULE_PERMISSIONS[role]]
    })
  ) as UmsModulePermissions
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
  const general =
    (incoming.general ?? {}) as Partial<UmsPublicSettings["general"]>
  const university =
    (incoming.university ?? {}) as Partial<UmsPublicSettings["university"]>
  const localization =
    (incoming.localization ?? {}) as Partial<UmsPublicSettings["localization"]>
  const terminology =
    (incoming.terminology ?? {}) as Partial<UmsPublicSettings["terminology"]>
  const branding =
    (incoming.branding ?? {}) as Partial<UmsPublicSettings["branding"]>
  const uiCustomization =
    (incomingCustomization.ui_customization ?? incomingCustomization.uiCustomization ?? {}) as Partial<UmsPublicSettings["uiCustomization"]>
  const maintenance =
    (incoming.maintenance ?? {}) as Partial<UmsPublicSettings["maintenance"]>
  const policies =
    (incoming.policies ?? {}) as Partial<UmsPublicSettings["policies"]>
  const passwordPolicy =
    (policies.password ?? {}) as Partial<UmsPublicSettings["policies"]["password"]>
  const uploadPolicy =
    (policies.uploads ?? {}) as Partial<UmsPublicSettings["policies"]["uploads"]>
  const venueBookingPolicy =
    (policies.venue_booking ?? {}) as Partial<UmsPublicSettings["policies"]["venue_booking"]>
  const diningPolicy =
    (policies.dining ?? {}) as Partial<UmsPublicSettings["policies"]["dining"]>
  const setup =
    (incoming.setup ?? {}) as Partial<UmsPublicSettings["setup"]>

  return {
    maintenance: {
      enabled: bool(
        maintenance.enabled,
        DEFAULT_UMS_PUBLIC_SETTINGS.maintenance.enabled
      ),
    },
    general: {
      portal_name: text(general.portal_name, DEFAULT_UMS_PUBLIC_SETTINGS.general.portal_name),
      support_email: text(general.support_email, DEFAULT_UMS_PUBLIC_SETTINGS.general.support_email),
      support_phone: text(general.support_phone, DEFAULT_UMS_PUBLIC_SETTINGS.general.support_phone),
      maintenance_banner: text(
        general.maintenance_banner,
        DEFAULT_UMS_PUBLIC_SETTINGS.general.maintenance_banner
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
      login_image_url: text(
        university.login_image_url,
        DEFAULT_UMS_PUBLIC_SETTINGS.university.login_image_url
      ),
      favicon_url: text(university.favicon_url, DEFAULT_UMS_PUBLIC_SETTINGS.university.favicon_url),
    },
    localization: {
      timezone: text(localization.timezone, DEFAULT_UMS_PUBLIC_SETTINGS.localization.timezone),
      locale: text(localization.locale, DEFAULT_UMS_PUBLIC_SETTINGS.localization.locale),
      currency_code: text(
        localization.currency_code,
        DEFAULT_UMS_PUBLIC_SETTINGS.localization.currency_code
      ).toUpperCase(),
      currency_symbol: text(
        localization.currency_symbol,
        DEFAULT_UMS_PUBLIC_SETTINGS.localization.currency_symbol
      ),
      number_format: text(
        localization.number_format,
        DEFAULT_UMS_PUBLIC_SETTINGS.localization.number_format
      ),
      date_format: text(localization.date_format, DEFAULT_UMS_PUBLIC_SETTINGS.localization.date_format),
      time_format: text(localization.time_format, DEFAULT_UMS_PUBLIC_SETTINGS.localization.time_format),
    },
    terminology: {
      school_label: text(terminology.school_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.school_label),
      center_label: text(terminology.center_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.center_label),
      centre_label: text(
        terminology.centre_label ?? terminology.center_label,
        DEFAULT_UMS_PUBLIC_SETTINGS.terminology.centre_label
      ),
      department_label: text(terminology.department_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.department_label),
      unit_label: text(terminology.unit_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.unit_label),
      program_label: text(terminology.program_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.program_label),
      programme_label: text(
        terminology.programme_label ?? terminology.program_label,
        DEFAULT_UMS_PUBLIC_SETTINGS.terminology.programme_label
      ),
      course_label: text(terminology.course_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.course_label),
      semester_label: text(terminology.semester_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.semester_label),
      academic_year_label: text(
        terminology.academic_year_label,
        DEFAULT_UMS_PUBLIC_SETTINGS.terminology.academic_year_label
      ),
      student_id_label: text(terminology.student_id_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.student_id_label),
      staff_id_label: text(terminology.staff_id_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.staff_id_label),
      applicant_label: text(terminology.applicant_label, DEFAULT_UMS_PUBLIC_SETTINGS.terminology.applicant_label),
    },
    branding: {
      primary_color: text(branding.primary_color, DEFAULT_UMS_PUBLIC_SETTINGS.branding.primary_color),
      secondary_color: text(branding.secondary_color, DEFAULT_UMS_PUBLIC_SETTINGS.branding.secondary_color),
      accent_color: text(branding.accent_color, DEFAULT_UMS_PUBLIC_SETTINGS.branding.accent_color),
      logo_url: text(branding.logo_url, DEFAULT_UMS_PUBLIC_SETTINGS.branding.logo_url),
      public_hero_image_url: text(
        branding.public_hero_image_url,
        DEFAULT_UMS_PUBLIC_SETTINGS.branding.public_hero_image_url
      ),
      login_image_url: text(branding.login_image_url, DEFAULT_UMS_PUBLIC_SETTINGS.branding.login_image_url),
      favicon_url: text(branding.favicon_url, DEFAULT_UMS_PUBLIC_SETTINGS.branding.favicon_url),
      social_image_url: text(branding.social_image_url, DEFAULT_UMS_PUBLIC_SETTINGS.branding.social_image_url),
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
      accent_color: text(uiCustomization.accent_color, DEFAULT_UMS_PUBLIC_SETTINGS.uiCustomization.accent_color),
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
    roles: roleSettings(incoming.roles),
    module_labels: moduleLabels(incoming.module_labels),
    module_permissions: modulePermissions(incoming.module_permissions),
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
    policies: {
      password: {
        min_length: numberValue(
          passwordPolicy.min_length,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.password.min_length
        ),
        max_length: numberValue(
          passwordPolicy.max_length,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.password.max_length
        ),
        require_uppercase: bool(
          passwordPolicy.require_uppercase,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.password.require_uppercase
        ),
        require_number: bool(
          passwordPolicy.require_number,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.password.require_number
        ),
      },
      uploads: {
        default_limit_mb: numberValue(
          uploadPolicy.default_limit_mb,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.uploads.default_limit_mb
        ),
        default_allowed_file_extensions: text(
          uploadPolicy.default_allowed_file_extensions,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.uploads.default_allowed_file_extensions
        ),
        applicant_max_upload_mb: numberValue(
          uploadPolicy.applicant_max_upload_mb,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.uploads.applicant_max_upload_mb
        ),
        applicant_allowed_file_extensions: text(
          uploadPolicy.applicant_allowed_file_extensions,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.uploads.applicant_allowed_file_extensions
        ),
      },
      venue_booking: {
        enabled: bool(
          venueBookingPolicy.enabled,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.enabled
        ),
        label: text(
          venueBookingPolicy.label,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.label
        ),
        requester_roles: textArray(
          venueBookingPolicy.requester_roles,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.requester_roles
        ),
        approval_mode: text(
          venueBookingPolicy.approval_mode,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.approval_mode
        ),
        reviewer_role: text(
          venueBookingPolicy.reviewer_role,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.reviewer_role
        ),
        min_duration_minutes: numberValue(
          venueBookingPolicy.min_duration_minutes,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.min_duration_minutes
        ),
        max_duration_hours: numberValue(
          venueBookingPolicy.max_duration_hours,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.max_duration_hours
        ),
        venue_categories: optionArray(
          venueBookingPolicy.venue_categories,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.venue_categories
        ),
        required_fields: venueRequiredFields(
          venueBookingPolicy.required_fields,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.required_fields
        ),
        blackout_ranges: blackoutRangeArray(
          venueBookingPolicy.blackout_ranges,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.venue_booking.blackout_ranges
        ),
      },
      dining: {
        enabled: bool(
          diningPolicy.enabled,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.enabled
        ),
        label: text(
          diningPolicy.label,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.label
        ),
        monthly_allowance_amount: text(
          diningPolicy.monthly_allowance_amount,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.monthly_allowance_amount
        ),
        allowance_reset_timezone: text(
          diningPolicy.allowance_reset_timezone,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.allowance_reset_timezone
        ),
        allowance_reset_day: numberValue(
          diningPolicy.allowance_reset_day,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.allowance_reset_day
        ),
        allowance_reset_hour: numberValue(
          diningPolicy.allowance_reset_hour,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.allowance_reset_hour
        ),
        eligible_enrollment_statuses: text(
          diningPolicy.eligible_enrollment_statuses,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.eligible_enrollment_statuses
        ),
        ineligible_enrollment_status_markers: text(
          diningPolicy.ineligible_enrollment_status_markers,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.ineligible_enrollment_status_markers
        ),
        require_scholarship: bool(
          diningPolicy.require_scholarship,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.require_scholarship
        ),
        eligible_program_codes: text(
          diningPolicy.eligible_program_codes,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.eligible_program_codes
        ),
        eligible_cohort_codes: text(
          diningPolicy.eligible_cohort_codes,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.eligible_cohort_codes
        ),
        sync_balance_to_student_profile: bool(
          diningPolicy.sync_balance_to_student_profile,
          DEFAULT_UMS_PUBLIC_SETTINGS.policies.dining.sync_balance_to_student_profile
        ),
      },
      attendance_threshold_percent: numberValue(
        policies.attendance_threshold_percent,
        DEFAULT_UMS_PUBLIC_SETTINGS.policies.attendance_threshold_percent
      ),
      leave_notice_period_days: numberValue(
        policies.leave_notice_period_days,
        DEFAULT_UMS_PUBLIC_SETTINGS.policies.leave_notice_period_days
      ),
      default_academic_calendar_type: text(
        policies.default_academic_calendar_type,
        DEFAULT_UMS_PUBLIC_SETTINGS.policies.default_academic_calendar_type
      ),
      default_application_number_prefix: text(
        policies.default_application_number_prefix,
        DEFAULT_UMS_PUBLIC_SETTINGS.policies.default_application_number_prefix
      ),
      default_payment_gateway_provider: text(
        policies.default_payment_gateway_provider,
        DEFAULT_UMS_PUBLIC_SETTINGS.policies.default_payment_gateway_provider
      ),
      payment_reference_prefix: text(
        policies.payment_reference_prefix,
        DEFAULT_UMS_PUBLIC_SETTINGS.policies.payment_reference_prefix
      ),
    },
    setup: {
      complete: bool(setup.complete, DEFAULT_UMS_PUBLIC_SETTINGS.setup.complete),
      completed: numberValue(setup.completed, DEFAULT_UMS_PUBLIC_SETTINGS.setup.completed),
      total: numberValue(setup.total, DEFAULT_UMS_PUBLIC_SETTINGS.setup.total),
      items: Array.isArray(setup.items)
        ? setup.items.map((item) => {
            const raw =
              item && typeof item === "object"
                ? (item as Record<string, unknown>)
                : {}
            return {
              key: text(raw.key, ""),
              section: text(raw.section, ""),
              field: text(raw.field, ""),
              label: text(raw.label, ""),
              complete: bool(raw.complete, false),
            }
          })
        : DEFAULT_UMS_PUBLIC_SETTINGS.setup.items,
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

export function formatUmsMoney(
  value: unknown,
  settings: UmsPublicSettings = DEFAULT_UMS_PUBLIC_SETTINGS,
  currencyOverride?: string | null
) {
  const amount = Number(value ?? 0)
  const numericAmount = Number.isFinite(amount) ? amount : 0
  const locale = settings.localization.locale || DEFAULT_UMS_PUBLIC_SETTINGS.localization.locale
  const currency = (
    currencyOverride ||
    settings.localization.currency_code ||
    DEFAULT_UMS_PUBLIC_SETTINGS.localization.currency_code
  ).toUpperCase()
  try {
    return new Intl.NumberFormat(locale, {
      currency,
      maximumFractionDigits: 2,
      style: "currency",
    }).format(numericAmount)
  } catch {
    const settingsCurrency = (
      settings.localization.currency_code ||
      DEFAULT_UMS_PUBLIC_SETTINGS.localization.currency_code
    ).toUpperCase()
    const symbol =
      currencyOverride && currency !== settingsCurrency
        ? currency
        : settings.localization.currency_symbol ||
          DEFAULT_UMS_PUBLIC_SETTINGS.localization.currency_symbol ||
          currency
    const separator = symbol.length === 1 ? "" : " "
    return `${symbol}${separator}${numericAmount.toFixed(2)}`
  }
}

export function isUmsFeaturePathEnabled(
  pathname: string,
  features: Record<OptionalFeatureKey, boolean>
) {
  const rules = featureRulesForPath(pathname)
  if (!rules.length) return true
  return rules.every((rule) =>
    rule.features.some((feature) => features[feature] !== false)
  )
}

function normalizedRoutePath(pathname: string) {
  const path = pathname.replace(/\/+$/, "") || "/"
  return path.toLowerCase()
}

function featureRulesForPath(pathname: string) {
  const path = normalizedRoutePath(pathname)
  return UMS_ROUTE_MODULE_REGISTRY.filter(
    (candidate) => routeRuleMatchScore(path, candidate) !== null
  )
}

function routeRuleMatchScore(path: string, rule: UmsRouteModuleRule) {
  const exactScore = rule.exactPaths
    ?.map((exactPath) => normalizedRoutePath(exactPath))
    .find((exactPath) => path === exactPath)
  if (exactScore) return exactScore.length + 1000

  const prefixScores =
    rule.prefixes
      ?.map((prefix) => normalizedRoutePath(prefix))
      .filter((prefix) => path === prefix || path.startsWith(`${prefix}/`))
      .map((prefix) => prefix.length) ?? []
  if (!prefixScores.length) return null
  return Math.max(...prefixScores)
}

export function umsRouteModulesForPath(pathname: string): OptionalFeatureKey[] {
  return Array.from(
    new Set(featureRulesForPath(pathname).flatMap((rule) => rule.features))
  )
}

function primaryUmsRouteLabelModulesForPath(pathname: string): OptionalFeatureKey[] {
  const path = normalizedRoutePath(pathname)
  const matches = UMS_ROUTE_MODULE_REGISTRY.map((rule) => ({
    rule,
    score: routeRuleMatchScore(path, rule),
  }))
    .filter(
      (match): match is { rule: UmsRouteModuleRule; score: number } =>
        match.score !== null && (match.rule.labelFeatures ?? match.rule.features).length > 0
    )
    .sort((left, right) => right.score - left.score)

  return matches[0]
    ? matches[0].rule.labelFeatures ?? matches[0].rule.features
    : []
}

export function isUmsRoleFeaturePathEnabled(
  pathname: string,
  settings: UmsPublicSettings,
  role: UserRole
) {
  const rules = featureRulesForPath(pathname)
  if (!rules.length) return true
  const allowedModules = settings.module_permissions[role] ?? allOptionalFeatures
  const featureAllowed = rules.every((rule) =>
    rule.features.some(
      (feature) =>
        settings.features[feature] !== false && allowedModules.includes(feature)
    )
  )
  if (!featureAllowed) return false
  if (rules.some((rule) => rule.features.includes("venue_booking"))) {
    return isVenueBookingPolicyPathEnabled(pathname, settings, role)
  }
  return true
}

export function disabledUmsRouteModules(
  pathname: string,
  settings: UmsPublicSettings,
  role?: UserRole
): OptionalFeatureKey[] {
  const allowedModules = role
    ? settings.module_permissions[role] ?? allOptionalFeatures
    : allOptionalFeatures
  const disabled = new Set<OptionalFeatureKey>()

  for (const rule of featureRulesForPath(pathname)) {
    const hasEnabledFeature = rule.features.some(
      (feature) =>
        settings.features[feature] !== false &&
        (!role || allowedModules.includes(feature))
    )
    if (!hasEnabledFeature) {
      rule.features.forEach((feature) => disabled.add(feature))
    }
  }

  return Array.from(disabled)
}

export function umsModuleLabels(
  features: OptionalFeatureKey[],
  settings: UmsPublicSettings = DEFAULT_UMS_PUBLIC_SETTINGS
): string[] {
  return features
    .map((feature) => settings.module_labels[feature] || DEFAULT_MODULE_LABELS[feature])
    .filter(Boolean)
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

function capitalizeWords(value: string) {
  return value.replace(/\b\w/g, (character) => character.toUpperCase())
}

function pluralizeLabel(label: string) {
  const value = label.trim()
  if (!value) return value
  const [head, ...tail] = value.split(/\s+/).reverse()
  const pluralHead = /[^aeiou]y$/i.test(head)
    ? `${head.slice(0, -1)}ies`
    : /(s|x|z|ch|sh)$/i.test(head)
      ? `${head}es`
      : `${head}s`
  return [pluralHead, ...tail].reverse().join(" ")
}

function textWithCase(source: string, replacement: string) {
  if (source.toUpperCase() === source) return replacement.toUpperCase()
  if (source.charAt(0).toUpperCase() === source.charAt(0)) {
    return capitalizeWords(replacement)
  }
  return replacement.toLowerCase()
}

function replaceTerm(textValue: string, source: string, replacement: string) {
  if (!source || !replacement) return textValue
  const pattern = new RegExp(`\\b${escapeRegExp(source)}\\b`, "gi")
  return textValue.replace(pattern, (match) => textWithCase(match, replacement))
}

export function applyUmsTerminology(
  value: string,
  settings: UmsPublicSettings = DEFAULT_UMS_PUBLIC_SETTINGS
) {
  const terminology = settings.terminology
  const modules = settings.module_labels
  const replacements: Array<[string, string]> = [
    ["academic years", pluralizeLabel(terminology.academic_year_label)],
    ["academic year", terminology.academic_year_label],
    ["venue bookings", pluralizeLabel(modules.venue_booking)],
    ["venue booking", modules.venue_booking],
    ["ict helpdesk", modules.ict_helpdesk],
    ["service desks", pluralizeLabel(modules.ict_helpdesk)],
    ["service desk", modules.ict_helpdesk],
    ["ict", modules.ict_helpdesk],
    ["library laptops", modules.library_laptops],
    ["library rooms", modules.library_rooms],
    ["canteens", pluralizeLabel(modules.canteen)],
    ["canteen", modules.canteen],
    ["dining", modules.canteen],
    ["hostels", pluralizeLabel(modules.hostel)],
    ["hostel", modules.hostel],
    ["elections", modules.elections],
    ["election", modules.elections],
    ["notifications", modules.notifications],
    ["notification", modules.notifications],
    ["evaluations", modules.evaluations],
    ["evaluation", modules.evaluations],
    ["quizzes", modules.quizzes],
    ["quiz", modules.quizzes],
    ["fines", modules.fines],
    ["fine", modules.fines],
    ["finance", modules.finance],
    ["libraries", pluralizeLabel(modules.library)],
    ["library", modules.library],
    ["attendance", modules.attendance],
    ["leave", modules.leave],
    ["admissions", modules.admissions],
    ["student ids", pluralizeLabel(terminology.student_id_label)],
    ["student id", terminology.student_id_label],
    ["staff ids", pluralizeLabel(terminology.staff_id_label)],
    ["staff id", terminology.staff_id_label],
    ["programmes", pluralizeLabel(terminology.programme_label)],
    ["programme", terminology.programme_label],
    ["programs", pluralizeLabel(terminology.program_label)],
    ["program", terminology.program_label],
    ["centres", pluralizeLabel(terminology.centre_label)],
    ["centre", terminology.centre_label],
    ["centers", pluralizeLabel(terminology.center_label)],
    ["center", terminology.center_label],
    ["schools", pluralizeLabel(terminology.school_label)],
    ["school", terminology.school_label],
    ["departments", pluralizeLabel(terminology.department_label)],
    ["department", terminology.department_label],
    ["semesters", pluralizeLabel(terminology.semester_label)],
    ["semester", terminology.semester_label],
    ["applicants", pluralizeLabel(terminology.applicant_label)],
    ["applicant", terminology.applicant_label],
    ["courses", pluralizeLabel(terminology.course_label)],
    ["course", terminology.course_label],
    ["units", pluralizeLabel(terminology.unit_label)],
    ["unit", terminology.unit_label],
  ]

  return replacements.reduce(
    (current, [source, replacement]) => replaceTerm(current, source, replacement),
    value
  )
}

function isVenueBookingPolicyPathEnabled(
  pathname: string,
  settings: UmsPublicSettings,
  role: UserRole
) {
  const path = pathname.replace(/\/+$/, "") || "/"
  const policy = settings.policies.venue_booking
  if (path === "/student/venue-bookings" || path.startsWith("/student/venue-bookings/")) {
    return role === "student" && policy.requester_roles.includes("student")
  }
  if (path === "/teacher/venue-bookings" || path.startsWith("/teacher/venue-bookings/")) {
    return role === "teacher" && policy.requester_roles.includes("teacher")
  }
  if (path === "/technician/venue-bookings" || path.startsWith("/technician/venue-bookings/")) {
    return (
      role === "technician" &&
      policy.approval_mode === "manual" &&
      policy.reviewer_role === "technician"
    )
  }
  if (path === "/admin/venue-bookings" || path.startsWith("/admin/venue-bookings/")) {
    return (
      role === "admin" &&
      policy.approval_mode === "manual" &&
      policy.reviewer_role === "admin"
    )
  }
  return true
}

function navItemWithConfiguredLabel(
  item: UmsNavItem,
  settings: UmsPublicSettings
): UmsNavItem {
  const routeModules = primaryUmsRouteLabelModulesForPath(item.url)
  const moduleLabel = routeModules.length
    ? routeModules
        .map((feature) => settings.module_labels[feature])
        .find(Boolean)
    : ""
  return {
    ...item,
    title: applyUmsTerminology(moduleLabel || item.title, settings),
    description: item.description
      ? applyUmsTerminology(item.description, settings)
      : item.description,
    items: item.items?.map((child) => ({
      ...child,
      title: applyUmsTerminology(child.title, settings),
      description: child.description
        ? applyUmsTerminology(child.description, settings)
        : child.description,
    })),
  }
}

export function filterUmsNavItemsByFeatures(
  items: UmsNavItem[],
  features: Record<OptionalFeatureKey, boolean>,
  libraryServices?: { books_enabled: boolean; laptops_enabled: boolean; rooms_enabled: boolean }
): UmsNavItem[] {
  return items
    .filter((item) => navItemEnabledForFeatures(item, features))
    .filter((item) => !libraryServices || item.items?.length || libraryServicePathEnabled(item.url, libraryServices))
    .map((item) => {
      const filteredChildren = item.items?.filter((child) => {
        if (!isUmsFeaturePathEnabled(child.url, features)) return false
        if (libraryServices && !libraryServicePathEnabled(child.url, libraryServices)) return false
        return true
      })
      return {
        ...item,
        url: libraryFallbackUrl(item.url, filteredChildren, libraryServices),
        items: filteredChildren,
      }
    })
    .filter((item) => !item.items || item.items.length > 0)
}

export function filterUmsNavItemsBySettings(
  items: UmsNavItem[],
  settings: UmsPublicSettings,
  role: UserRole
): UmsNavItem[] {
  return items
    .filter((item) => isUmsRoleFeaturePathEnabled(item.url, settings, role))
    .filter((item) => item.items?.length || libraryServicePathEnabled(item.url, settings.library_services))
    .map((item) => {
      const configuredItem = navItemWithConfiguredLabel(item, settings)
      const filteredChildren = configuredItem.items?.filter((child) => {
        if (!isUmsRoleFeaturePathEnabled(child.url, settings, role)) {
          return false
        }
        if (!libraryServicePathEnabled(child.url, settings.library_services)) return false
        return true
      })
      return {
        ...configuredItem,
        url: libraryFallbackUrl(configuredItem.url, filteredChildren, settings.library_services),
        items: filteredChildren,
      }
    })
    .filter((item) => !item.items || item.items.length > 0)
}

function libraryServicePathEnabled(
  url: string,
  libraryServices: { books_enabled: boolean; laptops_enabled: boolean; rooms_enabled: boolean }
) {
  const path = url.toLowerCase()
  if (path.includes("/library/books") || path === "/librarian/books" || path.startsWith("/librarian/books/")) {
    return libraryServices.books_enabled
  }
  if (path.includes("/library/laptops") || path === "/librarian/laptops" || path.startsWith("/librarian/laptops/")) {
    return libraryServices.laptops_enabled
  }
  if (path.includes("/library/rooms") || path === "/librarian/rooms" || path.startsWith("/librarian/rooms/")) {
    return libraryServices.rooms_enabled
  }
  return true
}

function libraryFallbackUrl(
  url: string,
  children: Array<{ url: string }> | undefined,
  libraryServices?: { books_enabled: boolean; laptops_enabled: boolean; rooms_enabled: boolean }
) {
  if (!libraryServices || !children?.length) return url
  if (libraryServicePathEnabled(url, libraryServices)) return url
  return children[0].url
}

export function zoneForUmsRole(
  role: UserRole,
  settings: UmsPublicSettings = DEFAULT_UMS_PUBLIC_SETTINGS
): UmsZone {
  const zone = ROLE_ZONES[role]
  const configuredRole = settings.roles[role]
  return {
    ...zone,
    label: applyUmsTerminology(configuredRole.label || zone.label, settings),
    shortLabel: applyUmsTerminology(
      configuredRole.short_label || zone.shortLabel,
      settings
    ),
    description: applyUmsTerminology(
      configuredRole.description || zone.description,
      settings
    ),
    headline: applyUmsTerminology(zone.headline, settings),
    scope: applyUmsTerminology(zone.scope, settings),
    priorities: zone.priorities.map((priority) =>
      applyUmsTerminology(priority, settings)
    ),
    metrics: zone.metrics.map((metric) => ({
      ...metric,
      title: applyUmsTerminology(metric.title, settings),
      subtitle: applyUmsTerminology(metric.subtitle, settings),
    })),
    navMain: zone.navMain.map((item) => ({
      ...item,
      title: applyUmsTerminology(item.title, settings),
      description: item.description
        ? applyUmsTerminology(item.description, settings)
        : item.description,
      items: item.items?.map((child) => ({
        ...child,
        title: applyUmsTerminology(child.title, settings),
        description: child.description
          ? applyUmsTerminology(child.description, settings)
          : child.description,
      })),
    })),
    navSecondary: zone.navSecondary.map((item) => ({
      ...item,
      title: applyUmsTerminology(item.title, settings),
      description: item.description
        ? applyUmsTerminology(item.description, settings)
        : item.description,
      items: item.items?.map((child) => ({
        ...child,
        title: applyUmsTerminology(child.title, settings),
        description: child.description
          ? applyUmsTerminology(child.description, settings)
          : child.description,
      })),
    })),
  }
}
