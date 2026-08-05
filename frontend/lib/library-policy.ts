export type LibraryAssetType = "book" | "laptop" | "room" | "other_asset"

export type LibraryDuration = {
  value: number
  unit: "days" | "hours"
  days?: number
  hours?: number
}

export type LibraryPolicy = {
  books_enabled: boolean
  laptops_enabled: boolean
  rooms_enabled: boolean
  other_assets_enabled: boolean
  service_types: Array<{
    key: LibraryAssetType
    label: string
    enabled: boolean
    requesting_enabled: boolean
    supported: boolean
  }>
  limits: Record<
    LibraryAssetType,
    { max_borrow_at_a_time: number; max_keep_at_a_time: number }
  >
  loan_periods: Record<LibraryAssetType, LibraryDuration>
  fine_rules: Record<LibraryAssetType, { daily_rate: string }>
  renewal_rules: Record<
    LibraryAssetType,
    { max_renewals: number; period: LibraryDuration }
  >
  reservation_rules: Record<LibraryAssetType, { enabled: boolean }>
}

export type LibraryServices = Pick<
  LibraryPolicy,
  "books_enabled" | "laptops_enabled" | "rooms_enabled" | "other_assets_enabled"
>

export const LIBRARY_ASSET_TYPES: LibraryAssetType[] = [
  "book",
  "laptop",
  "room",
  "other_asset",
]

export const LIBRARY_ASSET_LABELS: Record<LibraryAssetType, string> = {
  book: "Books",
  laptop: "Laptops",
  room: "Discussion rooms",
  other_asset: "Other assets",
}

export const DEFAULT_LIBRARY_POLICY: LibraryPolicy = {
  books_enabled: true,
  laptops_enabled: true,
  rooms_enabled: true,
  other_assets_enabled: false,
  service_types: [
    { key: "book", label: "Books", enabled: true, requesting_enabled: true, supported: true },
    { key: "laptop", label: "Laptops", enabled: true, requesting_enabled: true, supported: true },
    { key: "room", label: "Discussion rooms", enabled: true, requesting_enabled: true, supported: true },
    { key: "other_asset", label: "Other assets", enabled: false, requesting_enabled: false, supported: false },
  ],
  limits: {
    book: { max_borrow_at_a_time: 3, max_keep_at_a_time: 5 },
    laptop: { max_borrow_at_a_time: 1, max_keep_at_a_time: 1 },
    room: { max_borrow_at_a_time: 1, max_keep_at_a_time: 1 },
    other_asset: { max_borrow_at_a_time: 1, max_keep_at_a_time: 1 },
  },
  loan_periods: {
    book: { value: 14, unit: "days", days: 14 },
    laptop: { value: 7, unit: "days", days: 7 },
    room: { value: 2, unit: "hours", hours: 2 },
    other_asset: { value: 7, unit: "days", days: 7 },
  },
  fine_rules: {
    book: { daily_rate: "1.00" },
    laptop: { daily_rate: "5.00" },
    room: { daily_rate: "0.00" },
    other_asset: { daily_rate: "1.00" },
  },
  renewal_rules: {
    book: { max_renewals: 2, period: { value: 14, unit: "days", days: 14 } },
    laptop: { max_renewals: 0, period: { value: 7, unit: "days", days: 7 } },
    room: { max_renewals: 0, period: { value: 1, unit: "hours", hours: 1 } },
    other_asset: { max_renewals: 0, period: { value: 7, unit: "days", days: 7 } },
  },
  reservation_rules: {
    book: { enabled: true },
    laptop: { enabled: true },
    room: { enabled: true },
    other_asset: { enabled: false },
  },
}

function boolValue(value: unknown, fallback: boolean) {
  return typeof value === "boolean" ? value : fallback
}

function numberValue(value: unknown, fallback: number) {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback
}

function stringValue(value: unknown, fallback: string) {
  return typeof value === "string" && value.trim() ? value : fallback
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function durationValue(value: unknown, fallback: LibraryDuration): LibraryDuration {
  const record = recordValue(value)
  const unit = record.unit === "hours" ? "hours" : record.unit === "days" ? "days" : fallback.unit
  const duration = numberValue(record.value, fallback.value)
  return {
    value: duration,
    unit,
    days: unit === "days" ? duration : undefined,
    hours: unit === "hours" ? duration : undefined,
  }
}

function serviceEnabled(policy: LibraryServices, assetType: LibraryAssetType) {
  if (assetType === "book") return policy.books_enabled
  if (assetType === "laptop") return policy.laptops_enabled
  if (assetType === "room") return policy.rooms_enabled
  return policy.other_assets_enabled
}

export function normalizeLibraryPolicy(input: unknown): LibraryPolicy {
  const incoming = recordValue(input)
  const base = DEFAULT_LIBRARY_POLICY
  const services: LibraryServices = {
    books_enabled: boolValue(incoming.books_enabled, base.books_enabled),
    laptops_enabled: boolValue(incoming.laptops_enabled, base.laptops_enabled),
    rooms_enabled: boolValue(incoming.rooms_enabled, base.rooms_enabled),
    other_assets_enabled: boolValue(incoming.other_assets_enabled, base.other_assets_enabled),
  }
  const incomingLimits = recordValue(incoming.limits)
  const incomingLoanPeriods = recordValue(incoming.loan_periods)
  const incomingFineRules = recordValue(incoming.fine_rules)
  const incomingRenewalRules = recordValue(incoming.renewal_rules)
  const incomingReservationRules = recordValue(incoming.reservation_rules)
  const incomingServiceTypes = Array.isArray(incoming.service_types)
    ? incoming.service_types
    : []

  const limits = Object.fromEntries(
    LIBRARY_ASSET_TYPES.map((assetType) => {
      const fallback = base.limits[assetType]
      const value = recordValue(incomingLimits[assetType])
      return [
        assetType,
        {
          max_borrow_at_a_time: numberValue(value.max_borrow_at_a_time, fallback.max_borrow_at_a_time),
          max_keep_at_a_time: numberValue(value.max_keep_at_a_time, fallback.max_keep_at_a_time),
        },
      ]
    })
  ) as LibraryPolicy["limits"]

  const loanPeriods = Object.fromEntries(
    LIBRARY_ASSET_TYPES.map((assetType) => [
      assetType,
      durationValue(incomingLoanPeriods[assetType], base.loan_periods[assetType]),
    ])
  ) as LibraryPolicy["loan_periods"]

  const fineRules = Object.fromEntries(
    LIBRARY_ASSET_TYPES.map((assetType) => {
      const fallback = base.fine_rules[assetType]
      const value = recordValue(incomingFineRules[assetType])
      return [assetType, { daily_rate: stringValue(value.daily_rate, fallback.daily_rate) }]
    })
  ) as LibraryPolicy["fine_rules"]

  const renewalRules = Object.fromEntries(
    LIBRARY_ASSET_TYPES.map((assetType) => {
      const fallback = base.renewal_rules[assetType]
      const value = recordValue(incomingRenewalRules[assetType])
      return [
        assetType,
        {
          max_renewals: numberValue(value.max_renewals, fallback.max_renewals),
          period: durationValue(value.period, fallback.period),
        },
      ]
    })
  ) as LibraryPolicy["renewal_rules"]

  const reservationRules = Object.fromEntries(
    LIBRARY_ASSET_TYPES.map((assetType) => {
      const fallback = base.reservation_rules[assetType]
      const value = recordValue(incomingReservationRules[assetType])
      return [assetType, { enabled: boolValue(value.enabled, fallback.enabled) }]
    })
  ) as LibraryPolicy["reservation_rules"]

  const serviceTypes = LIBRARY_ASSET_TYPES.map((assetType) => {
    const existing = incomingServiceTypes.find(
      (item) => recordValue(item).key === assetType
    )
    const value = recordValue(existing)
    return {
      key: assetType,
      label: stringValue(value.label, LIBRARY_ASSET_LABELS[assetType]),
      enabled: serviceEnabled(services, assetType),
      requesting_enabled: boolValue(value.requesting_enabled, reservationRules[assetType].enabled),
      supported: boolValue(value.supported, assetType !== "other_asset"),
    }
  })

  return {
    ...services,
    service_types: serviceTypes,
    limits,
    loan_periods: loanPeriods,
    fine_rules: fineRules,
    renewal_rules: renewalRules,
    reservation_rules: reservationRules,
  }
}

export function libraryServiceEnabled(policy: LibraryPolicy, assetType: LibraryAssetType) {
  return serviceEnabled(policy, assetType)
}

export function libraryDurationLabel(duration: LibraryDuration) {
  const unit = duration.value === 1 ? duration.unit.replace(/s$/, "") : duration.unit
  return `${duration.value} ${unit}`
}
