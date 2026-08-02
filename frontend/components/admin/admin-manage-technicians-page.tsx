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

type Technician = {
  id: number
  name: string
  email: string
  staff_id: string
  designation: string
  phone: string
  department_name: string
  specialization: string
  is_active: boolean
}

export function AdminManageTechniciansPage() {
  const {
    rows: technicians,
    saving,
    error,
    success,
    loadData,
    update,
    save,
  } = useManageStaff<Technician>({
    endpoint: "/admin/manage/technicians",
    responseKey: "technicians",
    loadErrorMessage: "Unable to load technicians.",
    saveErrorMessage: "Unable to update technician.",
    payload: (technician) => ({
      staff_id: technician.staff_id,
      designation: technician.designation,
      phone: technician.phone,
      specialization: technician.specialization,
      is_active: technician.is_active,
    }),
  })

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/admin", title: "Admin" },
          { href: "/admin/manage", title: "Manage" },
          { href: "/admin/manage/technicians", title: "Technicians" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pt-4 pb-8 sm:px-6">
        <ManagePageHeader
          title="Manage Technicians"
          description="Maintain ICT Helpdesk accounts under the standalone ICT department."
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
        <section className="grid gap-4 xl:grid-cols-2">
          {technicians.map((technician) => (
            <Card key={technician.id}>
              <CardHeader>
                <CardTitle>{technician.name}</CardTitle>
                <CardDescription>
                  {technician.email} ·{" "}
                  {technician.department_name || "ICT Department"}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                <Input
                  placeholder="Staff ID"
                  value={technician.staff_id}
                  onChange={(event) =>
                    update(technician.id, "staff_id", event.target.value)
                  }
                />
                <Input
                  placeholder="Designation"
                  value={technician.designation}
                  onChange={(event) =>
                    update(technician.id, "designation", event.target.value)
                  }
                />
                <Input
                  placeholder="Phone"
                  value={technician.phone}
                  onChange={(event) =>
                    update(technician.id, "phone", event.target.value)
                  }
                />
                <Input
                  placeholder="Specialization"
                  value={technician.specialization}
                  onChange={(event) =>
                    update(technician.id, "specialization", event.target.value)
                  }
                />
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={technician.is_active}
                    onChange={(event) =>
                      update(technician.id, "is_active", event.target.checked)
                    }
                  />{" "}
                  Active account
                </label>
                <Button
                  onClick={() => void save(technician)}
                  disabled={saving === technician.id}
                >
                  {saving === technician.id ? (
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
