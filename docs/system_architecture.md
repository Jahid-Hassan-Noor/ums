# Django + Next.js System Architecture Blueprint

This document is a build-ready architecture contract for creating secure,
multi-role systems with Django, Django REST Framework, Next.js, PostgreSQL,
Redis, Celery, and Docker-style deployment.

It is written so a developer or Codex can take a project idea, combine it with
this architecture, and build a complete system in the same style. It is also
sanitized: it avoids credentials, private hostnames, local filesystem paths,
internal container names, production secrets, real user data, and deployment
values that should not be shared.

Use this document as the source of truth for architecture and technology. For a
new project, replace the example roles and domain apps with the product's real
roles and features, but keep the ownership boundaries and security rules.

---

## Table of Contents

1. [How To Use This File With Codex](#1-how-to-use-this-file-with-codex)
2. [Architecture Goals](#2-architecture-goals)
3. [Technology Stack](#3-technology-stack)
4. [Runtime Topology](#4-runtime-topology)
5. [Repository Layout](#5-repository-layout)
6. [Django Backend Architecture](#6-django-backend-architecture)
7. [Next.js Frontend Architecture](#7-nextjs-frontend-architecture)
8. [Authentication, Session, and Authorization](#8-authentication-session-and-authorization)
9. [API and Request Lifecycle](#9-api-and-request-lifecycle)
10. [Data Model Pattern](#10-data-model-pattern)
11. [Background Tasks and Notifications](#11-background-tasks-and-notifications)
12. [Security Baseline](#12-security-baseline)
13. [Performance Baseline](#13-performance-baseline)
14. [Testing and Verification](#14-testing-and-verification)
15. [Build Sequence For New Systems](#15-build-sequence-for-new-systems)
16. [AI Implementation Rules](#16-ai-implementation-rules)
17. [High-Impact Future Improvements](#17-high-impact-future-improvements)

---

## 1. How To Use This File With Codex

When asking Codex to build a new system from this architecture, use this shape:

```text
Project idea:
<describe the product, users, roles, and main workflows>

Architecture:
Use docs/system_architecture.md as the architecture contract.

Build instruction:
Create the system using Django + DRF backend, Next.js frontend, PostgreSQL,
Redis, Celery, Docker-style services, httpOnly cookie JWT auth, role-based apps,
protected API schema docs, and the module boundaries described in the
architecture file.
```

Codex should then:

1. Identify product roles.
2. Map each role to a backend app and a frontend route group.
3. Create a dedicated `auth_app` for identity, sessions, token helpers,
   permissions, auth serializers, and auth views.
4. Create feature/domain apps for real business areas instead of putting
   everything into one app.
5. Build the Next.js session route and backend proxy route before building
   protected screens.
6. Enforce every important rule in Django services and permissions.
7. Use frontend checks only as user experience helpers.
8. Add tests and run backend checks, frontend type checks, and migration checks.

This file is not meant to be a marketing document. It is an implementation
contract.

---

## 2. Architecture Goals

This architecture is for systems that need:

- A public site or public landing/content pages.
- A protected application area.
- Multiple user roles with separate workspaces.
- Backend-enforced permissions and business rules.
- Server-managed JWT sessions using httpOnly cookies.
- A Next.js backend-for-frontend layer that keeps tokens out of browser
  JavaScript.
- PostgreSQL-backed transactional data.
- Redis-backed cache and task queue.
- Celery workers for scheduled or long-running work.
- OpenAPI schema documentation for developer and AI-assisted integration.
- A strict separation between identity, admin/config, domain modules,
  notifications, and public content.

Core principles:

- Backend authorization is the source of truth.
- Frontend route guards are useful but are not trust boundaries.
- Tokens must not be stored in browser localStorage.
- Every role should have clear ownership in backend and frontend code.
- Shared infrastructure should be centralized.
- Feature logic should stay in feature-specific modules.
- Database writes that change business state should be service-backed and
  transaction-aware.
- Architecture docs must avoid leaking secrets or private deployment details.

---

## 3. Technology Stack

### 3.1 Backend

Use this backend stack:

| Technology | Purpose |
|---|---|
| Python | Backend language. |
| Django | Web framework, ORM, migrations, admin, settings, middleware. |
| Django REST Framework | API views, serializers, permissions, throttling, pagination. |
| SimpleJWT | JWT access and refresh tokens. |
| SimpleJWT token blacklist | Refresh-token rotation and blacklist-after-rotation. |
| drf-spectacular | OpenAPI schema and Swagger UI. |
| PostgreSQL | Primary relational database. |
| psycopg2-binary | PostgreSQL adapter. |
| Redis | Cache, Celery broker, and optional task result backend. |
| Celery | Background task execution. |
| django-cors-headers | CORS handling. |
| django-cleanup | File cleanup for replaced/deleted model files. |
| Pillow | Image validation and processing. |
| Gunicorn | Production WSGI server. |
| ReportLab | PDF/report generation when needed. |

Recommended backend packages:

```text
Django
djangorestframework
djangorestframework_simplejwt
drf-spectacular
django-cors-headers
django-cleanup
celery[redis]
psycopg2-binary
gunicorn
pillow
reportlab
```

### 3.2 Frontend

Use this frontend stack:

| Technology | Purpose |
|---|---|
| Next.js App Router | Routing, layouts, server components, route handlers. |
| React | UI runtime. |
| TypeScript | Type safety for UI, API payloads, and route helpers. |
| Tailwind CSS | Utility-first styling. |
| shadcn-style primitives | Consistent UI primitives and composition. |
| lucide-react | Icons. |
| next-themes | Theme handling. |
| class-variance-authority | Component variants. |
| clsx | Conditional class composition. |
| tailwind-merge | Class conflict resolution. |
| react-icons | Supplemental icons when needed. |
| qrcode.react | QR code display when the product needs QR workflows. |
| ESLint | Static checks. |
| Prettier | Formatting. |

Recommended frontend scripts:

```json
{
  "dev": "next dev --webpack",
  "build": "next build",
  "start": "next start",
  "lint": "eslint",
  "typecheck": "tsc --noEmit"
}
```

### 3.3 Runtime Services

Use these runtime service roles:

| Service role | Responsibility |
|---|---|
| edge proxy | One public HTTP entry point, rate limiting, security headers, routing. |
| frontend | Next.js application server. |
| backend | Django API server. |
| database | PostgreSQL. |
| cache | Redis for cache and broker use. |
| worker | Celery worker. |
| scheduler | Celery beat or equivalent scheduler. |
| media storage | Uploaded and generated files. |

Do not put real service names, private URLs, credentials, or production
addresses in shared architecture documents. Use placeholders such as:

```text
<edge-proxy>
<frontend-service>
<backend-service>
<database-service>
<cache-service>
<public-origin>
<private-api-origin>
```

---

## 4. Runtime Topology

### 4.1 Request Routing

All external traffic should enter through the edge proxy:

```text
Client
  -> Edge proxy
    -> Frontend server for pages and frontend route handlers
    -> Backend API for direct API/admin endpoints when intentionally exposed
```

The backend should not be exposed directly to browsers except through the edge
proxy. The frontend server may call the backend over the private service
network.

### 4.2 API Routing Pattern

Use two API paths:

```text
/api/*                 -> edge proxy to backend API, mostly public or direct backend paths
/<session-prefix>/*    -> Next.js route handlers for auth session and backend proxy
```

The authenticated browser path should usually be:

```text
Browser
  -> Next.js backend proxy route
    -> Django API
```

This allows the Next.js server to attach bearer tokens from httpOnly cookies
without exposing tokens to browser JavaScript.

### 4.3 Deployment Pattern

Use Docker-style services:

```text
edge proxy
frontend
backend
database
cache
worker
scheduler
```

The architecture does not require a specific hosting provider. It can run on a
VM, container platform, or managed infrastructure, as long as the service
boundaries remain intact.

---

## 5. Repository Layout

Recommended top-level layout:

```text
project-root/
  backend/
    manage.py
    core/
    auth_app/
    admin_app/
    notifications_package/
    home_app/
    <role_or_domain_app>/
    ...
  frontend/
    app/
    components/
    lib/
    middleware.ts
    next.config.mjs
    package.json
  deploy/
    edge-proxy/
  docs/
    system_architecture.md
  docker-compose.yml
```

The names can change for a new system, but the ownership boundaries should not.

---

## 6. Django Backend Architecture

### 6.1 Backend Module Map

Use this module pattern:

| Module type | Example name | Owns |
|---|---|---|
| core project | `core` | Settings, root URLs, WSGI/ASGI, Celery setup, shared infrastructure helpers. |
| identity app | `auth_app` | Profile, role lifecycle, auth serializers, auth views, token helpers, permissions. |
| admin/config app | `admin_app` | System settings, organization setup, audit surfaces, admin workflows. |
| public app | `home_app` or `public_app` | Public pages, public content APIs, news/events/directories. |
| notifications app | `notifications_package` | Notification model, notification API, reminder services, notification tasks. |
| role apps | `student_app`, `teacher_app`, etc. | Role-specific models, services, views, tests. |
| domain apps | `finance_app`, `library_app`, etc. | Domain-specific workflows that may be used by multiple roles. |
| integration apps | `chatbot_app`, `payments_app`, etc. | External systems or specialized capabilities. |

For a new system, replace role/domain names with the product's real modules.
For example:

```text
healthcare system:
  patient_app
  clinician_app
  receptionist_app
  billing_app
  lab_app

marketplace system:
  buyer_app
  seller_app
  operator_app
  catalog_app
  order_app

education system:
  student_app
  teacher_app
  executive_app
  library_app
  finance_app
```

### 6.2 `core` Project

`core` owns framework configuration:

```text
backend/core/
  settings.py
  urls.py
  celery.py
  asgi.py
  wsgi.py
  schema.py
  upload_security.py
  media_access.py
  task_backend.py
  common/                # shared, dependency-light reusable helpers (see 6.5.1)
    __init__.py
    errors.py
    <domain>.py
```

Required settings:

- `INSTALLED_APPS` includes Django apps, DRF, SimpleJWT, token blacklist,
  drf-spectacular, CORS, cleanup, and all custom apps.
- `MIDDLEWARE` includes CORS, security, gzip, sessions, common middleware,
  CSRF, auth, policy middleware, audit middleware, messages, and clickjacking
  protection.
- `REST_FRAMEWORK` uses JWT authentication, default active-user permission,
  throttling, pagination, JSON rendering, and the OpenAPI schema class.
- `SIMPLE_JWT` uses short-lived access tokens, one-week refresh tokens,
  refresh rotation, and blacklist-after-rotation.
- `DATABASES` uses PostgreSQL with persistent connections and health checks.
- `CACHES` uses Redis or an equivalent shared cache.
- `CELERY_*` settings use Redis or a compatible broker.
- CORS and CSRF origins come from environment variables.

Do not hardcode credentials or production origins in settings.

### 6.3 Django App Structure

Each app should use this structure when useful:

```text
app_name/
  apps.py
  models.py
  serializers.py
  urls.py
  service.py
  tasks.py
  tests.py
  views.py
  views/
    feature_a.py
    feature_b.py
```

Use `service.py` or feature-specific service files for business rules. Use
`views/` submodules when a single `views.py` would become too large.

### 6.4 View Pattern

Default to DRF `APIView` or generic views:

```text
APIView
  -> permission_classes
  -> serializer validation for input
  -> service call
  -> Response payload
```

Rules:

- Every protected view declares permission classes.
- Every mutating endpoint validates input.
- Views should be thin.
- Business rules belong in services.
- Multi-write operations use database transactions.
- Views return predictable JSON shapes.
- OpenAPI schema should be generated for the API.

### 6.5 Service Layer Pattern

Services own business behavior:

```python
def approve_request(actor_profile, request_id, data):
    # load object with ownership/scope checks
    # validate business state
    # write changes in a transaction
    # create audit/notification records if needed
    # return domain payload
```

Services should:

- Accept model instances or primitive IDs.
- Re-check authorization-sensitive ownership/scope.
- Use `select_related` and `prefetch_related` for expected reads.
- Use `transaction.atomic()` for multi-step writes.
- Avoid depending on frontend-only assumptions.

### 6.5.1 Shared Utilities & Code-Reduction (DRY) Pattern

As a codebase grows, small helper functions tend to get copy-pasted across apps
(error/response formatting, entity display/lookup, money math, pagination,
request parsing, slug/route normalization). Duplication inflates the line count,
causes drift (copies diverge and develop subtle bugs), and makes changes
expensive because the same logic must be edited in many places.

**Rule: consolidate reusable helpers into one shared package and import them
everywhere instead of re-defining.**

Suggested layout — a single dependency-light package for cross-app helpers:

```text
backend/core/
  common/            # cross-app, dependency-light reusable helpers
    errors.py        # error/response formatting helpers
    <domain>.py      # e.g. profiles.py, money.py, pagination.py
  ...                # other shared infrastructure (uploads, media, etc.)
```

When to consolidate:

- The same helper (or trivially different variants) appears in 2+ modules.
- The logic is generic and not tied to a single app's business rules.
- The helper is dependency-light so a shared module does not create import
  cycles. Keep app-specific business rules in that app's `service.py`.

Prefer extension over forking. If a shared helper *almost* fits, add an optional
parameter (e.g. a `default` value) instead of copying it, so all callers keep one
implementation:

```python
def first_error(errors, default="Operation failed."):
    ...  # flatten validation errors into one message; callers pass their own default
```

Backward-compatible migration. When a helper already has widely-used import
paths, move the definition into the shared package and **re-export** it from the
original module. This keeps existing call sites working without editing them all
at once:

```python
# old module keeps its public name available
from core.common.some_helper import do_thing  # re-export
```

New code should import directly from the shared package.

Concrete shared-helper inventory (cross-app, dependency-light):

- `errors.py` — flatten validation errors into one message, and build the standard
  error `Response` envelope, so every endpoint reports failures the same way.
- `profiles.py` — produce a human-friendly display name / stable identifier for an
  entity profile, and load the active profile for a user/role (with the correct
  `select_related`). Replaces the many copy-pasted `display_name`-style helpers.
- `money.py` — format a decimal as a fixed two-decimal string and parse user-supplied
  money values safely (with optional digit/scale validation). Centralizes the
  rounding and formatting rules so currency math behaves uniformly.
- `pagination.py` — paginate a queryset and produce a standardized metadata envelope
  (`count`, `page`, `page_size`, `total_pages`, `next`, `previous`). Stops each list
  view from hand-rolling the same slice/offset bookkeeping.
- `request_utils.py` — tolerant parsing of booleans, integers, and JSON bodies from
  request query/body params, with sane defaults instead of throwing on `None`/blank.

These helpers were consolidated from duplicated per-app implementations; existing
modules re-export their old names so call sites keep working, while new code imports
directly from the shared package.

Checklist before writing a new small helper:

1. Search the shared package for an existing version.
2. If it exists, import it. If it needs a tweak, extend it with an optional
   parameter rather than forking a copy.
3. If it does not exist but is clearly reusable, add it to the appropriate shared
   module and import from there.

Apply this pattern to any new system: create the shared helper package early and
route cross-cutting helpers through it to keep the total line count and
maintenance surface small.

### 6.6 URL Pattern

Use stable route prefixes:

```text
/auth/*
/admin/*
/role-a/*
/role-b/*
/feature/*
/notifications/*
/schema/
/docs/
```

Rules:

- Auth URLs stay stable even if auth implementation moves.
- Role URLs map clearly to role permission classes.
- Domain URLs map to domain ownership.
- Schema/docs routes are protected unless the API is intentionally public.

### 6.7 OpenAPI Schema

Use `drf-spectacular`.

Baseline:

- Add `drf_spectacular` to `INSTALLED_APPS`.
- Set `DEFAULT_SCHEMA_CLASS`.
- Add `/schema/` and `/docs/` routes.
- Protect schema/docs with admin-only permission by default.
- Add a fallback schema class for plain `APIView` endpoints if the project uses
  many manually constructed responses.

The schema should not include:

- Real tokens.
- Real credentials.
- Private URLs.
- Real user data.
- Production secrets.

---

## 7. Next.js Frontend Architecture

### 7.1 Frontend Layout

Recommended layout:

```text
frontend/
  app/
    layout.tsx
    page.tsx
    login/
    forgot-password/
    reset-password/
    <public-pages>/
    (<role-a>)/<role-a>/
    (<role-b>)/<role-b>/
    notifications/
    profile/
    <session-prefix>/
      session/route.ts
      backend/[[...path]]/route.ts
  components/
    layout/
    ui/
    role-zone/
    notifications/
    public/
    <role-or-domain>/
  lib/
    auth.ts
    server-session.ts
    api-base.ts
    ums-roles.ts
    notifications.ts
    optimistic.ts
    public-api.ts
    <domain-api>.ts
  middleware.ts
  next.config.mjs
```

Use route groups for organization:

```text
app/(admin)/admin/dashboard/page.tsx
app/(role-a)/role-a/dashboard/page.tsx
app/(role-b)/role-b/dashboard/page.tsx
```

Route groups in parentheses do not appear in URLs.

### 7.2 Page Layering

Every page should follow this shape:

```text
page.tsx
  -> Header / breadcrumbs / page shell
  -> feature component
    -> lib API helper
    -> shared UI primitives
```

Example:

```tsx
export default function RoleDashboardPage() {
  return (
    <div className="flex min-h-svh flex-col">
      <Header breadcrumbItems={[...]} />
      <main className="flex-1">
        <RoleDashboardContent />
      </main>
    </div>
  )
}
```

Route files should be small. Feature components hold state, forms, tables,
modals, and workflow UI.

### 7.3 Frontend API Helpers

Put API calls in `frontend/lib/`:

```text
lib/auth.ts
lib/notifications.ts
lib/public-api.ts
lib/<domain>.ts
```

Rules:

- Authenticated client-side API helpers call `apiFetch()`.
- `apiFetch()` targets the Next.js backend proxy route.
- Public server-side data helpers can call backend public endpoints directly
  from server components.
- API helper types should match backend response shapes.
- Use a declarative data fetching and caching library (e.g., TanStack Query or SWR) for client-side state/fetching instead of manual `useEffect` API loops to prevent race conditions and redundant network calls.

### 7.4 Session Route

Create a Next.js route handler for sessions:

```text
app/<session-prefix>/session/route.ts
```

Responsibilities:

- `GET`: validate current session and return sanitized `{ role, user }`.
- `POST`: proxy login/register endpoints to Django, set auth cookies, return
  sanitized session payload.
- `DELETE`: clear auth cookies.
- Set or refresh CSRF token cookie.
- Never return raw refresh tokens to browser JavaScript.

### 7.5 Backend Proxy Route

Create a catch-all backend proxy:

```text
app/<session-prefix>/backend/[[...path]]/route.ts
```

Responsibilities:

- Read access token from httpOnly cookies.
- Validate CSRF for mutating requests.
- Attach `Authorization: Bearer <access-token>` to backend request.
- Refresh tokens when access token expires.
- Retry once after selected 401 responses.
- Clear cookies when the session is invalid.
- Strip hop-by-hop headers.
- Preserve query params and request body.
- Return backend response to browser.

### 7.6 Middleware Route Guard

Use `middleware.ts` for fast route decisions:

- Allow public paths.
- Redirect unauthenticated users from protected paths to login.
- Use a role hint cookie to redirect users away from the wrong role workspace.
- Do not treat middleware as final authorization.

Backend permissions remain the authority.

### 7.7 Shared UI Modules

Recommended component ownership:

| Folder | Purpose |
|---|---|
| `components/ui` | Buttons, cards, inputs, labels, dialogs, badges, primitives. |
| `components/layout` | Header, shell, sidebar, user menu, theme wrapper. |
| `components/role-zone` | Shared dashboards, statistics pages, generic role surfaces. |
| `components/notifications` | Notification center and notification button. |
| `components/public` | Public website components. |
| `components/<role>` | Role-specific screens. |
| `components/<domain>` | Domain-specific shared screens. |

### 7.8 Frontend Reusable-Code & Code-Reduction Pattern

Large frontend systems drift when every page owns its own tiny helpers, loading
states, status badge mapping, download logic, chart scaffolding, and table
filter state. The result is more code, inconsistent behavior, and security or
UX fixes that must be repeated across many files.

**Rule: move repeated frontend behavior into shared utilities, hooks, and
compound components before the third copy appears.**

Recommended shared layout:

```text
frontend/
  lib/
    fetch-utils.ts       # path normalization, JSON/error parsing, downloads, query params
    status-utils.ts      # status badge variants and class names
    <domain-api>.ts      # API payload types and endpoint functions
  hooks/
    use-table-state.ts   # search/filter/sort/pagination state
    use-<workflow>.ts    # reusable role/workflow state machines
  components/
    ui/
      data-table-controls.tsx
    charts/
      data-chart.tsx
      chart-utils.ts
    results/
      result-display.tsx
    <domain>/
      shared compound components
```

Consolidate these patterns early:

- API path normalization, JSON parsing, throttling messages, and error extraction.
- Query-string building, filename parsing, and browser blob-download triggers.
- Status badge variant/class mapping.
- Page-level loading and error shells.
- Search/filter/sort/pagination state and table toolbars.
- Repeated admin or operator page headers.
- Add/edit entity card shells with cancel/save behavior.
- Chart canvas layout, axis/grid rendering, colors, and stat cards.
- Repeated async load/reload state.

Use wrappers to preserve existing imports during migration. For example, keep
old chart or page-component exports as thin compatibility wrappers while they
delegate to a single shared implementation. This lets a team reduce duplication
without a risky all-at-once rewrite.

Prefer small shared modules over one giant frontend utility file. A good shared
frontend helper is dependency-light, generic enough for 2+ pages, narrowly
named, easy to type-check, and free of secrets, private URLs, production values,
and real user data.

Checklist before writing new frontend logic:

1. Search `frontend/lib/`, `frontend/hooks/`, `frontend/components/ui/`, and
   relevant shared component folders.
2. If an existing helper fits, import it.
3. If it almost fits, extend it with a small optional prop or parameter.
4. If it is clearly reusable and no helper exists, add the shared helper first,
   then call it from the page.
5. Keep domain-specific business rules out of generic UI helpers; backend
   services and permissions remain the authority for sensitive decisions.

This pattern is safe for architecture documents because it describes reusable
engineering structure, not project-specific data. Use generic names and
placeholders in shared guidance; never include credentials, private hostnames,
internal user records, or proprietary deployment values.

### 7.9 Optimistic UI Pattern

Use a reusable optimistic helper for low-risk actions:

```text
snapshot current state
apply optimistic state
request backend
commit server result
rollback snapshot on error
show error
```

Use it for:

- Mark notification as read.
- Delete a local notification.
- Toggle low-risk display preferences.

Do not use it for:

- Payments.
- Grades/results.
- Permissions.
- Account creation.
- Irreversible deletes.
- Any workflow where server-side business rules are complex.

---

## 8. Authentication, Session, and Authorization

### 8.1 Identity Model

Use Django's built-in user model plus a profile:

```text
auth user
  -> profile
    -> role-specific detail model
```

The profile owns:

- Role.
- Shared account metadata.
- Active/inactive portal status.
- Profile picture.
- Password reset token digest and timestamp.
- Role detail lifecycle helpers.

Role detail models own role-specific fields:

- Student/customer/member IDs.
- Staff/operator IDs.
- Organization assignments.
- Department/unit/team scope.
- Role-specific metadata.

### 8.2 Auth App Ownership

`auth_app` should own:

```text
auth_app/
  models.py          # Profile, role lifecycle helpers, admin/staff detail if needed
  permissions.py     # IsActiveUser, IsAdminRole, IsRoleX, profile_role_for_user
  serializers.py     # Login, register, user, password reset, profile update
  auth_tokens.py     # JWT issue/rotate/session-exp helpers
  password_policy.py # Password rules
  views/account.py   # Login, register, me, refresh, password flows
  signals.py         # Profile creation and role detail lifecycle
```

Do not keep auth logic inside an unrelated admin/domain app.

### 8.3 Token Policy

Baseline:

- Short-lived access token.
- One-week refresh token.
- Refresh token rotation enabled.
- Blacklist after rotation enabled.
- Session expiry claim to cap refreshed tokens to the intended session window.
- Access token lifetime remains short.
- Refresh token lifetime defines the logged-in window.
- Immediate session revocation: Password change, password reset, or manual logout must immediately blacklist all active refresh tokens in the database, invalidating any concurrent browser sessions.

Do not implement JWT signing-key rotation with JWKS by default. Add it later
only when the project needs an independent JWT key lifecycle and can carry the
extra operational complexity.

### 8.4 Cookie Policy

Use cookies:

| Cookie | Purpose | JavaScript-readable |
|---|---|---|
| access token | Short-lived API authorization | No |
| refresh token | Session renewal | No |
| role hint | Fast route guard UX | Prefer no; readable only if low sensitivity |
| CSRF token | Double-submit CSRF protection | Yes, if using double-submit |

Cookie defaults:

- `httpOnly` for tokens.
- `sameSite=lax`.
- `secure=true` in production.
- `path=/`.
- Max age aligned with token/session purpose.
- Same-origin mapping via Edge Proxy: Both the Next.js frontend and the Django backend must be served under the same primary domain to ensure `sameSite=lax` cookies function seamlessly without cross-origin issues.

### 8.5 Authorization

Create permission classes:

```text
IsActiveUser
IsAdminRole
IsRoleA
IsRoleB
IsOwnerOrRole
IsScopedOperator
```

Permission checks must validate:

- Authenticated user.
- Active Django user.
- Existing active profile.
- Allowed role.
- Object ownership or assigned scope.

Every protected API endpoint must use backend permissions. Frontend route
guards are not enough.

---

## 9. API and Request Lifecycle

### 9.1 Authenticated Request

```text
1. Browser component calls a lib API helper.
2. Helper calls apiFetch().
3. apiFetch sends request to Next.js backend proxy route.
4. Proxy validates CSRF for mutating methods.
5. Proxy reads access token from httpOnly cookie.
6. Proxy refreshes access token if needed.
7. Proxy forwards request to Django with Authorization header.
8. Django authenticates JWT.
9. DRF permission class validates role/scope.
10. View validates input.
11. View calls service.
12. Service performs business logic and database work.
13. View returns JSON response.
14. Proxy returns response to browser.
15. UI updates state.
```

### 9.2 Login Request

```text
1. Browser submits login form.
2. Frontend calls session route POST with login endpoint and credentials.
3. Session route posts to Django auth login endpoint.
4. Django authenticates credentials and role access.
5. Django returns access token, refresh token, and sanitized user payload.
6. Session route stores tokens in httpOnly cookies.
7. Session route returns only sanitized session data to browser.
8. Browser redirects to the role dashboard.
```

### 9.3 Public Page Request

```text
1. Browser requests public page.
2. Edge proxy sends request to Next.js.
3. Server component fetches public data.
4. Public data uses bounded cache/revalidation.
5. HTML renders without protected app shell.
6. Page sends safe public cache headers.
```

### 9.4 Mutating Request

```text
1. Browser action triggers POST, PUT, PATCH, or DELETE.
2. apiFetch includes CSRF header.
3. Proxy compares CSRF header and CSRF cookie.
4. Proxy rejects mismatch before reaching Django.
5. Django still applies authentication, permissions, serializer validation,
   and service-level business rules.
```

---

## 10. Data Model Pattern

### 10.1 Identity Tables

Use:

```text
User
Profile
RoleDetail
```

For each role:

```text
Profile(role="role-a") -> RoleADetail
Profile(role="role-b") -> RoleBDetail
```

Rules:

- Profile has exactly one current role.
- Current role has exactly one matching detail row.
- Role change creates the new detail row and removes obsolete detail rows when
  needed.
- Domain records should reference `Profile` for actor/owner fields.
- Use string model references for cross-app relationships to avoid circular
  imports.

### 10.2 Domain Tables

Each domain app owns its own models:

```text
domain_app/
  models.py
  service.py
  views/
  serializers.py
  tests.py
```

Examples:

| Domain | Models |
|---|---|
| finance | Charge, LedgerEntry, PaymentAttempt, Subscription, Plan. |
| library | Book, Copy, Loan, BorrowRequest. |
| helpdesk | Ticket, Update, Assignment. |
| education | Course, Offering, Enrollment, Result, Attendance. |
| healthcare | Patient, Visit, Ward, Task, Observation. |
| marketplace | Product, Order, Shipment, Payout. |

### 10.3 Audit and Ownership Fields

Use profile references for:

- `created_by`.
- `updated_by`.
- `reviewed_by`.
- `approved_by`.
- `assigned_to`.
- `recipient`.
- `actor`.

Audit logs should store snapshots and redacted request metadata, not secrets.

---

## 11. Background Tasks and Notifications

### 11.1 Celery Pattern

Use Celery for:

- Reminders.
- Scheduled status transitions.
- Report generation.
- Email delivery fan-out.
- Import/export processing.
- Cleanup jobs.
- Payment reconciliation.

Recommended files:

```text
core/celery.py
core/task_backend.py
notifications_package/tasks.py
<domain_app>/tasks.py
```

Task rules:

- Tasks should be idempotent or protected by idempotency keys.
- Tasks should log failures.
- Tasks should re-check important database state before writing.
- Long-running tasks should write progress or completion records.
- Pass primitive database IDs (e.g., primary keys) as arguments to tasks rather than serialized Django model instances to avoid stale state and serialization bugs. Always fetch a fresh record from the database inside the task.

### 11.2 Notification Pattern

`notifications_package` owns:

```text
models.py       # Notification
views.py        # list, summary, mark read, delete
service.py      # create/send helpers
reminders.py    # reminder scheduling and delivery logic
tasks.py        # async/scheduled task entry points
```

Notification API should support:

- List notifications for current user.
- Unread count summary.
- Mark one notification read.
- Mark all read.
- Delete one notification.
- Delete read notifications.

Frontend should provide:

- Header notification count.
- Notification center.
- Optimistic read/delete for low-risk actions.

---

## 12. Security Baseline

### 12.1 Required Controls

| Area | Required control |
|---|---|
| Transport | HTTPS at production edge. |
| Token storage | httpOnly cookies, not localStorage. |
| Token lifetime | Short access token, rotating refresh token. |
| CSRF | Double-submit or framework CSRF validation for mutating requests. |
| Authorization | Backend permission classes and object-level checks. |
| Rate limiting | Edge and DRF throttling. |
| CORS | Explicit allowed origins from environment. |
| Security headers | CSP, frame protection, nosniff, referrer policy, permissions policy. |
| Uploads | Extension allowlist, magic-byte validation, size limits, image verification. |
| Audit | Mutating admin/operator actions logged with redaction. |
| Secrets | Environment variables or secret manager only. |
| Schema docs | Protected unless API is intentionally public. |

### 12.2 Middleware Order

Recommended Django middleware order:

```text
CorsMiddleware
SecurityMiddleware
GZipMiddleware
SessionMiddleware
CommonMiddleware
CsrfViewMiddleware
AuthenticationMiddleware
PolicyMiddleware
AuditMiddleware
MessageMiddleware
XFrameOptionsMiddleware
```

Policy middleware can enforce:

- Maintenance mode.
- Read-only mode.
- Feature flags.
- Route-level operational gates.

Audit middleware can record:

- Admin mutations.
- Staff/operator mutations.
- Before/after summaries.
- Redacted request metadata.

### 12.3 File Upload Security

All uploads must pass a secure storage/validation layer:

- Strip path components from filenames.
- Enforce size limits.
- Validate extension.
- Validate content type.
- Validate magic bytes.
- Verify images with Pillow.
- Protect against decompression bombs.
- Store uploaded files outside source folders.
- Prevent stored XSS from uploads (e.g., HTML, SVG) by serving files with restrictive Content-Security-Policy headers (such as `sandbox` or `default-src 'none'`) or enforcing `Content-Disposition: attachment` where direct browser rendering is not required.

### 12.4 Secrets and Sensitive Information

Never commit or include in docs:

- Secret keys.
- Passwords.
- API tokens.
- SMTP credentials.
- Payment credentials.
- Private hostnames.
- Private IPs.
- Local absolute paths.
- Real production user data.
- Raw cookies or authorization headers.

Use placeholders in examples.

---

## 13. Performance Baseline

### 13.1 Database

Use:

- PostgreSQL.
- Django migrations.
- Persistent connections with health checks.
- Indexes for common filters.
- `select_related` for foreign key and one-to-one joins.
- `prefetch_related` for reverse and many-to-many joins.
- Query-count tests for hot endpoints.

Add an external DB pooler only when metrics show connection churn or database
connection limits are a real bottleneck.

### 13.2 Cache

Use Redis cache for:

- System settings.
- Feature flags.
- Public metadata.
- Organization trees.
- Expensive summaries.
- Short-lived locks or idempotency keys.

Cache rules:

- Use short TTLs for operational settings.
- Invalidate cache after writes.
- Scope cache keys by user/role when data is permission-sensitive.
- Do not public-cache authenticated responses.

### 13.3 Response Compression

Enable gzip or equivalent compression for text responses:

- HTML.
- JSON.
- CSS.
- JavaScript.
- SVG.

Prefer edge compression when possible. Application-layer gzip is acceptable
when edge configuration must remain unchanged.

### 13.4 Public Caching

Public pages may use:

```text
Cache-Control: public, s-maxage=<short-window>, stale-while-revalidate=<long-window>
```

Authenticated pages and personalized APIs must not use public cache headers.

---

## 14. Testing and Verification

### 14.1 Backend Checks

Run:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test <changed_app> --keepdb
python manage.py spectacular --file /tmp/schema.yml --validate
```

Use `--keepdb` when the environment keeps an existing test database.

### 14.2 Frontend Checks

Run:

```bash
npm run typecheck
npm run lint
```

Run `npm run build` when:

- Shared routing changed.
- Next config changed.
- Middleware changed.
- App-wide layout changed.
- Production output behavior changed.

### 14.3 Runtime Smoke Checks

For auth/session changes:

- Login returns sanitized session data.
- Tokens are stored as httpOnly cookies.
- `/session` returns current role/user.
- Backend proxy attaches Authorization header.
- Token refresh succeeds.
- Logout clears cookies.
- Wrong role cannot access another role's API.

For schema/docs changes:

- `/schema/` is protected.
- Admin user can access schema.
- Schema generation completes with zero schema errors.

For cache changes:

- Django can set/get cache values.
- Cache failure does not expose sensitive data.

---

## 15. Build Sequence For New Systems

When building a new system from this architecture, follow this order.

### Phase 1: Foundation

1. Create repo layout: `backend/`, `frontend/`, `docs/`, `deploy/`.
2. Create Django project under `backend/core`.
3. Add Django, DRF, SimpleJWT, drf-spectacular, CORS, cleanup, Celery, Redis,
   PostgreSQL dependencies.
4. Create Next.js App Router frontend with TypeScript and Tailwind.
5. Add Docker-style services for edge, frontend, backend, database, cache,
   worker, and scheduler.
6. Create shared backend helper modules and shared frontend utility, hook, and
   component folders before building repeated feature pages.

### Phase 2: Identity

1. Create `auth_app`.
2. Add `Profile` model and role choices.
3. Add role detail lifecycle helpers.
4. Add auth serializers.
5. Add token helper functions.
6. Add permission classes.
7. Add login, register, me, refresh, password reset, and change password views.
8. Add auth URLs.
9. Add auth tests.

### Phase 3: Frontend Session Layer

1. Add `lib/server-session.ts`.
2. Add session route.
3. Add backend proxy route.
4. Add `lib/auth.ts` and `apiFetch()`.
5. Add middleware route guard.
6. Add login/logout UI.
7. Verify cookies and refresh behavior.

### Phase 4: Role and Domain Apps

1. Create one backend app per role/domain owner.
2. Create matching frontend route groups.
3. Build dashboards first.
4. Add domain models and migrations.
5. Add services before complex views.
6. Add serializers for input validation.
7. Add permission tests for every role.

### Phase 5: Shared Infrastructure

1. Add notifications app.
2. Add public content app.
3. Add admin/config settings.
4. Add audit middleware.
5. Add maintenance/read-only/feature gates.
6. Add secure upload storage.
7. Add OpenAPI schema routes.
8. Add background tasks.

### Phase 6: Product Workflows

For each workflow:

1. Define model ownership.
2. Define permissions.
3. Define service functions.
4. Define API views.
5. Define frontend API helper.
6. Define page/component UI.
7. Add tests.
8. Run targeted checks.

---

## 16. AI Implementation Rules

When Codex or another AI agent implements this architecture:

1. Start from this file and the project idea.
2. Identify roles and domain modules before writing code.
3. Create dedicated apps instead of dumping logic into one central app.
4. Keep `auth_app` as the identity/auth owner.
5. Keep public content separate from protected role apps.
6. Keep notification ownership in the notifications app.
7. Put business rules in backend services.
8. Put authorization in backend permissions and object checks.
9. Use frontend route guards only for UX.
10. Use httpOnly cookies for JWT tokens.
11. Never store tokens in localStorage.
12. Do not hardcode secrets or private URLs.
13. Add migrations for model changes.
14. Add tests near changed behavior.
15. Search shared backend/frontend helpers before creating another helper,
    hook, status mapper, load-state block, table toolbar, download trigger, or
    repeated entity editor/card shell.
16. Run backend and frontend verification.
17. Update architecture docs when architecture changes.

### 16.1 File Editing Preference

Prefer editing these files for each concern:

| Concern | Preferred files |
|---|---|
| Auth/session backend | `auth_app/*`, `core/urls.py`, `core/settings.py`. |
| Auth/session frontend | `lib/auth.ts`, `lib/server-session.ts`, session route, backend proxy route, middleware. |
| Role dashboard | role app views/services, role frontend components, role route page. |
| Notifications | `notifications_package/*`, `lib/notifications.ts`, notification components. |
| Public pages | public app views/serializers, `lib/public-api.ts`, public components. |
| Settings/feature flags | admin/config app, policy middleware, settings registry. |
| API schema | `core/schema.py`, `core/settings.py`, `core/urls.py`. |
| Upload security | shared upload storage/validator plus upload endpoints. |

### 16.2 Things To Avoid

Avoid:

- Frontend-only authorization.
- LocalStorage token storage.
- Direct browser calls to private backend services for authenticated APIs.
- One giant app owning all domains.
- One giant frontend component owning all role behavior.
- Business rules embedded only in React components.
- Raw SQL string concatenation.
- Public schema docs for private APIs.
- Broad cache keys for permission-sensitive data.
- Adding complex infrastructure before there is a measured need.
- Adding database-level non-nullable fields to existing models without providing a default (locks tables during migrations).
- Renaming or deleting database columns in a single deploy step (breaks zero-downtime deploy compatibility; use a multi-stage migration pattern).

---

## 17. High-Impact Future Improvements

These are intentionally limited to improvements that justify their complexity.

1. **Observability and alerting.**
   Add structured logs, request IDs, metrics, error tracking, uptime checks,
   task failure alerts, auth anomaly alerts, and database saturation alerts.

2. **Backup, restore, and disaster recovery drills.**
   Automate encrypted database/media backups and regularly prove restore works.

3. **Object-level authorization regression tests.**
   Add reusable tests proving users cannot read or mutate records outside their
   role, ownership, department, tenant, or assigned scope.

4. **Release gates for security and API contracts.**
   Add CI checks for migrations, backend checks, frontend type checks,
   OpenAPI schema generation, dependency vulnerabilities, and secret scanning.

5. **Load testing for high-traffic workflows.**
   Test login/session refresh, dashboards, notifications, search, public pages,
   reports, imports, and domain-specific hot paths before scaling decisions.

6. **External database pooling.**
   Add a dedicated pooler only after metrics show connection pressure that
   application-level persistent connections cannot handle.

7. **Independent JWT signing key lifecycle.**
   Add asymmetric JWT signing and JWKS only when the system needs independent
   key rotation and the team can operate the extra lifecycle safely.
