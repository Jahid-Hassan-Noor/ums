"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import {
  AlertCircle,
  BookOpen,
  Building2,
  CalendarDays,
  ClipboardList,
  ExternalLink,
  FileText,
  GraduationCap,
  Library,
  LinkIcon,
  Loader2,
  MapPin,
  Megaphone,
  Newspaper,
  Search,
  School,
} from "lucide-react"

import { Label } from "@/components/ui/label"
import { SidebarInput } from "@/components/ui/sidebar"
import {
  searchChatbotDocuments,
  type ChatbotSearchResult,
} from "@/lib/chatbot"
import { cn } from "@/lib/utils"

const DOMAIN_LABELS: Record<string, string> = {
  academic: "Academics",
  assignments: "Assignments",
  course_materials: "Course Materials",
  library: "Library",
  public: "Public",
  venues: "Venues",
}

const ICONS = {
  "book-open": BookOpen,
  "building-2": Building2,
  "calendar-days": CalendarDays,
  "clipboard-list": ClipboardList,
  "external-link": ExternalLink,
  "file-text": FileText,
  "graduation-cap": GraduationCap,
  library: Library,
  "map-pin": MapPin,
  megaphone: Megaphone,
  newspaper: Newspaper,
  school: School,
}

function resultHref(result: ChatbotSearchResult) {
  const url = result.url?.trim()
  if (!url) return ""
  if (/^https?:\/\//i.test(url)) return url
  return url.startsWith("/") ? url : `/${url}`
}

function groupResults(results: ChatbotSearchResult[]) {
  return results.reduce<Record<string, ChatbotSearchResult[]>>((groups, result) => {
    const key = result.domain || "portal"
    groups[key] = [...(groups[key] ?? []), result]
    return groups
  }, {})
}

function SearchResultIcon({ result }: { result: ChatbotSearchResult }) {
  const Icon = ICONS[result.icon as keyof typeof ICONS] ?? FileText
  return (
    <span className="grid size-8 shrink-0 place-items-center rounded-md border border-border bg-background text-muted-foreground">
      <Icon className="size-4" />
    </span>
  )
}

type SearchFormProps = React.ComponentProps<"form">

export function SearchForm({ className, ...props }: SearchFormProps) {
  const router = useRouter()
  const [query, setQuery] = React.useState("")
  const [results, setResults] = React.useState<ChatbotSearchResult[]>([])
  const [isOpen, setIsOpen] = React.useState(false)
  const [isLoading, setIsLoading] = React.useState(false)
  const [error, setError] = React.useState("")
  const [activeIndex, setActiveIndex] = React.useState(-1)
  const inputRef = React.useRef<HTMLInputElement | null>(null)
  const rootRef = React.useRef<HTMLFormElement | null>(null)
  const trimmedQuery = query.trim()
  const canSearch = trimmedQuery.length >= 2
  const groupedResults = React.useMemo(() => groupResults(results), [results])

  const navigateToResult = React.useCallback(
    (result: ChatbotSearchResult) => {
      const href = resultHref(result)
      if (!href) return
      setIsOpen(false)
      setQuery("")
      setResults([])
      if (/^https?:\/\//i.test(href)) {
        window.location.assign(href)
      } else {
        router.push(href)
      }
    },
    [router]
  )

  React.useEffect(() => {
    const onShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        setIsOpen(true)
        inputRef.current?.focus()
      }
    }

    window.addEventListener("keydown", onShortcut)
    return () => window.removeEventListener("keydown", onShortcut)
  }, [])

  React.useEffect(() => {
    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    window.addEventListener("pointerdown", onPointerDown)
    return () => window.removeEventListener("pointerdown", onPointerDown)
  }, [])

  React.useEffect(() => {
    if (!canSearch) {
      return
    }

    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setIsLoading(true)
      setError("")
      searchChatbotDocuments(
        { query: trimmedQuery, mode: "topbar", limit: 8 },
        { signal: controller.signal }
      )
        .then((payload) => {
          setResults(payload.results)
          setActiveIndex(payload.results.length > 0 ? 0 : -1)
          setIsOpen(true)
        })
        .catch((searchError) => {
          if (controller.signal.aborted) return
          setResults([])
          setActiveIndex(-1)
          setError(
            searchError instanceof Error
              ? searchError.message
              : "Search is unavailable right now."
          )
          setIsOpen(true)
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setIsLoading(false)
          }
        })
    }, 300)

    return () => {
      controller.abort()
      window.clearTimeout(timer)
    }
  }, [canSearch, trimmedQuery])

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Escape") {
      event.preventDefault()
      setIsOpen(false)
      setActiveIndex(-1)
      return
    }

    if (event.key === "ArrowDown") {
      event.preventDefault()
      setIsOpen(true)
      setActiveIndex((current) =>
        results.length === 0 ? -1 : Math.min(current + 1, results.length - 1)
      )
      return
    }

    if (event.key === "ArrowUp") {
      event.preventDefault()
      setIsOpen(true)
      setActiveIndex((current) =>
        results.length === 0 ? -1 : Math.max(current - 1, 0)
      )
      return
    }

    if (event.key === "Enter") {
      event.preventDefault()
      const activeResult = results[activeIndex]
      if (activeResult) {
        navigateToResult(activeResult)
      }
    }
  }

  return (
    <form
      ref={rootRef}
      className={cn("relative w-full min-w-0 sm:w-72", className)}
      onSubmit={(event) => event.preventDefault()}
      {...props}
    >
      <div className="relative">
        <Label htmlFor="global-search" className="sr-only">
          Search
        </Label>
        <SidebarInput
          ref={inputRef}
          id="global-search"
          value={query}
          onChange={(event) => {
            const value = event.target.value
            setQuery(value)
            if (value.trim().length < 2) {
              setResults([])
              setIsLoading(false)
              setError("")
              setActiveIndex(-1)
            }
            setIsOpen(true)
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Search portal..."
          className="h-9 min-w-0 pl-8 pr-8"
          autoComplete="off"
          role="combobox"
          aria-expanded={isOpen}
          aria-controls="global-search-results"
        />
        <Search className="pointer-events-none absolute left-2 top-1/2 size-4 -translate-y-1/2 opacity-50" />
        {isLoading ? (
          <Loader2 className="pointer-events-none absolute right-2 top-1/2 size-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        ) : null}
      </div>

      {isOpen ? (
        <div
          id="global-search-results"
          className="absolute left-0 top-[calc(100%+0.5rem)] z-50 w-[min(34rem,calc(100vw-2rem))] overflow-hidden rounded-lg border border-border bg-popover text-popover-foreground shadow-xl sm:left-auto sm:right-0"
        >
          {!canSearch ? (
            <div className="px-3 py-3 text-sm text-muted-foreground">
              Type at least 2 characters.
            </div>
          ) : error ? (
            <div className="flex items-start gap-2 px-3 py-3 text-sm text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <span>{error}</span>
            </div>
          ) : isLoading && results.length === 0 ? (
            <div className="flex items-center gap-2 px-3 py-3 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              <span>Searching</span>
            </div>
          ) : results.length === 0 ? (
            <div className="px-3 py-3 text-sm text-muted-foreground">
              No approved results found.
            </div>
          ) : (
            <div className="max-h-[min(28rem,70vh)] overflow-y-auto py-2">
              {Object.entries(groupedResults).map(([domain, items]) => (
                <div key={domain} className="py-1">
                  <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-normal text-muted-foreground">
                    {DOMAIN_LABELS[domain] ?? domain}
                  </div>
                  {items.map((result) => {
                    const globalIndex = results.indexOf(result)
                    const href = resultHref(result)
                    const isExternal = /^https?:\/\//i.test(href)
                    return (
                      <button
                        key={`${result.domain}-${result.type}-${result.title}-${href}`}
                        type="button"
                        className={cn(
                          "flex w-full min-w-0 items-start gap-3 px-3 py-2 text-left transition",
                          globalIndex === activeIndex
                            ? "bg-muted text-foreground"
                            : "hover:bg-muted/70"
                        )}
                        onMouseEnter={() => setActiveIndex(globalIndex)}
                        onClick={() => navigateToResult(result)}
                      >
                        <SearchResultIcon result={result} />
                        <span className="min-w-0 flex-1">
                          <span className="flex min-w-0 items-center gap-1.5">
                            <span className="truncate text-sm font-medium">
                              {result.title}
                            </span>
                            {isExternal ? (
                              <ExternalLink className="size-3.5 shrink-0 text-muted-foreground" />
                            ) : null}
                          </span>
                          <span className="mt-0.5 line-clamp-2 block text-xs leading-5 text-muted-foreground">
                            {result.summary}
                          </span>
                          {result.breadcrumbs.length > 0 ? (
                            <span className="mt-1 flex min-w-0 items-center gap-1 text-[11px] text-muted-foreground">
                              <LinkIcon className="size-3 shrink-0" />
                              <span className="truncate">
                                {result.breadcrumbs.join(" / ")}
                              </span>
                            </span>
                          ) : null}
                        </span>
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </form>
  )
}
