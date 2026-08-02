"use client"

import { useCallback, useEffect, useState } from "react"

import { apiFetch } from "@/lib/auth"

type StaffRecord = {
  id: number
  name: string
}

type UseManageStaffOptions<TRecord extends StaffRecord> = {
  endpoint: string
  responseKey: string
  loadErrorMessage: string
  saveErrorMessage: string
  payload: (record: TRecord) => Record<string, unknown>
  successMessage?: (record: TRecord) => string
}

export function useManageStaff<TRecord extends StaffRecord>({
  endpoint,
  responseKey,
  loadErrorMessage,
  saveErrorMessage,
  payload,
  successMessage = (record) => `${record.name} updated successfully.`,
}: UseManageStaffOptions<TRecord>) {
  const [rows, setRows] = useState<TRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<number | null>(null)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const data = await apiFetch<Record<string, TRecord[]>>(endpoint)
    setRows(data[responseKey] ?? [])
  }, [endpoint, responseKey])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadData()
        .catch((caught) =>
          setError(caught instanceof Error ? caught.message : loadErrorMessage)
        )
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadData, loadErrorMessage])

  const update = useCallback(
    <K extends keyof TRecord>(id: number, field: K, value: TRecord[K]) => {
      setRows((current) =>
        current.map((row) => (row.id === id ? { ...row, [field]: value } : row))
      )
    },
    []
  )

  const save = useCallback(
    async (record: TRecord) => {
      setSaving(record.id)
      setError("")
      setSuccess("")
      try {
        await apiFetch(`${endpoint}?profile_id=${record.id}`, {
          method: "PATCH",
          body: JSON.stringify(payload(record)),
        })
        setSuccess(successMessage(record))
        await loadData()
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : saveErrorMessage)
      } finally {
        setSaving(null)
      }
    },
    [endpoint, loadData, payload, saveErrorMessage, successMessage]
  )

  return {
    rows,
    loading,
    saving,
    error,
    success,
    loadData,
    update,
    save,
  }
}
