type DateTimeFormatConfig = {
  locale?: string
  formatOptions?: Intl.DateTimeFormatOptions
}

type CurrencyFormatConfig = {
  locale?: string
  currency?: string
  minimumFractionDigits?: number
  maximumFractionDigits?: number
}

const numberFormatters = new Map<string, Intl.NumberFormat>()
const currencyFormatters = new Map<string, Intl.NumberFormat>()
const dateTimeFormatters = new Map<string, Intl.DateTimeFormat>()

const DEFAULT_LOCALE = "en-MY"
const DEFAULT_DATE_TIME_OPTIONS: Intl.DateTimeFormatOptions = {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
}

function getNumberFormatter(locale: string) {
  const key = locale || DEFAULT_LOCALE
  const cached = numberFormatters.get(key)
  if (cached) return cached
  const formatter = new Intl.NumberFormat(key)
  numberFormatters.set(key, formatter)
  return formatter
}

function getCurrencyFormatter(config: CurrencyFormatConfig) {
  const locale = config.locale || DEFAULT_LOCALE
  const currency = config.currency || "MYR"
  const minDigits = config.minimumFractionDigits ?? 2
  const maxDigits = config.maximumFractionDigits ?? 2
  const key = `${locale}|${currency}|${minDigits}|${maxDigits}`

  const cached = currencyFormatters.get(key)
  if (cached) return cached

  const formatter = new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: minDigits,
    maximumFractionDigits: maxDigits,
  })
  currencyFormatters.set(key, formatter)
  return formatter
}

function getDateTimeFormatter(config: DateTimeFormatConfig) {
  const locale = config.locale || DEFAULT_LOCALE
  const options = config.formatOptions || DEFAULT_DATE_TIME_OPTIONS
  const key = `${locale}|${JSON.stringify(options)}`

  const cached = dateTimeFormatters.get(key)
  if (cached) return cached

  const formatter = new Intl.DateTimeFormat(locale, options)
  dateTimeFormatters.set(key, formatter)
  return formatter
}

export function formatNumber(value: number, locale = DEFAULT_LOCALE) {
  return getNumberFormatter(locale).format(Math.round(value || 0))
}

export function formatCampaignItemQuantity(value?: number | null, locale = DEFAULT_LOCALE) {
  const quantity = Number(value || 0)
  if (quantity <= 0) return "Unspecified"
  return formatNumber(quantity, locale)
}

export function formatCampaignAvailability(
  quantityAvailable?: number | null,
  hasUnspecifiedQuantity?: boolean,
  locale = DEFAULT_LOCALE
) {
  const quantity = Math.max(Number(quantityAvailable || 0), 0)
  if (hasUnspecifiedQuantity && quantity > 0) {
    return `${formatNumber(quantity, locale)} listed + on-demand`
  }
  if (hasUnspecifiedQuantity) {
    return "Cooked to order"
  }
  return formatNumber(quantity, locale)
}

export function formatCurrency(value: number, config?: string | CurrencyFormatConfig) {
  const normalized: CurrencyFormatConfig =
    typeof config === "string" ? { locale: config } : (config ?? {})
  return getCurrencyFormatter(normalized).format(value || 0)
}

export function formatDateTime(value?: string | null, config?: string | DateTimeFormatConfig) {
  if (!value) return "N/A"
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return "N/A"

  const normalized: DateTimeFormatConfig =
    typeof config === "string" ? { locale: config } : (config ?? {})
  return getDateTimeFormatter(normalized).format(parsed)
}

export { DEFAULT_DATE_TIME_OPTIONS }
