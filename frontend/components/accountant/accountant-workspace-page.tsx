"use client"

import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, Download, Loader2, Plus, RefreshCw, Save, Settings, Trash2, WalletCards } from "lucide-react"

import { Header } from "@/components/layout/header"
import { AccountantDashboard } from "@/components/role-zone/role-dashboard"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiFetch } from "@/lib/auth"

type View = "dashboard" | "gateway" | "plans" | "subscriptions"

type Gateway = {
  provider: string
  mode: string
  merchant_name: string
  api_base_url: string
  checkout_base_url: string
  category_code: string
  secret_key_present: boolean
  secret_key_preview: string
  callback_token_present: boolean
  callback_token_preview: string
  is_active: boolean
}

type Plan = {
  id: number
  subscription_type: string
  name: string
  description: string
  price: string
  duration_days: number
  is_active: boolean
  available_to_all_roles: boolean
  available_roles: string[]
  allowed_roles: string[]
}

type RoleOption = {
  value: string
  label: string
}

type Subscription = {
  id: number
  plan: Plan
  subscriber: {
    name: string
    role: string
    identifier: string
    email: string
  }
  status: string
  amount: string
  starts_at: string | null
  ends_at: string | null
  card_url: string
  created_at: string
}

type DashboardResponse = {
  summary: {
    active: number
    pending: number
    expired: number
    successful_payments: number
  }
  gateway: Gateway
  plans: Plan[]
  role_options: RoleOption[]
  recent_subscriptions: Subscription[]
}

type PlanForm = {
  subscription_type: string
  name: string
  description: string
  price: string
  duration_days: number
  is_active: boolean
  available_to_all_roles: boolean
  available_roles: string[]
}

const emptyGateway: Gateway = {
  provider: "toyyibpay",
  mode: "sandbox",
  merchant_name: "",
  api_base_url: "",
  checkout_base_url: "",
  category_code: "",
  secret_key_present: false,
  secret_key_preview: "",
  callback_token_present: false,
  callback_token_preview: "",
  is_active: false,
}

const emptyPlanForm: PlanForm = {
  subscription_type: "",
  name: "",
  description: "",
  price: "0.00",
  duration_days: 30,
  is_active: true,
  available_to_all_roles: true,
  available_roles: [],
}

function money(value: string) {
  return `RM ${Number(value || 0).toFixed(2)}`
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleDateString() : "Pending"
}

function formatRoles(plan: Plan, roleOptions: RoleOption[]) {
  if (plan.available_to_all_roles) return "All roles"
  const labels = roleOptions
    .filter((role) => plan.allowed_roles.includes(role.value))
    .map((role) => role.label)
  return labels.length ? labels.join(", ") : "No roles selected"
}

function viewTitle(view: View) {
  if (view === "gateway") return "Gateway Settings"
  if (view === "plans") return "Manage Subscriptions"
  if (view === "subscriptions") return "Subscription Records"
  return "Finance Dashboard"
}

export function AccountantWorkspacePage({ view }: { view: View }) {
  const [summary, setSummary] = useState<DashboardResponse["summary"] | null>(null)
  const [gateway, setGateway] = useState<Gateway>(emptyGateway)
  const [secretKey, setSecretKey] = useState("")
  const [callbackToken, setCallbackToken] = useState("")
  const [plans, setPlans] = useState<Plan[]>([])
  const [roleOptions, setRoleOptions] = useState<RoleOption[]>([])
  const [newPlan, setNewPlan] = useState<PlanForm>(emptyPlanForm)
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const data = await apiFetch<DashboardResponse>("/finance/dashboard")
    setSummary(data.summary)
    setGateway(data.gateway ?? emptyGateway)
    setPlans(data.plans ?? [])
    setRoleOptions(data.role_options ?? [])
    setSubscriptions(data.recent_subscriptions ?? [])
  }, [])

  const refresh = useCallback(() => {
    setLoading(true)
    setError("")
    void loadData()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load finance data."))
      .finally(() => setLoading(false))
  }, [loadData])

  useEffect(() => {
    const timer = window.setTimeout(refresh, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  function updateGateway(field: keyof Gateway, value: string | boolean) {
    setGateway((current) => ({ ...current, [field]: value }))
  }

  function updatePlan(id: number, field: keyof Plan, value: string | boolean | number | string[]) {
    setPlans((current) => current.map((plan) => plan.id === id ? { ...plan, [field]: value } : plan))
  }

  function updateNewPlan(field: keyof PlanForm, value: string | boolean | number | string[]) {
    setNewPlan((current) => ({ ...current, [field]: value }))
  }

  function togglePlanRole(plan: Plan, role: string, checked: boolean) {
    const roles = new Set(plan.available_roles ?? [])
    if (checked) {
      roles.add(role)
    } else {
      roles.delete(role)
    }
    updatePlan(plan.id, "available_roles", roleOptions.map((option) => option.value).filter((value) => roles.has(value)))
  }

  function toggleNewPlanRole(role: string, checked: boolean) {
    const roles = new Set(newPlan.available_roles)
    if (checked) {
      roles.add(role)
    } else {
      roles.delete(role)
    }
    updateNewPlan("available_roles", roleOptions.map((option) => option.value).filter((value) => roles.has(value)))
  }

  async function saveGateway() {
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ gateway: Gateway; message: string }>("/finance/gateway", {
        method: "PATCH",
        body: JSON.stringify({
          provider: gateway.provider,
          mode: gateway.mode,
          merchant_name: gateway.merchant_name,
          api_base_url: gateway.api_base_url,
          checkout_base_url: gateway.checkout_base_url,
          category_code: gateway.category_code,
          secret_key: secretKey,
          callback_token: callbackToken,
          is_active: gateway.is_active,
        }),
      })
      setGateway(response.gateway)
      setSecretKey("")
      setCallbackToken("")
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save gateway settings.")
    } finally {
      setSaving(false)
    }
  }

  async function savePlan(plan: Plan) {
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ plan: Plan; message: string }>("/finance/plans", {
        method: "PATCH",
        body: JSON.stringify({
          plan_id: plan.id,
          subscription_type: plan.subscription_type,
          name: plan.name,
          description: plan.description,
          price: plan.price,
          duration_days: plan.duration_days,
          is_active: plan.is_active,
          available_to_all_roles: plan.available_to_all_roles,
          available_roles: plan.available_roles,
        }),
      })
      setPlans((current) => current.map((item) => item.id === response.plan.id ? response.plan : item))
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save subscription plan.")
    } finally {
      setSaving(false)
    }
  }

  async function createPlan() {
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ plan: Plan; message: string }>("/finance/plans", {
        method: "POST",
        body: JSON.stringify(newPlan),
      })
      setPlans((current) => [...current, response.plan].sort((a, b) => a.subscription_type.localeCompare(b.subscription_type)))
      setNewPlan(emptyPlanForm)
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create subscription option.")
    } finally {
      setSaving(false)
    }
  }

  async function deletePlan(plan: Plan) {
    if (!window.confirm(`Remove ${plan.name}?`)) return
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ deleted: boolean; plan?: Plan; message: string }>("/finance/plans", {
        method: "DELETE",
        body: JSON.stringify({ plan_id: plan.id }),
      })
      if (response.deleted) {
        setPlans((current) => current.filter((item) => item.id !== plan.id))
      } else if (response.plan) {
        setPlans((current) => current.map((item) => item.id === response.plan?.id ? response.plan : item))
      }
      setSuccess(response.message)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to remove subscription option.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: "/accountant", title: "Accountant" }, { href: `/accountant/${view === "dashboard" ? "dashboard" : view}`, title: viewTitle(view) }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              {view === "gateway" ? <Settings className="size-6" /> : <WalletCards className="size-6" />} {viewTitle(view)}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">Manage finance subscriptions, DuitNow settings, and payment records.</p>
          </div>
          <Button variant="outline" disabled={loading} onClick={refresh}>{loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh</Button>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        {view === "dashboard" ? (
          <>
            <AccountantDashboard />
            {summary ? (
              <section className="grid gap-4 md:grid-cols-4">
                <Card><CardHeader><CardDescription>Active</CardDescription><CardTitle>{summary.active}</CardTitle></CardHeader></Card>
                <Card><CardHeader><CardDescription>Pending</CardDescription><CardTitle>{summary.pending}</CardTitle></CardHeader></Card>
                <Card><CardHeader><CardDescription>Expired</CardDescription><CardTitle>{summary.expired}</CardTitle></CardHeader></Card>
                <Card><CardHeader><CardDescription>Paid</CardDescription><CardTitle>{summary.successful_payments}</CardTitle></CardHeader></Card>
              </section>
            ) : null}
          </>
        ) : null}

        {view === "gateway" ? (
          <Card>
            <CardHeader>
              <CardTitle>DuitNow Merchant API</CardTitle>
              <CardDescription>{gateway.secret_key_present ? `Secret saved ${gateway.secret_key_preview}` : "No secret saved"}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2"><Label htmlFor="provider">Provider</Label><select id="provider" value={gateway.provider} onChange={(event) => updateGateway("provider", event.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"><option value="toyyibpay">ToyyibPay-compatible</option><option value="custom">Custom DuitNow endpoint</option></select></div>
              <div className="space-y-2"><Label htmlFor="mode">Mode</Label><select id="mode" value={gateway.mode} onChange={(event) => updateGateway("mode", event.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"><option value="sandbox">Sandbox</option><option value="production">Production</option></select></div>
              <div className="space-y-2"><Label htmlFor="merchant_name">Merchant Name</Label><Input id="merchant_name" value={gateway.merchant_name} onChange={(event) => updateGateway("merchant_name", event.target.value)} /></div>
              <div className="space-y-2"><Label htmlFor="category_code">Category Code</Label><Input id="category_code" value={gateway.category_code} onChange={(event) => updateGateway("category_code", event.target.value)} /></div>
              <div className="space-y-2 md:col-span-2"><Label htmlFor="api_base_url">Create Payment Endpoint</Label><Input id="api_base_url" value={gateway.api_base_url} onChange={(event) => updateGateway("api_base_url", event.target.value)} /></div>
              <div className="space-y-2 md:col-span-2"><Label htmlFor="checkout_base_url">Checkout Base URL</Label><Input id="checkout_base_url" value={gateway.checkout_base_url} onChange={(event) => updateGateway("checkout_base_url", event.target.value)} /></div>
              <div className="space-y-2"><Label htmlFor="secret_key">Secret Key</Label><Input id="secret_key" type="password" placeholder={gateway.secret_key_present ? gateway.secret_key_preview : ""} value={secretKey} onChange={(event) => setSecretKey(event.target.value)} /></div>
              <div className="space-y-2"><Label htmlFor="callback_token">Callback Token</Label><Input id="callback_token" type="password" placeholder={gateway.callback_token_present ? gateway.callback_token_preview : ""} value={callbackToken} onChange={(event) => setCallbackToken(event.target.value)} /></div>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={gateway.is_active} onChange={(event) => updateGateway("is_active", event.target.checked)} /> Active gateway</label>
              <Button onClick={() => void saveGateway()} disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Save Gateway</Button>
            </CardContent>
          </Card>
        ) : null}

        {view === "plans" ? (
          <section className="space-y-4">
            <Card>
              <CardHeader>
                <CardDescription>New option</CardDescription>
                <CardTitle>Add Subscription</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 lg:grid-cols-4">
                <div className="space-y-2"><Label htmlFor="new-plan-name">Name</Label><Input id="new-plan-name" value={newPlan.name} onChange={(event) => updateNewPlan("name", event.target.value)} /></div>
                <div className="space-y-2"><Label htmlFor="new-plan-code">Code</Label><Input id="new-plan-code" value={newPlan.subscription_type} onChange={(event) => updateNewPlan("subscription_type", event.target.value)} /></div>
                <div className="space-y-2"><Label htmlFor="new-plan-price">Price</Label><Input id="new-plan-price" type="number" min="0" step="0.01" value={newPlan.price} onChange={(event) => updateNewPlan("price", event.target.value)} /></div>
                <div className="space-y-2"><Label htmlFor="new-plan-duration">Duration Days</Label><Input id="new-plan-duration" type="number" min="1" step="1" value={newPlan.duration_days} onChange={(event) => updateNewPlan("duration_days", Number(event.target.value || 0))} /></div>
                <div className="space-y-2 lg:col-span-4"><Label htmlFor="new-plan-description">Description</Label><Input id="new-plan-description" value={newPlan.description} onChange={(event) => updateNewPlan("description", event.target.value)} /></div>
                <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={newPlan.is_active} onChange={(event) => updateNewPlan("is_active", event.target.checked)} /> Active</label>
                <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={newPlan.available_to_all_roles} onChange={(event) => updateNewPlan("available_to_all_roles", event.target.checked)} /> All roles</label>
                {!newPlan.available_to_all_roles ? (
                  <div className="grid gap-2 sm:grid-cols-2 lg:col-span-4 xl:grid-cols-3">
                    {roleOptions.map((role) => (
                      <label key={role.value} className="flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm">
                        <input type="checkbox" checked={newPlan.available_roles.includes(role.value)} onChange={(event) => toggleNewPlanRole(role.value, event.target.checked)} />
                        {role.label}
                      </label>
                    ))}
                  </div>
                ) : null}
                <div className="lg:col-span-4">
                  <Button onClick={() => void createPlan()} disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />} Add Subscription</Button>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-4 xl:grid-cols-2">
              {plans.map((plan) => (
                <Card key={plan.id}>
                  <CardHeader>
                    <CardDescription>{plan.duration_days} days · {plan.subscription_type} · {formatRoles(plan, roleOptions)}</CardDescription>
                    <CardTitle>{plan.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-3">
                    <div className="grid gap-3 md:grid-cols-2">
                      <div className="space-y-2"><Label htmlFor={`plan-${plan.id}-name`}>Name</Label><Input id={`plan-${plan.id}-name`} value={plan.name} onChange={(event) => updatePlan(plan.id, "name", event.target.value)} /></div>
                      <div className="space-y-2"><Label htmlFor={`plan-${plan.id}-code`}>Code</Label><Input id={`plan-${plan.id}-code`} value={plan.subscription_type} onChange={(event) => updatePlan(plan.id, "subscription_type", event.target.value)} /></div>
                      <div className="space-y-2"><Label htmlFor={`plan-${plan.id}-price`}>Price</Label><Input id={`plan-${plan.id}-price`} type="number" min="0" step="0.01" value={plan.price} onChange={(event) => updatePlan(plan.id, "price", event.target.value)} /></div>
                      <div className="space-y-2"><Label htmlFor={`plan-${plan.id}-duration`}>Duration Days</Label><Input id={`plan-${plan.id}-duration`} type="number" min="1" step="1" value={plan.duration_days} onChange={(event) => updatePlan(plan.id, "duration_days", Number(event.target.value || 0))} /></div>
                    </div>
                    <div className="space-y-2"><Label htmlFor={`plan-${plan.id}-description`}>Description</Label><Input id={`plan-${plan.id}-description`} value={plan.description} onChange={(event) => updatePlan(plan.id, "description", event.target.value)} /></div>
                    <div className="flex flex-wrap gap-4">
                      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={plan.is_active} onChange={(event) => updatePlan(plan.id, "is_active", event.target.checked)} /> Active</label>
                      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={plan.available_to_all_roles} onChange={(event) => updatePlan(plan.id, "available_to_all_roles", event.target.checked)} /> All roles</label>
                    </div>
                    {!plan.available_to_all_roles ? (
                      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                        {roleOptions.map((role) => (
                          <label key={role.value} className="flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm">
                            <input type="checkbox" checked={plan.available_roles.includes(role.value)} onChange={(event) => togglePlanRole(plan, role.value, event.target.checked)} />
                            {role.label}
                          </label>
                        ))}
                      </div>
                    ) : null}
                    <div className="flex flex-wrap gap-2">
                      <Button onClick={() => void savePlan(plan)} disabled={saving}>{saving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />} Save</Button>
                      <Button variant="outline" onClick={() => void deletePlan(plan)} disabled={saving}><Trash2 className="size-4" /> Delete</Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        ) : null}

        {view === "subscriptions" ? (
          <section className="grid gap-3">
            {subscriptions.map((subscription) => (
              <Card key={subscription.id}>
                <CardContent className="flex flex-col gap-4 p-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="font-medium">{subscription.subscriber.name} · {subscription.plan.name}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{subscription.subscriber.role} · {subscription.subscriber.identifier} · {subscription.status} · {formatDate(subscription.starts_at)} to {formatDate(subscription.ends_at)} · {money(subscription.amount)}</p>
                  </div>
                  {subscription.status === "active" ? (
                    <Button variant="outline" render={<a href={`/ums-auth/backend${subscription.card_url}`} target="_blank" rel="noreferrer" />}>
                      <Download className="size-4" /> Card
                    </Button>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </section>
        ) : null}
      </main>
    </div>
  )
}
