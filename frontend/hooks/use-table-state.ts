"use client"

import { useCallback, useMemo, useState } from "react"

export type SortDirection = "asc" | "desc"

type SortState = {
  field: string
  direction: SortDirection
}

type UseTableStateOptions<TFilters extends Record<string, unknown>> = {
  initialFilters: TFilters
  initialSearch?: string
  initialPage?: number
  initialPageSize?: number
  initialSort?: SortState
}

export function useTableState<TFilters extends Record<string, unknown>>({
  initialFilters,
  initialSearch = "",
  initialPage = 1,
  initialPageSize = 10,
  initialSort,
}: UseTableStateOptions<TFilters>) {
  const [search, setSearchValue] = useState(initialSearch)
  const [filters, setFilters] = useState<TFilters>(initialFilters)
  const [page, setPage] = useState(initialPage)
  const [pageSize, setPageSizeValue] = useState(initialPageSize)
  const [sort, setSortState] = useState<SortState | null>(initialSort ?? null)

  const resetPage = useCallback(() => setPage(1), [])

  const setSearch = useCallback(
    (value: string) => {
      setSearchValue(value)
      resetPage()
    },
    [resetPage]
  )

  const updateFilter = useCallback(
    <K extends keyof TFilters>(key: K, value: TFilters[K]) => {
      setFilters((current) => ({ ...current, [key]: value }))
      resetPage()
    },
    [resetPage]
  )

  const resetFilters = useCallback(() => {
    setFilters(initialFilters)
    resetPage()
  }, [initialFilters, resetPage])

  const setSort = useCallback(
    (field: string, direction?: SortDirection) => {
      setSortState((current) => ({
        field,
        direction:
          direction ??
          (current?.field === field && current.direction === "asc"
            ? "desc"
            : "asc"),
      }))
      resetPage()
    },
    [resetPage]
  )

  const setPageSize = useCallback(
    (value: number) => {
      setPageSizeValue(value)
      resetPage()
    },
    [resetPage]
  )

  const query = useMemo(
    () => ({
      search,
      filters,
      page,
      pageSize,
      sortField: sort?.field ?? "",
      sortDirection: sort?.direction ?? "asc",
    }),
    [filters, page, pageSize, search, sort]
  )

  return {
    search,
    setSearch,
    filters,
    setFilters,
    updateFilter,
    resetFilters,
    page,
    setPage,
    pageSize,
    setPageSize,
    sort,
    setSort,
    query,
  }
}
