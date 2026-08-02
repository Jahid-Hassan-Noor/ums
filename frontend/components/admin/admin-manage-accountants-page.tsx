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

type Accountant = {
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

export function AdminManageAccountantsPage() {
  const {
    rows: accountants,
    loading,
    saving,
    error,
    success,
    loadData,
    update,
    save,
  } = useManageStaff<Accountant>({
    endpoint: "/admin/manage/accountants",
    responseKey: "accountants",
    loadErrorMessage: "Unable to load accountants.",
    saveErrorMessage: "Unable to update accountant.",
    payload: (accountant) => ({
      staff_id: accountant.staff_id,
      designation: accountant.designation,
      phone: accountant.phone,
      office_location: accountant.office_location,
      is_active: accountant.is_active,
    }),
  })

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/manage", title: "Manage" },
          { href: "/admin/manage/accountants", title: "Accountants" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <ManagePageHeader
          title="Manage Accountants"
          description="Maintain finance department accounts for subscriptions and payment operations."
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
          {accountants.map((accountant) => (
            <Card key={accountant.id}>
              <CardHeader>
                <CardTitle>{accountant.name}</CardTitle>
                <CardDescription>
                  {accountant.email} · {accountant.username}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                <Input
                  placeholder="Staff ID"
                  value={accountant.staff_id}
                  onChange={(event) =>
                    update(accountant.id, "staff_id", event.target.value)
                  }
                />
                <Input
                  placeholder="Designation"
                  value={accountant.designation}
                  onChange={(event) =>
                    update(accountant.id, "designation", event.target.value)
                  }
                />
                <Input
                  placeholder="Phone"
                  value={accountant.phone}
                  onChange={(event) =>
                    update(accountant.id, "phone", event.target.value)
                  }
                />
                <Input
                  placeholder="Office location"
                  value={accountant.office_location}
                  onChange={(event) =>
                    update(accountant.id, "office_location", event.target.value)
                  }
                />
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={accountant.is_active}
                    onChange={(event) =>
                      update(accountant.id, "is_active", event.target.checked)
                    }
                  />{" "}
                  Active account
                </label>
                <Button
                  onClick={() => void save(accountant)}
                  disabled={saving === accountant.id}
                >
                  {saving === accountant.id ? (
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
