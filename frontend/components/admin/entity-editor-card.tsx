"use client"

import type { FormEvent, ReactNode } from "react"
import { Loader2, Plus, Save, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

type EntityEditorCardProps = {
  title: string
  description: string
  isEditing: boolean
  isSaving: boolean
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onCancel: () => void
  children: ReactNode
}

export function EntityEditorCard({
  title,
  description,
  isEditing,
  isSaving,
  onSubmit,
  onCancel,
  children,
}: EntityEditorCardProps) {
  return (
    <Card className="h-fit border-border/70 bg-card/95 shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Plus className="size-5 text-primary" />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <form onSubmit={onSubmit}>
        <CardContent className="space-y-4">{children}</CardContent>
        <div className="flex justify-between gap-3 border-t p-4">
          {isEditing ? (
            <Button type="button" variant="outline" onClick={onCancel}>
              <X className="size-4" />
              Cancel
            </Button>
          ) : (
            <span />
          )}
          <Button type="submit" disabled={isSaving}>
            {isSaving ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Save className="size-4" />
            )}
            {isSaving ? "Saving..." : isEditing ? "Save" : "Add"}
          </Button>
        </div>
      </form>
    </Card>
  )
}
