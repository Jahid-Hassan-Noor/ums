"use client"

import { CheckCircle2, Loader2, RefreshCw, Save } from "lucide-react"

import { Header } from "@/components/layout/header"
import { ManagePageHeader } from "@/components/admin/manage-page-header"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useManageStaff } from "@/hooks/use-manage-staff"

type HrStaff = {
  id: number
  username: string
  name: string
  email: string
  staff_id: string
  designation: string
  phone: string
  office_location: string
  is_active: boolean
}

export function AdminManageHrPage() {
  const {
    rows: staff,
    loading,
    saving,
    error,
    success,
    loadData,
    update,
    save,
  } = useManageStaff<HrStaff>({
    endpoint: "/admin/manage/hr",
    responseKey: "hr_staff",
    loadErrorMessage: "Unable to load HR accounts.",
    saveErrorMessage: "Unable to update HR account.",
    payload: (row) => ({
      staff_id: row.staff_id,
      designation: row.designation,
      phone: row.phone,
      office_location: row.office_location,
      is_active: row.is_active,
    }),
  })

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/manage", title: "Manage" },
          { href: "/admin/manage/hr", title: "HR" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <ManagePageHeader
          title="Manage HR"
          description="Maintain human resources accounts that manage university employee records."
          actions={
            <Button variant="outline" onClick={() => void loadData()}>
              <RefreshCw className="size-4" /> Refresh
            </Button>
          }
        />
        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        ) : null}
        {success ? (
          <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="size-4" />
            {success}
          </p>
        ) : null}
        {loading ? (
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        ) : null}
        <section className="grid gap-4 xl:grid-cols-2">
          {staff.map((row) => (
            <Card key={row.id}>
              <CardHeader>
                <CardTitle>{row.name}</CardTitle>
                <CardDescription>
                  {row.email} · {row.username}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                <Input
                  placeholder="Staff ID"
                  value={row.staff_id}
                  onChange={(event) =>
                    update(row.id, "staff_id", event.target.value)
                  }
                />
                <Input
                  placeholder="Designation"
                  value={row.designation}
                  onChange={(event) =>
                    update(row.id, "designation", event.target.value)
                  }
                />
                <Input
                  placeholder="Phone"
                  value={row.phone}
                  onChange={(event) =>
                    update(row.id, "phone", event.target.value)
                  }
                />
                <Input
                  placeholder="Office location"
                  value={row.office_location}
                  onChange={(event) =>
                    update(row.id, "office_location", event.target.value)
                  }
                />
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={row.is_active}
                    onChange={(event) =>
                      update(row.id, "is_active", event.target.checked)
                    }
                  />{" "}
                  Active account
                </label>
                <Button
                  onClick={() => void save(row)}
                  disabled={saving === row.id}
                >
                  {saving === row.id ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Save className="size-4" />
                  )}{" "}
                  Save
                </Button>
              </CardContent>
            </Card>
          ))}
        </section>
      </main>
    </div>
  )
}
