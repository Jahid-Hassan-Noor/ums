"use client"

import { Plus, Search } from "lucide-react"
import type { ReactNode } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

type ManagePageHeaderProps = {
  title: string
  description?: string
  search?: string
  onSearch?: (value: string) => void
  searchPlaceholder?: string
  createLabel?: string
  onCreate?: () => void
  actions?: ReactNode
}

export function ManagePageHeader({
  title,
  description,
  search,
  onSearch,
  searchPlaceholder = "Search records",
  createLabel = "Create",
  onCreate,
  actions,
}: ManagePageHeaderProps) {
  return (
    <div className="flex flex-col gap-3 border-b border-border/70 pb-4 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {description ? (
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            {description}
          </p>
        ) : null}
      </div>
      <div className="flex w-full flex-col gap-2 sm:flex-row md:w-auto">
        {onSearch ? (
          <label className="relative min-w-0 sm:w-72">
            <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-8"
              placeholder={searchPlaceholder}
              value={search ?? ""}
              onChange={(event) => onSearch(event.target.value)}
            />
          </label>
        ) : null}
        {onCreate ? (
          <Button onClick={onCreate}>
            <Plus className="size-4" />
            {createLabel}
          </Button>
        ) : null}
        {actions}
      </div>
    </div>
  )
}
