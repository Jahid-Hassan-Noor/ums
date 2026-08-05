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

type Librarian = {
  id: number
  username: string
  name: string
  email: string
  staff_id: string
  designation: string
  phone: string
  school_name: string
  center_name: string
  unit_name: string
  department_name: string
  office_location: string
  is_active: boolean
}

function ownerLabel(librarian: Librarian) {
  const scope = librarian.school_name || librarian.center_name || "No owner scope"
  return librarian.unit_name ? `${scope} / ${librarian.unit_name}` : scope
}

export function AdminManageLibrariansPage() {
  const {
    rows: librarians,
    loading,
    saving,
    error,
    success,
    loadData,
    update,
    save,
  } = useManageStaff<Librarian>({
    endpoint: "/admin/manage/librarians",
    responseKey: "librarians",
    loadErrorMessage: "Unable to load librarians.",
    saveErrorMessage: "Unable to update librarian.",
    payload: (librarian) => ({
      staff_id: librarian.staff_id,
      designation: librarian.designation,
      phone: librarian.phone,
      office_location: librarian.office_location,
      is_active: librarian.is_active,
    }),
  })

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/manage", title: "Manage" },
          { href: "/admin/manage/librarians", title: "Librarians" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <ManagePageHeader
          title="Manage Librarians"
          description="Maintain librarian accounts assigned to configured library owners."
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
          {librarians.map((librarian) => (
            <Card key={librarian.id}>
              <CardHeader>
                <CardTitle>{librarian.name}</CardTitle>
                <CardDescription>
                  {librarian.email} - {ownerLabel(librarian)}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                <Input
                  placeholder="Staff ID"
                  value={librarian.staff_id}
                  onChange={(e) =>
                    update(librarian.id, "staff_id", e.target.value)
                  }
                />
                <Input
                  placeholder="Designation"
                  value={librarian.designation}
                  onChange={(e) =>
                    update(librarian.id, "designation", e.target.value)
                  }
                />
                <Input
                  placeholder="Phone"
                  value={librarian.phone}
                  onChange={(e) =>
                    update(librarian.id, "phone", e.target.value)
                  }
                />
                <Input
                  placeholder="Office location"
                  value={librarian.office_location}
                  onChange={(e) =>
                    update(librarian.id, "office_location", e.target.value)
                  }
                />
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={librarian.is_active}
                    onChange={(e) =>
                      update(librarian.id, "is_active", e.target.checked)
                    }
                  />{" "}
                  Active account
                </label>
                <Button
                  onClick={() => void save(librarian)}
                  disabled={saving === librarian.id}
                >
                  {saving === librarian.id ? (
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
