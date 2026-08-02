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

type Caterer = {
  id: number
  username: string
  name: string
  email: string
  staff_id: string
  designation: string
  phone: string
  center_name: string
  unit_name: string
  canteen_location: string
  is_active: boolean
}

export function AdminManageCaterersPage() {
  const {
    rows: caterers,
    loading,
    saving,
    error,
    success,
    loadData,
    update,
    save,
  } = useManageStaff<Caterer>({
    endpoint: "/admin/manage/caterers",
    responseKey: "caterers",
    loadErrorMessage: "Unable to load caterers.",
    saveErrorMessage: "Unable to update caterer.",
    payload: (caterer) => ({
      staff_id: caterer.staff_id,
      designation: caterer.designation,
      phone: caterer.phone,
      canteen_location: caterer.canteen_location,
      is_active: caterer.is_active,
    }),
  })

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/manage", title: "Manage" },
          { href: "/admin/manage/caterers", title: "Caterers" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <ManagePageHeader
          title="Manage Caterers"
          description="Maintain canteen worker accounts under the Centre for Student Affairs and Alumni."
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
          {caterers.map((caterer) => (
            <Card key={caterer.id}>
              <CardHeader>
                <CardTitle>{caterer.name}</CardTitle>
                <CardDescription>
                  {caterer.email} · {caterer.center_name || "CSAA"} /{" "}
                  {caterer.unit_name || "CTN-ADMIN"}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                <Input
                  placeholder="Staff ID"
                  value={caterer.staff_id}
                  onChange={(event) =>
                    update(caterer.id, "staff_id", event.target.value)
                  }
                />
                <Input
                  placeholder="Designation"
                  value={caterer.designation}
                  onChange={(event) =>
                    update(caterer.id, "designation", event.target.value)
                  }
                />
                <Input
                  placeholder="Phone"
                  value={caterer.phone}
                  onChange={(event) =>
                    update(caterer.id, "phone", event.target.value)
                  }
                />
                <Input
                  placeholder="Canteen location"
                  value={caterer.canteen_location}
                  onChange={(event) =>
                    update(caterer.id, "canteen_location", event.target.value)
                  }
                />
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={caterer.is_active}
                    onChange={(event) =>
                      update(caterer.id, "is_active", event.target.checked)
                    }
                  />{" "}
                  Active account
                </label>
                <Button
                  onClick={() => void save(caterer)}
                  disabled={saving === caterer.id}
                >
                  {saving === caterer.id ? (
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
