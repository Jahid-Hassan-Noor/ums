"use client"

import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, Download, Loader2, RefreshCw, WalletCards } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { apiFetch } from "@/lib/auth"

type Plan = {
  id: number
  subscription_type: string
  name: string
  description: string
  price: string
  duration_days: number
  can_purchase: boolean
}

type Subscription = {
  id: number
  plan: Plan
  status: string
  amount: string
  starts_at: string | null
  ends_at: string | null
  is_current: boolean
  card_url: string
  checkout_url: string
  created_at: string
}

function money(value: string) {
  return `RM ${Number(value || 0).toFixed(2)}`
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleDateString() : "Pending"
}

function durationLabel(days: number) {
  return `${days} ${days === 1 ? "day" : "days"}`
}

export function SubscriptionsPage({
  roleBasePath,
  roleLabel,
}: {
  roleBasePath: string
  roleLabel: string
}) {
  const [plans, setPlans] = useState<Plan[]>([])
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [busyPlan, setBusyPlan] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadData = useCallback(async () => {
    const data = await apiFetch<{ plans: Plan[]; subscriptions: Subscription[] }>("/finance/my-subscriptions")
    setPlans(data.plans ?? [])
    setSubscriptions(data.subscriptions ?? [])
  }, [])

  const refresh = useCallback(() => {
    setLoading(true)
    setError("")
    void loadData()
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load subscriptions."))
      .finally(() => setLoading(false))
  }, [loadData])

  useEffect(() => {
    const timer = window.setTimeout(refresh, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  async function purchase(plan: Plan) {
    setBusyPlan(plan.id)
    setError("")
    setSuccess("")
    try {
      const response = await apiFetch<{ checkout_url: string; message: string }>("/finance/subscriptions/purchase", {
        method: "POST",
        body: JSON.stringify({ plan_id: plan.id }),
      })
      setSuccess(response.message)
      if (response.checkout_url) {
        window.location.assign(response.checkout_url)
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create payment checkout.")
    } finally {
      setBusyPlan(null)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header breadcrumbItems={[{ href: roleBasePath, title: roleLabel }, { href: `${roleBasePath}/subscriptions`, title: "Subscriptions" }]} />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="flex flex-wrap items-end justify-between gap-4 border-b border-border/70 pb-5">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
              <WalletCards className="size-6" /> Subscriptions
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Buy available subscriptions and print active subscription cards.
            </p>
          </div>
          <Button variant="outline" disabled={loading} onClick={refresh}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
          </Button>
        </section>

        {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        {success ? <p className="flex gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700"><CheckCircle2 className="size-4" />{success}</p> : null}

        <section className="grid gap-4 md:grid-cols-2">
          {plans.length ? (
            plans.map((plan) => (
              <Card key={plan.id}>
                <CardHeader>
                  <CardDescription>{durationLabel(plan.duration_days)} · {plan.subscription_type}</CardDescription>
                  <CardTitle>{plan.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm leading-6 text-muted-foreground">{plan.description || "Subscription option managed by the finance department."}</p>
                  <div className="flex items-center justify-between gap-3 rounded-lg border bg-muted/30 p-3">
                    <span className="text-sm text-muted-foreground">Price</span>
                    <strong className="text-lg">{money(plan.price)}</strong>
                  </div>
                  <Button className="w-full" disabled={!plan.can_purchase || busyPlan === plan.id} onClick={() => void purchase(plan)}>
                    {busyPlan === plan.id ? <Loader2 className="size-4 animate-spin" /> : <WalletCards className="size-4" />}
                    Buy Subscription
                  </Button>
                </CardContent>
              </Card>
            ))
          ) : (
            <p className="rounded-lg border bg-background p-4 text-sm text-muted-foreground md:col-span-2">
              No subscription options available now.
            </p>
          )}
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold tracking-tight">My Subscriptions</h2>
          <div className="grid gap-3">
            {subscriptions.length ? (
              subscriptions.map((subscription) => (
                <Card key={subscription.id}>
                  <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="font-medium">{subscription.plan.name}</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {subscription.status} · {formatDate(subscription.starts_at)} to {formatDate(subscription.ends_at)} · {money(subscription.amount)}
                      </p>
                    </div>
                    {subscription.status === "active" ? (
                      <Button variant="outline" render={<a href={`/ums-auth/backend${subscription.card_url}`} target="_blank" rel="noreferrer" />}>
                        <Download className="size-4" /> Card
                      </Button>
                    ) : null}
                  </CardContent>
                </Card>
              ))
            ) : (
              <p className="rounded-lg border bg-background p-4 text-sm text-muted-foreground">No subscription history yet.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}
