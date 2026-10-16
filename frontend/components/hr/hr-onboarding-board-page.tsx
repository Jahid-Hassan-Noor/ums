"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { ArrowRight, CheckCircle2, GripVertical, History, Link2, Loader2, Plus, RefreshCw } from "lucide-react"

import { Header } from "@/components/layout/header"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { formatDateOnly } from "@/components/utils/format"
import { usePublicUmsSettings } from "@/hooks/use-public-ums-settings"
import { apiFetch, apiRequest } from "@/lib/auth"
import { readJsonResponse } from "@/lib/fetch-utils"

type Phase = "applicant" | "onboarding"
type BoardColumn = { id: number; label: string; phase: Phase; position: number; is_active: boolean; count?: number }
type BoardCard = {
  id: number
  name: string
  email: string
  kind: Phase
  column_id: number
  position: { id: number; title: string } | null
  employee_id: number | null
  has_employee_link: boolean
  notes: string
  updated_at: string
  last_moved_at: string | null
}
type BoardResponse = { columns: BoardColumn[]; archived_columns: BoardColumn[]; cards: BoardCard[]; can_manage: boolean }
type PositionOption = { id: number; title: string; code: string; is_active: boolean }
type EmployeeOption = {
  id: number
  name: string
  employee_no: string
  email: string
  work_email: string
  position: { title: string } | null
}
type BoardChange = {
  id: number
  from_column_id: number | null
  from_label: string
  from_phase: Phase | ""
  to_column_id: number
  to_label: string
  to_phase: Phase
  actor_name: string
  reason: string
  created_at: string
}
type EmployeeLinkHistory = {
  employee_id: number | null
  employee_no: string
  employee_name: string
  actor_name: string
  created_at: string
}

const emptyCardForm = { name: "", email: "", position_id: "", notes: "", column_id: "" }
const emptyColumnForm = { label: "", phase: "applicant" as Phase }

export function HrOnboardingBoardPage() {
  const settings = usePublicUmsSettings()
  const [board, setBoard] = useState<BoardResponse | null>(null)
  const [positions, setPositions] = useState<PositionOption[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [showCardForm, setShowCardForm] = useState(false)
  const [cardForm, setCardForm] = useState(emptyCardForm)
  const [showColumnForm, setShowColumnForm] = useState(false)
  const [columnForm, setColumnForm] = useState(emptyColumnForm)
  const [editingColumnId, setEditingColumnId] = useState<number | null>(null)
  const [columnDraft, setColumnDraft] = useState({ label: "", position: 0 })
  const [archiveColumn, setArchiveColumn] = useState<BoardColumn | null>(null)
  const [draggedCardId, setDraggedCardId] = useState<number | null>(null)
  const [pendingMove, setPendingMove] = useState<{ card: BoardCard; column: BoardColumn } | null>(null)
  const [moveReason, setMoveReason] = useState("")
  const [moveError, setMoveError] = useState("")
  const [historyCard, setHistoryCard] = useState<BoardCard | null>(null)
  const [history, setHistory] = useState<BoardChange[]>([])
  const [historyLink, setHistoryLink] = useState<EmployeeLinkHistory | null>(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState("")
  const historyRequestId = useRef(0)
  const [linkCard, setLinkCard] = useState<BoardCard | null>(null)
  const [employeeQuery, setEmployeeQuery] = useState("")
  const [employeeOptions, setEmployeeOptions] = useState<EmployeeOption[]>([])
  const [selectedEmployeeId, setSelectedEmployeeId] = useState("")
  const [employeeSearchLoading, setEmployeeSearchLoading] = useState(false)
  const [employeeSearchFinished, setEmployeeSearchFinished] = useState(false)
  const [employeeSearchError, setEmployeeSearchError] = useState("")
  const [linkError, setLinkError] = useState("")
  const employeeSearchRequestId = useRef(0)

  const columns = useMemo(
    () => [...(board?.columns ?? [])].sort((a, b) =>
      a.phase.localeCompare(b.phase) || a.position - b.position || a.id - b.id
    ),
    [board]
  )
  const cardsByColumn = useMemo(() => {
    const grouped = new Map<number, BoardCard[]>()
    columns.forEach((column) => grouped.set(column.id, []))
    board?.cards.forEach((card) => grouped.get(card.column_id)?.push(card))
    return grouped
  }, [board, columns])

  const loadBoard = useCallback(async () => {
    const response = await apiFetch<BoardResponse>("/hr/onboarding-board")
    setBoard(response)
  }, [])

  const refresh = useCallback(() => {
    setLoading(true)
    setError("")
    void loadBoard()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load the onboarding board."))
      .finally(() => setLoading(false))
  }, [loadBoard])

  useEffect(() => {
    const timer = window.setTimeout(refresh, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  function startCardForm() {
    const firstApplicantColumn = columns.find((column) => column.phase === "applicant") ?? columns[0]
    setCardForm({ ...emptyCardForm, column_id: firstApplicantColumn ? String(firstApplicantColumn.id) : "" })
    setShowCardForm(true)
    void apiFetch<{ positions: PositionOption[] }>("/hr/positions")
      .then((response) => setPositions((response.positions ?? []).filter((position) => position.is_active)))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load positions."))
  }

  async function createCard(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!cardForm.name.trim() || !cardForm.column_id) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/hr/onboarding-board/cards", {
        method: "POST",
        body: JSON.stringify({
          name: cardForm.name.trim(),
          email: cardForm.email.trim(),
          position_id: cardForm.position_id ? Number(cardForm.position_id) : null,
          notes: cardForm.notes.trim(),
          column_id: Number(cardForm.column_id),
        }),
      })
      await loadBoard()
      setShowCardForm(false)
      setCardForm(emptyCardForm)
      setSuccess("Staff card created.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create staff card.")
    } finally {
      setSaving(false)
    }
  }

  async function createColumn(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!columnForm.label.trim()) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch("/hr/onboarding-board/columns", {
        method: "POST",
        body: JSON.stringify({ label: columnForm.label.trim(), phase: columnForm.phase }),
      })
      await loadBoard()
      setShowColumnForm(false)
      setColumnForm(emptyColumnForm)
      setSuccess("Column added.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to add column.")
    } finally {
      setSaving(false)
    }
  }

  async function updateColumn(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (editingColumnId === null || !columnDraft.label.trim()) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/hr/onboarding-board/columns/${editingColumnId}`, {
        method: "PATCH",
        body: JSON.stringify({ label: columnDraft.label.trim(), position: columnDraft.position }),
      })
      await loadBoard()
      setEditingColumnId(null)
      setSuccess("Column updated.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update column.")
    } finally {
      setSaving(false)
    }
  }

  async function disableColumn() {
    if (!archiveColumn) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/hr/onboarding-board/columns/${archiveColumn.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: false }),
      })
      await loadBoard()
      setEditingColumnId(null)
      setArchiveColumn(null)
      setSuccess("Empty column archived.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to archive column.")
      setArchiveColumn(null)
    } finally {
      setSaving(false)
    }
  }

  async function restoreColumn(column: BoardColumn) {
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      await apiFetch(`/hr/onboarding-board/columns/${column.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: true }),
      })
      await loadBoard()
      setSuccess(`${column.label} restored.`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to restore column.")
    } finally {
      setSaving(false)
    }
  }

  function proposeMove(card: BoardCard, column: BoardColumn) {
    if (!board?.can_manage || saving || card.column_id === column.id) return
    setPendingMove({ card, column })
    setMoveReason("")
    setMoveError("")
  }

  async function confirmMove() {
    if (!pendingMove) return
    setSaving(true)
    setMoveError("")
    setError("")
    setSuccess("")
    const { card, column } = pendingMove
    try {
      const response = await apiRequest(`/hr/onboarding-board/cards/${card.id}/move`, {
        method: "POST",
        body: JSON.stringify({
          column_id: column.id,
          expected_column_id: card.column_id,
          reason: moveReason.trim(),
        }),
      })
      const stale = response.status === 409
      try {
        await readJsonResponse<{ card: BoardCard }>(response, "Unable to move the staff card.")
      } catch (caught) {
        if (stale) {
          await loadBoard()
          setPendingMove(null)
          setError("This card changed since you opened the board. The board has been refreshed; choose a destination again.")
          return
        }
        throw caught
      }
      await loadBoard()
      setPendingMove(null)
      setSuccess(`${card.name} moved to ${column.label}.`)
    } catch (caught) {
      setMoveError(caught instanceof Error ? caught.message : "Unable to move the staff card.")
    } finally {
      setSaving(false)
    }
  }

  function showHistory(card: BoardCard) {
    const requestId = ++historyRequestId.current
    setHistoryCard(card)
    setHistory([])
    setHistoryLink(null)
    setHistoryError("")
    setHistoryLoading(true)
    void apiFetch<{ changes: BoardChange[]; employee_link: EmployeeLinkHistory | null }>(`/hr/onboarding-board/cards/${card.id}/history`)
      .then((response) => {
        if (requestId === historyRequestId.current) {
          setHistory(response.changes ?? [])
          setHistoryLink(response.employee_link ?? null)
        }
      })
      .catch((caught) => {
        if (requestId === historyRequestId.current) {
          setHistoryError(caught instanceof Error ? caught.message : "Unable to load card history.")
        }
      })
      .finally(() => {
        if (requestId === historyRequestId.current) setHistoryLoading(false)
      })
  }

  function openEmployeeLink(card: BoardCard) {
    setLinkCard(card)
    setEmployeeQuery(card.email || card.name.split(" ")[0] || "")
    setEmployeeOptions([])
    setSelectedEmployeeId("")
    setEmployeeSearchLoading(false)
    setEmployeeSearchFinished(false)
    setEmployeeSearchError("")
    setLinkError("")
  }

  async function searchEmployees(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const query = employeeQuery.trim()
    if (!query) return
    const requestId = ++employeeSearchRequestId.current
    setEmployeeSearchLoading(true)
    setEmployeeSearchFinished(false)
    setEmployeeSearchError("")
    setSelectedEmployeeId("")
    try {
      const response = await apiFetch<{ employees: EmployeeOption[] }>(`/hr/employees?q=${encodeURIComponent(query)}`)
      if (requestId !== employeeSearchRequestId.current) return
      const linkedIds = new Set(board?.cards.map((card) => card.employee_id).filter((id) => id !== null))
      setEmployeeOptions((response.employees ?? []).filter((employee) => !linkedIds.has(employee.id)))
    } catch (caught) {
      if (requestId === employeeSearchRequestId.current) {
        setEmployeeSearchError(caught instanceof Error ? caught.message : "Unable to search employee records.")
      }
    } finally {
      if (requestId === employeeSearchRequestId.current) {
        setEmployeeSearchLoading(false)
        setEmployeeSearchFinished(true)
      }
    }
  }

  async function confirmEmployeeLink() {
    if (!linkCard || !selectedEmployeeId) return
    setSaving(true)
    setLinkError("")
    setError("")
    setSuccess("")
    try {
      const response = await apiRequest(`/hr/onboarding-board/cards/${linkCard.id}/employee-link`, {
        method: "POST",
        body: JSON.stringify({
          employee_id: Number(selectedEmployeeId),
          expected_column_id: linkCard.column_id,
        }),
      })
      const conflict = response.status === 409
      try {
        await readJsonResponse<{ card: BoardCard }>(response, "Unable to link this employee.")
      } catch (caught) {
        if (conflict) {
          await loadBoard()
          setLinkCard(null)
          setError("The card or employee changed. The board has been refreshed; search and confirm again.")
          return
        }
        throw caught
      }
      const employee = employeeOptions.find((option) => option.id === Number(selectedEmployeeId))
      await loadBoard()
      setLinkCard(null)
      setSuccess(`${linkCard.name} linked to ${employee?.employee_no ?? "the employee record"}.`)
    } catch (caught) {
      setLinkError(caught instanceof Error ? caught.message : "Unable to link this employee.")
    } finally {
      setSaving(false)
    }
  }

  const selectedEmployee = employeeOptions.find((employee) => employee.id === Number(selectedEmployeeId))
  const phaseLabel = (phase: Phase) => phase === "applicant" ? settings.terminology.applicant_label : "Onboarding"
  const displayDate = (value: string | null) => value
    ? formatDateOnly(value, { locale: settings.localization.locale, formatOptions: { dateStyle: "medium" } })
    : "Not recorded"

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/hr", title: "HR" }, { href: "/hr/onboarding", title: "Staff Onboarding" }]} />
      <main className="min-w-0 flex-1 space-y-5 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Staff Onboarding</h1>
            <p className="mt-2 text-sm text-muted-foreground">Track staff applicants and onboarding progress through your configured stages.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {board?.can_manage ? (
              <>
                <Button variant="outline" onClick={() => { setShowColumnForm((current) => !current); setShowCardForm(false) }} disabled={saving}>
                  <Plus className="size-4" /> Add column
                </Button>
                <Button onClick={() => { startCardForm(); setShowColumnForm(false) }} disabled={saving || columns.length === 0}>
                  <Plus className="size-4" /> Add staff card
                </Button>
              </>
            ) : null}
            <Button variant="outline" onClick={refresh} disabled={loading || saving}>
              {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
            </Button>
          </div>
        </section>

        {error ? <p role="alert" className="rounded-lg border border-destructive/30 bg-background p-3 text-sm text-destructive">{error}</p> : null}
        {success ? <p role="status" className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {showCardForm && board?.can_manage ? (
          <form onSubmit={createCard} className="grid gap-3 rounded-lg border border-border bg-background p-4 shadow-sm sm:grid-cols-2 xl:grid-cols-3">
            <div className="space-y-1.5"><Label htmlFor="onboarding-card-name">Name</Label><Input id="onboarding-card-name" value={cardForm.name} onChange={(event) => setCardForm((current) => ({ ...current, name: event.target.value }))} required maxLength={160} /></div>
            <div className="space-y-1.5"><Label htmlFor="onboarding-card-email">Email</Label><Input id="onboarding-card-email" type="email" value={cardForm.email} onChange={(event) => setCardForm((current) => ({ ...current, email: event.target.value }))} maxLength={254} /></div>
            <div className="space-y-1.5"><Label htmlFor="onboarding-card-position">Position</Label><select id="onboarding-card-position" value={cardForm.position_id} onChange={(event) => setCardForm((current) => ({ ...current, position_id: event.target.value }))} className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"><option value="">No position yet</option>{positions.map((position) => <option key={position.id} value={position.id}>{position.title}{position.code ? ` (${position.code})` : ""}</option>)}</select></div>
            <div className="space-y-1.5"><Label htmlFor="onboarding-card-column">Starting column</Label><select id="onboarding-card-column" value={cardForm.column_id} onChange={(event) => setCardForm((current) => ({ ...current, column_id: event.target.value }))} className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm" required>{columns.map((column) => <option key={column.id} value={column.id}>{column.label}</option>)}</select></div>
            <div className="space-y-1.5 sm:col-span-2"><Label htmlFor="onboarding-card-notes">Notes</Label><Textarea id="onboarding-card-notes" value={cardForm.notes} onChange={(event) => setCardForm((current) => ({ ...current, notes: event.target.value }))} maxLength={5000} /></div>
            <div className="flex flex-wrap gap-2 sm:col-span-2 xl:col-span-3"><Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : null}Create card</Button><Button type="button" variant="outline" onClick={() => setShowCardForm(false)} disabled={saving}>Cancel</Button></div>
          </form>
        ) : null}

        {showColumnForm && board?.can_manage ? (
          <form onSubmit={createColumn} className="flex flex-wrap items-end gap-3 rounded-lg border border-border bg-background p-4 shadow-sm">
            <div className="min-w-48 flex-1 space-y-1.5"><Label htmlFor="onboarding-column-label">Column name</Label><Input id="onboarding-column-label" value={columnForm.label} onChange={(event) => setColumnForm((current) => ({ ...current, label: event.target.value }))} required maxLength={80} /></div>
            <div className="min-w-40 space-y-1.5"><Label htmlFor="onboarding-column-phase">Phase</Label><select id="onboarding-column-phase" value={columnForm.phase} onChange={(event) => setColumnForm((current) => ({ ...current, phase: event.target.value as Phase }))} className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"><option value="applicant">{phaseLabel("applicant")}</option><option value="onboarding">Onboarding</option></select></div>
            <Button type="submit" disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : null}Add column</Button>
            <Button type="button" variant="outline" onClick={() => setShowColumnForm(false)} disabled={saving}>Cancel</Button>
          </form>
        ) : null}

        {loading && !board ? <p role="status" className="flex items-center gap-2 py-12 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" />Loading onboarding board</p> : null}
        {!loading && !board && !error ? <p className="rounded-lg border border-border bg-background p-6 text-sm text-muted-foreground">The onboarding board is unavailable.</p> : null}
        {board && columns.length === 0 ? <p className="rounded-lg border border-border bg-background p-6 text-sm text-muted-foreground">No active columns yet. Add a column to start tracking staff onboarding.</p> : null}

        {board && columns.length > 0 ? (
          <section aria-label="Staff onboarding board" className="flex snap-x snap-mandatory gap-4 overflow-x-auto pb-4">
            {columns.map((column) => {
              const cards = cardsByColumn.get(column.id) ?? []
              return (
                <div key={column.id} className="w-[min(85vw,21rem)] shrink-0 snap-start rounded-xl border border-border bg-muted/40 p-3 sm:w-80"
                  onDragOver={(event) => { if (draggedCardId !== null && board.can_manage) event.preventDefault() }}
                  onDrop={(event) => { event.preventDefault(); const card = board.cards.find((item) => item.id === draggedCardId); if (card) proposeMove(card, column); setDraggedCardId(null) }}>
                  <div className="mb-3 flex items-start justify-between gap-2">
                    <div className="min-w-0"><h2 className="break-words text-base font-semibold">{column.label}</h2><p className="mt-1 text-xs text-muted-foreground">{phaseLabel(column.phase)} · {cards.length} {cards.length === 1 ? "card" : "cards"}</p></div>
                    {board.can_manage ? <Button size="xs" variant="ghost" onClick={() => { setEditingColumnId(column.id); setColumnDraft({ label: column.label, position: column.position }) }} disabled={saving} aria-label={`Edit ${column.label} column`}>Edit</Button> : null}
                  </div>

                  {editingColumnId === column.id && board.can_manage ? (
                    <form onSubmit={updateColumn} className="mb-3 space-y-2 rounded-lg border border-border bg-background p-3">
                      <div className="space-y-1"><Label htmlFor={`column-label-${column.id}`}>Name</Label><Input id={`column-label-${column.id}`} value={columnDraft.label} onChange={(event) => setColumnDraft((current) => ({ ...current, label: event.target.value }))} required maxLength={80} /></div>
                      <div className="space-y-1"><Label htmlFor={`column-position-${column.id}`}>Order</Label><Input id={`column-position-${column.id}`} type="number" min={0} value={columnDraft.position} onChange={(event) => setColumnDraft((current) => ({ ...current, position: Number(event.target.value) }))} required /></div>
                      <div className="flex flex-wrap gap-2"><Button size="sm" type="submit" disabled={saving}>Save</Button><Button size="sm" type="button" variant="outline" onClick={() => setEditingColumnId(null)} disabled={saving}>Cancel</Button><Button size="sm" type="button" variant="destructive" onClick={() => setArchiveColumn(column)} disabled={saving || cards.length > 0} title={cards.length ? "Move cards out before archiving" : "Archive this empty column"}>Archive</Button></div>
                    </form>
                  ) : null}

                  <div className="space-y-3">
                    {cards.length === 0 ? <p className="rounded-lg border border-dashed border-border bg-background/70 px-3 py-6 text-center text-sm text-muted-foreground">No cards in this column</p> : null}
                    {cards.map((card) => (
                      <Card key={card.id} draggable={board.can_manage && !saving} onDragStart={(event) => { event.dataTransfer.effectAllowed = "move"; setDraggedCardId(card.id) }} onDragEnd={() => setDraggedCardId(null)} className="gap-2 py-3 shadow-sm">
                        <CardHeader className="px-3"><div className="flex items-start justify-between gap-2"><CardTitle className="min-w-0 break-words text-sm">{card.name}</CardTitle>{board.can_manage ? <GripVertical className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" /> : null}</div></CardHeader>
                        <CardContent className="space-y-2 px-3 text-xs text-muted-foreground">
                          {card.position ? <p className="break-words">{card.position.title}</p> : null}
                          {card.email ? <p className="break-all">{card.email}</p> : null}
                          {card.notes ? <p className="line-clamp-2 break-words">{card.notes}</p> : null}
                          <div className="flex flex-wrap items-center gap-2"><Badge variant="outline">{phaseLabel(card.kind)}</Badge>{card.has_employee_link ? <Badge variant="secondary">Employee link recorded</Badge> : null}</div>
                          <p>Updated {displayDate(card.updated_at)}</p>
                          <div className="flex flex-wrap items-center gap-2 pt-1">
                            {board.can_manage ? <select aria-label={`Move ${card.name} to column`} value={column.id} onChange={(event) => { const target = columns.find((item) => item.id === Number(event.target.value)); if (target) proposeMove(card, target) }} disabled={saving} className="h-8 min-w-0 max-w-full flex-1 rounded-lg border border-input bg-background px-2 text-xs text-foreground"><option value={column.id}>Move to…</option>{columns.filter((target) => target.id !== column.id).map((target) => <option key={target.id} value={target.id}>{target.label}</option>)}</select> : null}
                            {board.can_manage && card.kind === "onboarding" && !card.has_employee_link ? <Button size="xs" variant="outline" onClick={() => openEmployeeLink(card)} disabled={saving}><Link2 className="size-3" /> Link employee</Button> : null}
                            <Button size="xs" variant="outline" onClick={() => showHistory(card)}><History className="size-3" /> History</Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )
            })}
          </section>
        ) : null}
        {board?.can_manage && board.archived_columns.length > 0 ? (
          <section aria-label="Archived onboarding columns" className="rounded-lg border border-border bg-background p-4">
            <h2 className="text-sm font-semibold">Archived columns</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {board.archived_columns.map((column) => (
                <div key={column.id} className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm">
                  <span className="break-words">{column.label}</span>
                  <Button size="xs" variant="outline" onClick={() => void restoreColumn(column)} disabled={saving}>
                    Restore
                  </Button>
                </div>
              ))}
            </div>
          </section>
        ) : null}
      </main>

      <AlertDialog open={pendingMove !== null} onOpenChange={(open) => { if (!open && !saving) setPendingMove(null) }}>
        <AlertDialogContent>
          <AlertDialogHeader><AlertDialogTitle>Move staff card?</AlertDialogTitle><AlertDialogDescription>{pendingMove ? `${pendingMove.card.name} will move to ${pendingMove.column.label}. The change will be recorded in the card history.` : ""}</AlertDialogDescription></AlertDialogHeader>
          <div className="space-y-1.5"><Label htmlFor="onboarding-move-reason">Reason (optional)</Label><Textarea id="onboarding-move-reason" value={moveReason} onChange={(event) => setMoveReason(event.target.value)} maxLength={1000} /></div>
          {moveError ? <p role="alert" className="text-sm text-destructive">{moveError}</p> : null}
          <AlertDialogFooter><AlertDialogCancel disabled={saving}>Cancel</AlertDialogCancel><AlertDialogAction onClick={(event) => { event.preventDefault(); void confirmMove() }} disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <ArrowRight className="size-4" />}Move card</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={archiveColumn !== null} onOpenChange={(open) => { if (!open && !saving) setArchiveColumn(null) }}>
        <AlertDialogContent><AlertDialogHeader><AlertDialogTitle>Archive empty column?</AlertDialogTitle><AlertDialogDescription>{archiveColumn?.label} will be hidden from the board. Columns with cards must be emptied first.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel disabled={saving}>Cancel</AlertDialogCancel><AlertDialogAction variant="destructive" onClick={(event) => { event.preventDefault(); void disableColumn() }} disabled={saving}>Archive column</AlertDialogAction></AlertDialogFooter></AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={linkCard !== null} onOpenChange={(open) => { if (!open && !saving) { employeeSearchRequestId.current += 1; setLinkCard(null) } }}>
        <AlertDialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
          <AlertDialogHeader>
            <AlertDialogTitle>Link employee record</AlertDialogTitle>
            <AlertDialogDescription>
              Select the employee record for {linkCard?.name}. The link and the HR staff member who confirms it will appear in this card&apos;s history. Links cannot be changed from this board.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <form onSubmit={searchEmployees} className="flex flex-wrap items-end gap-2">
            <div className="min-w-48 flex-1 space-y-1.5">
              <Label htmlFor="onboarding-employee-search">Name, email, or employee number</Label>
              <Input id="onboarding-employee-search" value={employeeQuery} onChange={(event) => { employeeSearchRequestId.current += 1; setEmployeeQuery(event.target.value); setEmployeeOptions([]); setSelectedEmployeeId(""); setEmployeeSearchLoading(false); setEmployeeSearchFinished(false); setEmployeeSearchError("") }} required />
            </div>
            <Button type="submit" variant="outline" disabled={employeeSearchLoading || saving}>
              {employeeSearchLoading ? <Loader2 className="size-4 animate-spin" /> : null} Search
            </Button>
          </form>
          {employeeSearchError ? <p role="alert" className="text-sm text-destructive">{employeeSearchError}</p> : null}
          {employeeSearchFinished && !employeeSearchError && employeeOptions.length === 0 ? <p className="text-sm text-muted-foreground">No unlinked employee records matched. Try a more specific name or employee number.</p> : null}
          {employeeOptions.length > 0 ? (
            <div className="space-y-1.5">
              <Label htmlFor="onboarding-employee-select">Employee record</Label>
              <select id="onboarding-employee-select" value={selectedEmployeeId} onChange={(event) => setSelectedEmployeeId(event.target.value)} className="h-9 w-full rounded-lg border border-input bg-background px-2.5 text-sm">
                <option value="">Select employee</option>
                {employeeOptions.map((employee) => <option key={employee.id} value={employee.id}>{employee.name} · {employee.employee_no}</option>)}
              </select>
            </div>
          ) : null}
          {selectedEmployee ? (
            <div className="rounded-lg border border-border bg-muted/40 p-3 text-sm">
              <p className="font-medium">{selectedEmployee.name} · {selectedEmployee.employee_no}</p>
              <p className="mt-1 break-all text-muted-foreground">{selectedEmployee.email || selectedEmployee.work_email || "No email recorded"}</p>
              {selectedEmployee.position ? <p className="mt-1 text-muted-foreground">{selectedEmployee.position.title}</p> : null}
            </div>
          ) : null}
          <p className="text-xs text-muted-foreground">Need to create an employee record first? Use the existing <Link href="/hr/employees" className="font-medium text-primary underline underline-offset-2">Employees page</Link>, then return to this card.</p>
          {linkError ? <p role="alert" className="text-sm text-destructive">{linkError}</p> : null}
          <AlertDialogFooter>
            <AlertDialogCancel disabled={saving}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={(event) => { event.preventDefault(); void confirmEmployeeLink() }} disabled={saving || !selectedEmployeeId}>
              {saving ? <Loader2 className="size-4 animate-spin" /> : <Link2 className="size-4" />} Confirm link
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={historyCard !== null} onOpenChange={(open) => { if (!open) { historyRequestId.current += 1; setHistoryCard(null) } }}>
        <AlertDialogContent className="max-h-[80vh] overflow-y-auto sm:max-w-lg">
          <AlertDialogHeader><AlertDialogTitle>{historyCard?.name} history</AlertDialogTitle><AlertDialogDescription>Recorded stage changes and employee link for this staff card.</AlertDialogDescription></AlertDialogHeader>
          {historyLoading ? <p role="status" className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" />Loading history</p> : null}
          {historyError ? <p role="alert" className="text-sm text-destructive">{historyError}</p> : null}
          {!historyLoading && !historyError && history.length === 0 && !historyLink ? <p className="text-sm text-muted-foreground">No changes recorded.</p> : null}
          {historyLink ? <div className="rounded-lg border border-border p-3 text-sm"><p className="font-medium">Linked to {historyLink.employee_name} · {historyLink.employee_no}</p><p className="mt-1 text-xs text-muted-foreground">By {historyLink.actor_name || "HR"} · {displayDate(historyLink.created_at)}</p></div> : null}
          <ol className="space-y-3">{history.map((change) => <li key={change.id} className="rounded-lg border border-border p-3 text-sm"><p className="font-medium">{change.from_column_id ? `${change.from_label} → ${change.to_label}` : `Created in ${change.to_label}`}</p><p className="mt-1 text-xs text-muted-foreground">{change.actor_name} · {displayDate(change.created_at)}</p>{change.reason ? <p className="mt-2 break-words text-xs">{change.reason}</p> : null}</li>)}</ol>
          <AlertDialogFooter><AlertDialogCancel>Close</AlertDialogCancel></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
