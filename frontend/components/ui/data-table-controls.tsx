"use client"

import type { ReactNode } from "react"
import { Search, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

type SelectOption = {
  value: string
  label: string
}

type SelectFilter = {
  id: string
  label: string
  value: string
  options: SelectOption[]
  allLabel?: string
  onChange: (value: string) => void
}

type DataTableToolbarProps = {
  title: string
  description: string
  search: {
    id: string
    value: string
    placeholder: string
    onChange: (value: string) => void
  }
  filters: SelectFilter[]
  sort?: SelectFilter
  hasFilters?: boolean
  onClear?: () => void
  gridClassName?: string
  children: ReactNode
}

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"

function SelectControl({ filter }: { filter: SelectFilter }) {
  return (
    <div className="space-y-2">
      <Label htmlFor={filter.id}>{filter.label}</Label>
      <select
        id={filter.id}
        className={selectClass}
        value={filter.value}
        onChange={(event) => filter.onChange(event.target.value)}
      >
        {filter.allLabel ? <option value="">{filter.allLabel}</option> : null}
        {filter.options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export function DataTableToolbar({
  title,
  description,
  search,
  filters,
  sort,
  hasFilters = false,
  onClear,
  gridClassName = "md:grid-cols-2 xl:grid-cols-8",
  children,
}: DataTableToolbarProps) {
  return (
    <>
      <CardHeader>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          {hasFilters && onClear ? (
            <Button variant="outline" size="sm" onClick={onClear}>
              <X className="size-4" />
              Clear Filters
            </Button>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className={`grid gap-3 ${gridClassName}`}>
          <div className="space-y-2 md:col-span-2 xl:col-span-2">
            <Label htmlFor={search.id}>Search</Label>
            <div className="relative">
              <Search className="pointer-events-none absolute top-2.5 left-3 size-4 text-muted-foreground" />
              <Input
                id={search.id}
                className="pl-9"
                value={search.value}
                onChange={(event) => search.onChange(event.target.value)}
                placeholder={search.placeholder}
              />
            </div>
          </div>
          {filters.map((filter) => (
            <SelectControl key={filter.id} filter={filter} />
          ))}
          {sort ? <SelectControl filter={sort} /> : null}
        </div>
        {children}
      </CardContent>
    </>
  )
}
