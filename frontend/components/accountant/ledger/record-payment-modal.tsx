"use client"

import { useState } from "react"
import { CreditCard, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

type RecordPaymentModalProps = {
  studentId: number
  studentName: string
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

export function RecordPaymentModal({ studentId, studentName, open, onClose, onSuccess }: RecordPaymentModalProps) {
  const [amount, setAmount] = useState("")
  const [description, setDescription] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  if (!open) return null

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError("")
    try {
      await apiFetch("/finance/student-ledgers", {
        method: "POST",
        body: JSON.stringify({
          student_id: studentId,
          amount: Number(amount),
          description: description || "Manual payment recorded",
          entry_type: "payment",
        }),
      })
      setAmount("")
      setDescription("")
      onSuccess()
      onClose()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to record payment.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-md mx-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="size-4" /> Record Payment — {studentName}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error ? <p className="mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="pay_amount">Amount (RM)</Label>
              <Input
                id="pay_amount"
                type="number"
                min="0.01"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="pay_description">Description</Label>
              <Input
                id="pay_description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Cash payment at office"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
              <Button type="submit" disabled={saving}>
                {saving ? <Loader2 className="size-4 animate-spin" /> : <CreditCard className="size-4" />}
                Record Payment
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
