# UMS Enterprise Customization Guide — Ultimate Blueprint

**Version:** 3.0  
**Updated:** 2026-07-06  
**Derived from:** `UMS_ENTERPRISE_CUSTOMIZATION_GUIDE.md` (v1) and `UMS_ENTERPRISE_CUSTOMIZATION_GUIDE_DETAILED.md` (v2)  
**Related context reviewed:** `documentation.html`, `moodle_portal_functionality_comparison.md`, `threat_model.md`, `portal_dead_code_cleanup_backlog.md`

---

## 0. How To Use This Guide

This document explains how to transform the current **AIU Unified Portal** into a reusable enterprise SaaS product named **UMS — University Management System**.

The goal is not to simply rename AIU to UMS. The goal is to convert the existing project into a **multi-university platform** where many universities can use the same codebase while keeping their data, branding, settings, users, workflows, reports, files, billing, and public website fully separated.

Use this guide in four ways:

1. **Product planning** — decide what UMS will sell, what modules it includes, and how it differs from Moodle.
2. **Architecture planning** — design multi-tenancy, roles, permissions, data isolation, billing, public websites, and integrations.
3. **Engineering execution** — follow the backend, frontend, migration, testing, and deployment steps.
4. **Enterprise readiness checklist** — verify that the product is safe, configurable, secure, and sellable before onboarding real universities.

### Recommended Reading Order

| Reader | Read first | Then read |
| --- | --- | --- |
| Founder / product owner | Sections 1–4 | Sections 8, 16, 17, 19 |
| Backend developer | Sections 5–7 | Sections 10–13, Appendices A–D |
| Frontend developer | Sections 8–9 | Appendices E–F |
| DevOps / platform engineer | Sections 11–15 | Sections 17–18 |
| QA engineer | Sections 13, 17 | Appendices A, B, F |
| University stakeholder | Sections 1–4 | Sections 8, 16, 19 |

---

## 1. Executive Summary

The current AIU Unified Portal is a strong foundation because it already includes:

- A **Django + Django REST Framework backend**.
- A **Next.js + React frontend**.
- Public website pages and content surfaces.
- Applicant, student, teacher, executive, admin, librarian, caterer, technician, accountant, and public user flows.
- Admissions, academic records, LMS-like teaching workflows (assignments, attendance, course content, study guides, rubrics), student services, operations, notifications, reports, and finance/subscription features.
- Notifications, audit logs, reports, exports, and administrative dashboards.
- Docker-based local/deployment workflow.
- Existing documentation and Graphify-based repository understanding.
- Quiz engine, question bank, and gradebook modules inspired by Moodle LMS depth.
- Chatbot and vector search infrastructure.
- Centralized upload security validation.

However, a single-university portal is not yet an enterprise SaaS platform. To become UMS, the system must add:

- **Multi-tenancy:** every university is a separate tenant.
- **Tenant isolation:** one university must never see another university's data.
- **Tenant branding:** each university has its own logo, colors, public website, emails, documents, and dashboard identity.
- **Tenant-aware roles:** one login identity can have different roles in different universities.
- **Platform control plane:** UMS company staff can manage tenants, plans, billing, support, usage, and global settings.
- **Tenant application plane:** each university uses its own portal, users, academic structures, modules, reports, and workflows.
- **Module entitlements:** modules can be sold and enabled by plan.
- **Audit logs:** important actions must be traceable.
- **Billing and subscriptions:** tenants can be created, billed, suspended, upgraded, and archived.
- **Enterprise integrations:** SSO, OpenAPI, webhooks, LTI, payment gateways, email/SMS providers, and import/export tools.
- **Operational readiness:** backups, monitoring, security checks, accessibility, CI/CD, test coverage, and support runbooks.

### The Core Product Decision

UMS should be positioned as:

> **A complete cloud University Management System that gives every university a branded portal for admissions, student information, academic delivery, LMS workflows, student life, finance, operations, reporting, and integrations.**

This is broader than Moodle. Moodle is very strong as an LMS, but UMS should become a complete university operating system.

### The Most Important Engineering Decision

The most important technical decision is **tenant isolation**.

Every tenant-owned record must belong to one university. Tenant separation must be enforced by the backend, not only hidden in the frontend UI.

Recommended default:

> Use **PostgreSQL schema-per-tenant** with a proven Django multi-tenancy package such as `django-tenants`, unless the team has strong reasons to use shared tables with `tenant_id`.

---

## 2. Strategic Principles

### 2.1 Preserve Working Product Value

Do not destroy the existing AIU workflows while building UMS. Treat AIU as the first tenant. Convert one module at a time and keep every existing workflow passing targeted tests.

### 2.2 Backend-Enforced Isolation

Every tenant boundary must be enforced on the server side. The frontend may hide or show tenant-specific UI, but it must never be the source of security.

### 2.3 Configuration Over Forking

Universities will need different branding, admissions rules, grading schemes, academic terms, payment gateways, support contacts, modules, and public content. These differences should live in tenant configuration, not separate code branches.

### 2.4 Product Modules Over Random Pages

Group features into product modules that can be sold, enabled, disabled, tested, and documented. This creates pricing clarity and lowers support cost.

### 2.5 Enterprise Readiness From The Start

Tenant isolation, audit logs, backup strategy, role permissions, OpenAPI docs, accessibility, security verification, and observability are product features. They should not be left until after universities start using the platform.

### 2.6 Docker Workflow Stays Stable

The current project instruction is to use Docker containers and not change Docker configuration unless the task explicitly requires it. All customization work should respect the existing container workflow.

### 2.7 Graphify Stays Current

For code changes, use Graphify first to identify affected files. After edits, run targeted checks and `graphify update .` so the project map stays useful.

---

## 3. Current Project Baseline

The current system should be treated as **AIU Tenant 1**. Do not throw it away. Convert it gradually.

### 3.1 Existing Architecture

| Layer | Current direction | Enterprise target |
| --- | --- | --- |
| Backend | Django + DRF | Tenant-aware Django/DRF platform API |
| Frontend | Next.js App Router | Tenant-aware branded portal UI |
| Database | PostgreSQL-style relational data | Public/platform schema + tenant schemas or tenant-scoped tables |
| Auth | JWT/session role routing | Global identity + tenant membership + active tenant context |
| Deployment | Docker Compose + Nginx | Stable Docker workflow with production-grade environment separation |
| Background tasks | Celery + Redis | Tenant-aware scheduled jobs, retries, report generation, notifications |
| Public website | AIU-specific public pages | Tenant-managed public website per university |
| Reports | Institution-specific reports | Tenant reports + platform aggregate analytics |

### 3.2 Existing Product Areas

| Area | Existing value | Enterprise transformation needed |
| --- | --- | --- |
| Public website | Home, about, admissions, programmes, schools, centres, departments, events, news, official links | Make all public content tenant-owned and brandable |
| Authentication | Login, applicant login, password reset, profile, role-based routing | Add global identity, tenant memberships, tenant switching, SSO later |
| Admissions | Applicant account, application form, documents, review/status | Make application templates, intakes, documents, and status workflows configurable per tenant |
| Academic core | Schools, centres, departments, programmes, courses, semesters, offerings, timetables | Tenant-scope every academic model and unique code |
| LMS-like workflows | Course content, study guides, assignments, submissions, feedback, attendance, quizzes, gradebook | Convert to tenant-aware LMS module with continued Moodle-inspired improvements |
| Student services | Registration, history, results, leave, venue booking, hostel, canteen, library, ICT/helpdesk | Add policy configuration and module entitlements |
| Operations | Library circulation, laptop lending, canteen claims, ICT tickets, venues, reports | Tenant-scope and add configurable SLAs/workflows |
| Finance | Accountant workspace, subscriptions, payment attempts, gateway config, fines | Separate tenant internal finance from UMS platform billing |
| Notifications | Email, in-app notices, reminders | Tenant templates, sender settings, delivery logs, preferences |
| Chatbot/LLM | Ollama integration, vector search, RAG pipeline | Tenant-scoped knowledge bases and query permissions |
| Documentation | Planning docs and Docker notes | Add operator, tenant admin, developer, and support docs |

### 3.3 Keep These Rules During Transformation

1. **AIU must keep working.** Treat it as the first tenant.
2. **Avoid large rewrites.** Convert one module at a time.
3. **Use Graphify before code changes.** Identify affected models, views, serializers, pages, services, and tests.
4. **Do not change Docker configuration unless the task explicitly requires it.** Keep the current container workflow stable.
5. **Every migration needs rollback thinking.** Tenant conversion touches important data.
6. **Every tenant-sensitive change needs tests.** Especially cross-tenant access tests.

---

## 4. Product Positioning

### 4.1 What UMS Is

UMS is:

- A SaaS product for universities, colleges, training institutes, and multi-campus education groups.
- A complete University Management System, not only a Learning Management System.
- A tenant-aware platform where each institution receives its own public website, internal portal, users, roles, records, reports, branding, workflows, files, and settings.
- A modular product that can be sold by plan and enabled by feature flags.
- A system that covers the full university lifecycle:
  - public website visitor,
  - applicant,
  - accepted student,
  - registered student,
  - course participant,
  - graduate/alumni later,
  - teacher,
  - executive,
  - staff,
  - operational service user,
  - platform operator.

### 4.2 What UMS Is Not

UMS is not:

- AIU with the name changed.
- A separate code fork for each university.
- A frontend-only theme switcher.
- Only an LMS.
- A collection of unrelated dashboards.
- A system where users must log in separately for each module.
- A system where the frontend is responsible for security.

### 4.3 UMS vs Moodle

Moodle is a mature LMS. It is deeper in course activities, quizzes, question banks, gradebook, completion tracking, plugins, repositories, SCORM, H5P, LTI, badges, competencies, backup/restore, and learning analytics.

UMS should be broader. UMS should cover university administration and campus operations as first-class features.

| Area | Moodle strength | UMS target strength |
| --- | --- | --- |
| LMS depth | Very strong | Strong enough initially, deeper over time (quiz engine, question bank, gradebook now implemented) |
| Admissions | Usually external/plugin | First-class workflow |
| Student information system | Limited/core integrations | Core product area |
| Public university website | Usually separate | Built-in tenant public CMS |
| Operations | Usually external | Library, hostel, canteen, helpdesk, venue booking |
| University finance | Usually external | Tenant billing + internal finance surfaces |
| Tenant branding | LMS theme/login | Public website, portal, emails, documents, reports |
| Enterprise APIs | Plugin/web service ecosystem | OpenAPI-first platform APIs and webhooks |
| Product scope | Learning management | Full university operating system |

### 4.4 Moodle-Inspired Capabilities — Implementation Status

| Capability | Status | Notes |
| --- | --- | --- |
| Quiz engine | **Implemented** | Full quiz engine with multiple choice, true/false, short answer, essay; attempts, grading, review policies |
| Question bank | **Implemented** | Hierarchical question banks, categories, versioned questions, random rules |
| Gradebook | **Implemented** | Course-offering gradebook with categories, items, grades, scales, history, override audit |
| Attendance QR/code | **Implemented before comparison** | First-class teacher attendance sessions, QR/code, corrections, reports |
| Rubrics and marking guides | **Implemented before comparison** | Assignment rubrics available |
| Discussion forums | **Not yet implemented** | Future priority |
| Lesson/page/book content | **Not yet implemented** | Future priority |
| Completion tracking | **Not yet implemented** | Future priority |
| Conditional access | **Not yet implemented** | Future priority |
| Competencies | **Not yet implemented** | Future priority |
| Badges | **Not yet implemented** | Future priority |
| SCORM/IMS/H5P/LTI | **Not yet implemented** | Future priority |
| Plugin/repository ecosystem | **Not yet implemented** | Future priority |

---

## 5. Target Enterprise Architecture

UMS should be designed as two connected planes:

1. **Platform Control Plane** — used by the UMS company.
2. **Tenant Application Plane** — used by each university.

A third layer, **Shared Technical Services**, supports both planes.

```text
+-------------------------------------------------------------+
|                    UMS Platform Control Plane               |
| Tenant management | Billing | Plans | Support | Usage | Ops  |
+-------------------------------------------------------------+
                          |
                          | resolves tenant/domain/plan
                          v
+-------------------------------------------------------------+
|                    Shared Technical Services                |
| Auth | Tenant context | Audit | Files | Email | APIs | Jobs   |
+-------------------------------------------------------------+
                          |
                          | tenant-aware requests
                          v
+-------------------------------------------------------------+
|                    Tenant Application Plane                 |
| Public site | Admissions | SIS | LMS | Services | Reports     |
+-------------------------------------------------------------+
```

### 5.1 Platform Control Plane

The control plane is for the company operating UMS, not for university admins.

It manages:

- Tenant creation.
- Tenant domains and subdomains.
- Tenant lifecycle states.
- Subscription plans.
- Plan entitlements.
- Billing and invoices.
- Platform administrators.
- Platform support staff.
- Tenant onboarding progress.
- Global announcements.
- Platform audit logs.
- Global feature flags.
- Integration marketplace.
- Health, usage, and support metrics.

Recommended future Django app:

```text
backend/platform_app/
```

Do not mix this into `admin_app`. A university admin and a UMS platform operator are different actors.

### 5.2 Tenant Application Plane

The tenant plane is what each university uses.

It contains:

- Tenant public website.
- Tenant-specific branding.
- Tenant users and memberships.
- Admissions.
- Academic directory.
- Programmes and courses.
- Semesters and course offerings.
- Timetable and registration.
- Attendance and assignments.
- Quizzes, question banks, and gradebook.
- Results and transcripts.
- Library, hostel, canteen, ICT/helpdesk, venue booking.
- Notifications.
- Reports and exports.
- Tenant admin settings.

### 5.3 Shared Technical Services

These services must be tenant-aware:

| Service | Enterprise requirement |
| --- | --- |
| Authentication | Resolve identity and active tenant membership |
| Authorization | Check tenant role, permissions, and entitlements |
| Tenant context | Available in request, services, jobs, file paths, reports, emails |
| Notifications | Tenant sender, templates, preferences, delivery logs |
| Files | Tenant-isolated storage paths and signed download checks |
| Audit logging | Immutable logs for sensitive actions |
| Reports | Tenant-scoped exports, scheduled reports, audit trail |
| Payments | Gateway adapters, signatures, sandbox/live modes |
| Background tasks | Must run inside correct tenant context |
| Feature flags | Backend enforcement before data access/mutation |
| OpenAPI | Tenant-aware documented APIs |
| Observability | Logs and metrics include tenant identifier safely |
| AI/chatbot | Tenant-scoped knowledge bases and query permissions |

---

## 6. Multi-Tenancy Strategy

### 6.1 Recommended Default: Schema-Per-Tenant

For UMS, the recommended default is **PostgreSQL schema-per-tenant**.

In this model:

- Public/platform tables live in the public schema.
- Each university receives its own PostgreSQL schema.
- Tenant-owned tables are created inside each tenant schema.
- Tenant is resolved by domain or subdomain.
- Queries run inside the current tenant schema context.

Why this fits UMS:

- Universities expect strong data separation.
- The project already has many domain tables.
- It reduces the risk of forgetting `tenant_id` filters in every query.
- It makes tenant backup/export/purge easier than shared rows.

Suggested package direction:

```text
django-tenants or a similar mature Django schema-tenancy package
```

### 6.2 Alternative: Shared Tables With `tenant_id`

This model stores all tenants in the same tables and adds `tenant_id` to tenant-owned records.

Advantages:

- Easier cross-tenant reporting.
- Fewer schemas to migrate.
- Simpler local database inspection.

Disadvantages:

- Every query must be tenant-filtered.
- Every unique constraint must include tenant.
- One missed filter can leak another university's data.
- Tenant deletion/export is more delicate.

If this path is chosen, use PostgreSQL Row-Level Security for sensitive tables.

### 6.3 Alternative: Database-Per-Tenant

This gives strong physical isolation but increases operational complexity.

Use later for:

- Very large universities.
- Premium enterprise contracts.
- Data residency requirements.
- Separate backup and maintenance windows.
- Institutions with strict procurement/security requirements.

### 6.4 Tenant Resolution Rules

Tenants should be resolved using:

| Resolution method | Example | Use case |
| --- | --- | --- |
| Custom domain | `portal.example.edu` | Production customer domain |
| UMS subdomain | `example.umscloud.com` | Default SaaS domain |
| Path-based preview | `umscloud.com/t/example` | Internal demo/preview only |

Tenant resolution must happen before:

- Authentication context is finalized.
- Permissions are checked.
- Querysets are evaluated.
- Files are uploaded/downloaded.
- Public website data is loaded.
- Emails are rendered.
- Reports are generated.
- Background jobs run.

### 6.5 Tenant Lifecycle

Every tenant should have a lifecycle state.

| State | Meaning | Allowed behavior |
| --- | --- | --- |
| `trial` | Demo/trial tenant | Limited usage, sample data allowed |
| `onboarding` | Tenant is being configured | Setup wizard, imports, staff creation |
| `active` | Live paid tenant | Full allowed plan usage |
| `suspended` | Restricted because of billing/policy | Admin/support access only, student login may be blocked |
| `archived` | Read-only retention | Data visible to authorized admins, no new transactions |
| `deleted_pending` | Scheduled deletion | No login, pending retention/legal checks |

### 6.6 Tenant Context Must Be Available In

- Django request object.
- DRF permissions.
- Serializer validation.
- Model managers/querysets.
- Services and domain logic.
- File upload helpers.
- Email rendering.
- Celery tasks.
- Report generation.
- Audit logs.
- Frontend server-side data loading.
- Frontend client navigation and branding.

### 6.7 Tenant Isolation Rule

Use this rule everywhere:

> A tenant user can only access records that belong to the active tenant and modules enabled for that tenant's plan.

This rule must be tested for every module.

---

## 7. Platform Data Model

This section gives a conceptual model. It is not a direct code patch.

### 7.1 Platform-Owned Models

These models live outside tenant-specific university schemas/data.

| Model | Purpose | Important fields |
| --- | --- | --- |
| `UniversityTenant` | One university/customer using UMS | name, slug, lifecycle_state, timezone, locale, created_at |
| `TenantDomain` | Domain/subdomain mapping | tenant, domain, is_primary, verified_at, ssl_status |
| `TenantBranding` | Visual identity | logo, favicon, colors, typography, document header/footer |
| `TenantSettings` | Tenant defaults | timezone, locale, academic year start, support contacts |
| `TenantFeatureFlag` | Enabled features | tenant, key, enabled, rollout_value |
| `SubscriptionPlan` | Sellable product tier | name, price, billing_cycle, status |
| `PlanEntitlement` | Features/limits in plan | plan, entitlement_key, value, limit_type |
| `TenantSubscription` | Tenant plan state | tenant, plan, status, trial_end, renewal_date |
| `TenantUsageMetric` | Usage tracking | tenant, metric_key, value, measured_at |
| `PlatformUser` | UMS company user | user, platform_role, status |
| `PlatformAuditLog` | Platform-level audit | actor, action, tenant, metadata, ip_address |
| `TenantOnboardingStep` | Setup progress | tenant, step_key, status, completed_by |
| `SupportAccessGrant` | Controlled support/impersonation | platform_user, tenant, reason, expires_at |

### 7.2 Tenant-Owned Models

These existing concepts should become tenant-owned:

- User profile and role records.
- Schools, centres, departments, units.
- Programmes and courses.
- Semesters, intakes, holidays, academic calendars.
- Course offerings, groups, meetings, schedules.
- Applicants, applications, application documents, review events.
- Students, teachers, executives, staff, operational role profiles.
- Assignments, submissions, feedback, attendance, course resources.
- Quiz banks, quizzes, quiz attempts, questions, question versions.
- Gradebook scales, categories, items, grades, grade history.
- Result records, transcripts, exam slips, final exam schedules.
- Library books, copies, loans, reservations, laptop lending.
- Hostel buildings, rooms, residents, wardens, emergency contacts.
- Canteen balances, allowances, meals, claims, caterer workflows.
- ICT tickets, technician actions, SLA records.
- Venue booking requests and approvals.
- Notifications, reminders, settings.
- Reports, exports, audit logs.
- Public pages, news, events, announcements, official links, media.
- Chatbot queries, vector search indexes, LLM interaction logs.

### 7.3 Shared Reference Data

Some data may be shared globally if it is not institution-specific.

Examples:

- Country list.
- Currency list.
- Language list.
- Timezone list.
- File type definitions.
- System-level permission keys.
- Global integration provider definitions.

Rule:

> If a university can customize it, it is probably tenant-owned or tenant-configurable.

### 7.4 Unique Constraint Pattern

Single-university constraints must become tenant-aware.

| Existing idea | Enterprise rule |
| --- | --- |
| Course code unique globally | Course code unique per tenant |
| Programme code unique globally | Programme code unique per tenant |
| Student ID unique globally | Student ID unique per tenant |
| Public page slug unique globally | Slug unique per tenant |
| Email unique globally | Product decision required |

Recommended identity decision:

- Keep login identity global.
- Make tenant membership tenant-scoped.
- Allow one email to belong to multiple tenants through memberships.

### 7.5 Identity And Membership Model

Do not rely on one global `role` field.

Recommended model:

```text
User / Identity
  -> TenantMembership
       -> UniversityTenant
       -> role
       -> status
       -> permissions / permission group
       -> profile links
```

Examples:

- One person can be a teacher in University A and an external examiner in University B.
- A student can apply to one university and work as staff in another.
- A UMS support employee can access a tenant only through audited support access.

### 7.6 Platform Roles

Platform roles belong to the UMS company.

| Role | Purpose |
| --- | --- |
| `platform_owner` | Full company-level control |
| `platform_admin` | Tenant creation, plans, support, settings |
| `platform_support` | Customer support with controlled access |
| `platform_billing` | Billing, invoices, subscriptions |
| `platform_auditor` | Read-only audit/compliance access |

### 7.7 Tenant Roles

Tenant roles belong to a university.

| Role | Purpose |
| --- | --- |
| `tenant_admin` | University system administrator |
| `applicant` | Admissions applicant |
| `student` | Enrolled student |
| `teacher` | Lecturer/instructor |
| `executive` | Dean/HOD/management role |
| `accountant` | Tenant finance/accountant workflow |
| `librarian` | Library workflow |
| `technician` | ICT/helpdesk workflow |
| `caterer` | Canteen workflow |
| `public_editor` | Public website content editor |
| `observer` | Read-only reviewer/auditor |

---

## 8. Product Modules

UMS should be packaged as modules. Modules make the product easier to sell, configure, test, support, and document.

Each module should have:

- Clear feature list.
- Tenant-owned data list.
- Entitlement key.
- Permission rules.
- Frontend route group.
- Backend API group.
- Setup checklist.
- Acceptance criteria.

### 8.1 UMS Core

**Purpose:** Basic platform and university portal foundation.

Includes:

- Tenant management.
- Branding.
- Users and roles.
- Dashboards.
- Notifications.
- Audit logs.
- Public website basics.
- Academic directory basics.
- Basic reports.

Suggested entitlement keys:

```text
module.core
module.public_cms
feature.audit_logs
feature.basic_reports
```

Tenant configuration:

- University name.
- Logo and favicon.
- Color palette.
- Timezone and locale.
- Support contact.
- Admissions contact.
- Public website visibility.
- Dashboard widgets.

Acceptance criteria:

- A new tenant can be created without code changes.
- Tenant branding appears on login, dashboard, public website, emails, and documents.
- Tenant admins can manage only their own tenant.
- AIU still works as Tenant 1.

### 8.2 UMS Admissions

**Purpose:** Manage applicant-to-student lifecycle.

Includes:

- Applicant registration/login.
- Application form.
- Programme preference selection.
- Scholarship fields.
- Required document uploads.
- Review workflow.
- Status transitions.
- Offer letters.
- Enrollment conversion.

Suggested entitlement key:

```text
module.admissions
```

Tenant configuration:

- Intakes.
- Application opening/closing dates.
- Programme choices.
- Required documents.
- Scholarship fields.
- Application declaration text.
- Status pipeline.
- Reviewer roles.
- Email templates.

Tenant-owned data:

- Applicant accounts/memberships.
- Applications.
- Application documents.
- Review comments.
- Status history.
- Offer records.

Acceptance criteria:

- Two universities can run different admission forms at the same time.
- Applicant documents are stored under tenant-specific paths.
- A rejected/withdrawn application follows tenant retention rules.
- Accepted applicant can be converted into student membership.

### 8.3 UMS Academic / SIS

**Purpose:** Manage university academic structure and student information system.

Includes:

- Schools.
- Centres.
- Departments.
- Units.
- Programmes.
- Courses.
- Semesters.
- Intakes.
- Course offerings.
- Class groups.
- Timetables.
- Registration.
- Academic records.
- Results and transcripts.

Suggested entitlement key:

```text
module.sis
module.academic_core
```

Tenant configuration:

- Academic year pattern.
- Semester naming.
- Credit system.
- Programme levels.
- Grading scale.
- GPA rules.
- Registration rules.
- Transcript template.
- Student ID format.

Tenant-owned data:

- Academic organization records.
- Programme and course catalog.
- Semester records.
- Course offering records.
- Student academic records.
- Registration records.
- Results/transcripts.

Acceptance criteria:

- Two tenants can use the same course code without conflict.
- Academic APIs never return another tenant's records.
- Student ID generation is tenant-specific.
- Registration rules are enforced by backend services.

### 8.4 UMS LMS

**Purpose:** Support teaching and learning inside courses.

Includes:

- Course content.
- Study guides.
- Resources.
- Assignments.
- Submissions.
- Feedback.
- Rubrics.
- Attendance.
- QR/code attendance.
- Quiz engine.
- Question bank.
- Gradebook.
- Student course pages.
- Teacher course pages.

Suggested entitlement key:

```text
module.lms
feature.attendance
feature.assignments
feature.course_resources
feature.quiz
feature.gradebook
```

Tenant configuration:

- Attendance rules.
- Late submission rules.
- Submission file size limits.
- Allowed file types.
- Grade visibility rules.
- Course content publishing rules.
- Quiz default settings (time limits, attempt limits, review policies).
- Gradebook scale and category defaults.

Tenant-owned data:

- Course materials.
- Assignment records.
- Submissions.
- Feedback.
- Attendance sessions.
- Attendance records.
- Course announcements.
- Quiz banks, quizzes, attempts, questions.
- Gradebook categories, items, grades, history.

Acceptance criteria:

- Teacher can manage only assigned tenant course offerings.
- Student sees only registered tenant courses.
- Disabled LMS module blocks backend actions, not just menu visibility.
- Attendance records cannot cross tenant boundaries.
- Quiz engine enforces backend-side time limits, attempt counts, and review policies.
- Gradebook grades are tenant-scoped and audit-logged.

Future Moodle-inspired backlog:

- Lesson/page/book content modules.
- Discussion forums.
- Completion tracking.
- Conditional content access.
- H5P/SCORM/LTI support.
- Course backup/restore/import.

### 8.5 UMS Student Life

**Purpose:** Manage non-classroom student services.

Includes:

- Hostel.
- Leave requests.
- Venue booking.
- Emergency contacts.
- Warden schedules.
- Student calendar.
- Student service requests.

Suggested entitlement keys:

```text
module.hostel
module.venue_booking
module.student_life
```

Tenant configuration:

- Hostel policy.
- Room categories.
- Leave types.
- Approval chain.
- Venue categories.
- Booking limits.
- Emergency contact visibility.

Acceptance criteria:

- Students can request services only inside their tenant.
- Approvers see only tenant-specific requests.
- Disabled modules return backend 403/404 according to policy.
- Exported reports are tenant-scoped.

### 8.6 UMS Operations

**Purpose:** Manage campus service operations.

Includes:

- Library.
- ICT/helpdesk.
- Canteen.
- Laptop/device lending.
- Technician workflow.
- Librarian workspace.
- Caterer workflow.

Suggested entitlement keys:

```text
module.library
module.helpdesk
module.canteen
feature.device_lending
```

Tenant configuration:

- Library branches.
- Fine rules.
- Loan periods.
- Device categories.
- Ticket categories.
- SLA policies.
- Meal periods.
- Canteen allowance rules.

Acceptance criteria:

- Library books, copies, loans, and fines are tenant-owned.
- ICT tickets are visible only to assigned tenant roles.
- Canteen deductions cannot affect another tenant.
- Device lending records remain tenant-isolated.

### 8.7 UMS Finance

**Purpose:** Handle tenant billing and, separately, university finance surfaces.

Important separation:

1. **Platform billing:** UMS bills the university.
2. **Tenant finance:** The university manages its own student/staff financial workflows.

Suggested entitlement keys:

```text
module.finance
feature.billing
feature.payment_gateway
```

Platform billing includes:

- Subscription plans.
- Tenant subscriptions.
- Invoices.
- Payment attempts.
- Receipts.
- Usage limits.
- Plan changes.
- Suspension logic.

Tenant finance may include:

- Student fines.
- Canteen claims.
- Internal payments.
- Tenant accountant dashboard.

Acceptance criteria:

- Platform billing data is not mixed with tenant internal finance records.
- Payment webhooks verify signatures.
- Invoice numbers are predictable and unique.
- Suspended tenant behavior is controlled by policy.

### 8.8 UMS Communications

**Purpose:** Deliver messages, notifications, and reminders.

Includes:

- In-app notifications.
- Email delivery.
- Reminder tasks.
- Public announcements.
- Role-specific notices.
- Delivery logs.

Suggested entitlement keys:

```text
module.communications
feature.email_templates
feature.sms_adapter
feature.whatsapp_adapter
```

Tenant configuration:

- Sender name.
- Reply-to email.
- Email templates.
- Notification categories.
- Student/staff preferences.
- SMS/WhatsApp provider credentials.

Acceptance criteria:

- Email templates can be customized per tenant.
- Delivery logs include tenant and message category.
- Users can manage notification preferences where legally required.
- Failed messages can be retried safely.

### 8.9 UMS Reports And Analytics

**Purpose:** Give operational and executive visibility.

Includes:

- Admin statistics.
- Academic reports.
- Student reports.
- Teacher reports.
- Operations reports.
- Exports.
- Dashboards.
- Scheduled reports later.

Suggested entitlement keys:

```text
module.reports
feature.advanced_reports
feature.scheduled_reports
```

Report categories:

| Category | Examples |
| --- | --- |
| Academic | enrollment, course registration, GPA, results, attendance |
| Admissions | applications, conversion, pending documents, offers |
| Operations | library loans, ICT tickets, canteen claims, venue bookings |
| Finance | invoices, payments, subscriptions, fines |
| Executive | institution dashboard, trends, risk indicators |
| Platform | tenant usage, active users, storage, API calls |

Acceptance criteria:

- Tenant reports never include another tenant's records.
- Exports are audit logged.
- Platform aggregate reports do not expose private tenant details unnecessarily.

### 8.10 UMS Integrations

**Purpose:** Make UMS fit enterprise university ecosystems.

Includes:

- OpenAPI documentation.
- API keys or OAuth client credentials.
- Webhooks.
- SSO.
- LTI.
- Payment gateway adapters.
- Email/SMS/WhatsApp providers.
- Import/export templates.

Suggested entitlement keys:

```text
feature.api_access
feature.webhooks
feature.sso
feature.lti
feature.integration_marketplace
```

Acceptance criteria:

- Every external API is documented.
- API access is tenant-scoped.
- Webhooks are signed.
- SSO configuration is tenant-specific.
- Integration credentials are encrypted or stored in a secure secret store.

---

## 9. Feature Flags, Entitlements, And Pricing

### 9.1 Entitlement Principles

Feature flags and entitlements are product controls. They must be enforced in backend code.

Frontend feature checks are useful for hiding menus, but they are not security.

Example entitlement keys:

```text
module.core
module.admissions
module.sis
module.lms
module.library
module.hostel
module.canteen
module.helpdesk
module.finance
module.public_cms
module.reports
feature.sso
feature.lti
feature.api_access
feature.webhooks
feature.advanced_reports
feature.scheduled_reports
feature.email_templates
feature.quiz
feature.gradebook
limit.active_students
limit.staff_users
limit.storage_gb
limit.monthly_api_calls
limit.public_pages
limit.course_offerings
```

### 9.2 Pricing Tier Example

| Plan | Target customer | Included modules |
| --- | --- | --- |
| Starter | Small colleges, demos, early customers | Core, public website, admissions, academic directory, basic student records, basic reports |
| Professional | Mid-size institutions | Starter + SIS, registration, attendance, assignments, library, helpdesk, notifications, payment integration, quiz engine, gradebook |
| Enterprise | Large universities, multi-campus groups | Professional + SSO, API access, advanced reports, webhooks, custom branding, premium support, advanced LMS features, LTI |

### 9.3 Add-On Modules

- Hostel.
- Canteen.
- Advanced LMS.
- Advanced reports.
- API/webhooks.
- SSO.
- LTI.
- Data migration package.
- Premium support.
- Dedicated tenant database.
- Custom integration.

### 9.4 Backend Entitlement Check Pattern

Every protected action should check:

1. Is there an active tenant?
2. Is tenant lifecycle allowed?
3. Is the user's membership active?
4. Does the user have the required tenant role/permission?
5. Is the module enabled by plan/feature flag?
6. Is the usage limit still available?

---

## 10. Branding And Public Website Customization

UMS must let each university operate with its own identity.

### 10.1 Tenant Branding Fields

| Field | Purpose |
| --- | --- |
| Legal name | Official documents and contracts |
| Display name | UI and public website |
| Short name | Sidebar, navbar, small screens |
| Logo | Portal/public website |
| Icon/favicon | Browser and app identity |
| Primary color | Buttons, links, highlights |
| Secondary color | Supporting brand color |
| Accent color | Highlights/charts/cards |
| Success/warning/danger colors | Status UI |
| Public hero image | Homepage/admissions pages |
| Address | Footer/contact/documents |
| Phone/email | Contact and support |
| Admissions contact | Applicant pages/emails |
| Support contact | Help pages/emails |
| Social links | Public website footer |
| Document header/footer | PDFs, letters, receipts |
| Email sender name | Tenant email identity |

### 10.2 Public Website Pages

Each tenant should control:

- Homepage.
- About page.
- Admissions page.
- Programme pages.
- School/department/centre/unit pages.
- News.
- Events.
- Announcements.
- Official links.
- Scholarship pages.
- Student life pages.
- Contact page.
- Media library.

### 10.3 Public CMS Rules

- Public content is tenant-owned.
- Draft and published states are required.
- Slugs are unique per tenant.
- Scheduled publishing should be supported.
- Public pages should be cacheable per tenant.
- Media files must be stored in tenant-specific paths.
- Editors need role-based publishing permissions.
- Public website APIs must resolve tenant from domain/subdomain.

---

## 11. Backend Customization Roadmap

### Step 1: Add Platform Layer

Create a new app, for example:

```text
backend/platform_app/
```

Add models:

- `UniversityTenant`
- `TenantDomain`
- `TenantBranding`
- `TenantSettings`
- `SubscriptionPlan`
- `PlanEntitlement`
- `TenantSubscription`
- `TenantFeatureFlag`
- `TenantUsageMetric`
- `PlatformAuditLog`
- `TenantOnboardingStep`

Acceptance criteria:

- AIU exists as a tenant.
- Tenant can be found by domain/subdomain.
- Tenant settings and branding can be read by backend services.
- Unknown tenant domain fails safely.

### Step 2: Add Tenant Context

Add request middleware or schema-tenancy middleware.

Tenant context must provide:

- `request.tenant`
- active tenant ID/slug/schema
- tenant lifecycle state
- active subscription/plan
- enabled entitlements

Acceptance criteria:

- Every authenticated request has a resolved tenant.
- Public requests resolve tenant from domain.
- Background jobs can explicitly enter tenant context.

### Step 3: Convert Identity And Membership

Add a tenant membership model.

Fields to consider:

- user
- tenant
- role
- status
- profile link
- invited_by
- joined_at
- last_active_at
- permissions/group

Acceptance criteria:

- Existing AIU users map to AIU tenant membership.
- A user can have more than one tenant membership.
- Session response includes active tenant and role.
- Role checks use membership, not a global role field only.

### Step 4: Convert Academic Core

Convert tenant ownership for:

- Schools.
- Centres.
- Departments.
- Units.
- Programmes.
- Courses.
- Semesters.
- Holidays.
- Course offerings.
- Class groups.
- Rooms/buildings/venues.

Acceptance criteria:

- Same code/name can exist in different tenants when appropriate.
- Unique constraints are tenant-aware.
- Admin/executive academic APIs return only active tenant data.

### Step 5: Convert Admissions

Convert:

- Applicants.
- Applications.
- Documents.
- Review comments.
- Status history.
- Offers.
- Applicant-to-student conversion.

Add configurable:

- Required documents.
- Application sections.
- Intakes.
- Status workflow.
- Email templates.

Acceptance criteria:

- Each tenant can run its own admissions cycle.
- Applicant uploads are tenant-isolated.
- Accepted applicant creates tenant-scoped student membership.

### Step 6: Convert Student And Teaching Workflows

Convert:

- Course registration.
- Timetables.
- Course content.
- Study guides.
- Assignments.
- Submissions.
- Feedback.
- Attendance.
- Quiz banks, quizzes, attempts.
- Gradebook categories, items, grades.
- Results.
- Exam slips.
- Transcripts.

Acceptance criteria:

- Student sees only active tenant courses and records.
- Teacher sees only assigned tenant offerings.
- Result publishing is tenant-scoped and audited.
- Quiz and gradebook data cannot cross tenant boundaries.

### Step 7: Convert Operations Modules

Convert:

- Library.
- Hostel.
- Canteen.
- ICT/helpdesk.
- Venue booking.
- Leave requests.
- Notifications.

Acceptance criteria:

- Module APIs check both tenant and entitlement.
- Reports and exports are tenant-scoped.
- Disabled modules cannot be accessed through direct API calls.

### Step 8: Add Enterprise APIs

Add:

- OpenAPI schema.
- Tenant-scoped API authentication.
- API keys or OAuth client credentials.
- Webhook subscriptions.
- Signed webhook delivery.
- Rate limiting.
- API audit logs.

Acceptance criteria:

- Customers can read API docs.
- API credentials are tenant-scoped.
- Webhook delivery is signed, logged, and retryable.

---

## 12. Frontend Customization Roadmap

### 12.1 Tenant Branding Provider

Add a provider that loads tenant branding before rendering authenticated and public pages.

It should expose:

- tenant name.
- short name.
- logo.
- favicon.
- color tokens.
- support contact.
- enabled modules.
- active role.

Acceptance criteria:

- Login page reflects tenant branding.
- Dashboard reflects tenant branding.
- Public pages reflect tenant branding.
- Missing branding falls back to safe defaults.

### 12.2 Route Strategy

Recommended route separation:

```text
/app/(public)/...
/app/(auth)/login
/app/(tenant)/dashboard
/app/(tenant)/student/...
/app/(tenant)/teacher/...
/app/(tenant)/admin/...
/app/(platform)/...
```

Principles:

- Public website routes resolve tenant by domain.
- Tenant portal routes require tenant membership.
- Platform routes require platform role.
- Role-specific pages should share reusable module components where possible.

### 12.3 Module Navigation

Navigation should be generated from:

- active tenant.
- active membership role.
- enabled modules.
- user permissions.
- tenant lifecycle state.

Do not hardcode all modules in every sidebar.

### 12.4 Public CMS UI

Tenant admins/public editors should be able to manage:

- Pages.
- News.
- Events.
- Announcements.
- Official links.
- Media.
- Draft/publish states.
- Scheduled publishing.

### 12.5 Platform Admin UI

UMS company staff need pages for:

- Tenant list.
- Tenant details.
- Create tenant.
- Domains.
- Branding preview.
- Plans and subscriptions.
- Usage metrics.
- Support access grants.
- Platform audit logs.
- Tenant health.
- Onboarding checklist.

---

## 13. Data Migration Strategy

### 13.1 AIU Becomes The First Tenant

Do not migrate everything at once without a rollback plan.

Create:

```text
UniversityTenant(name="Albukhary International University", slug="aiu")
```

Then associate existing records with AIU or move them into the AIU tenant schema depending on tenancy strategy.

### 13.2 Migration Phases

| Phase | Scope | Goal |
| --- | --- | --- |
| 1 | Platform seed | Create AIU tenant, domain, branding, settings |
| 2 | Users | Create tenant memberships for existing users |
| 3 | Academic core | Tenant-scope schools/programmes/courses/semesters |
| 4 | Admissions | Tenant-scope applicants/applications/documents |
| 5 | Teaching | Tenant-scope LMS/attendance/results/quizzes/gradebook |
| 6 | Operations | Tenant-scope library/hostel/canteen/helpdesk/venues |
| 7 | Reports/files | Tenant-scope exports, media, generated documents |

### 13.3 Migration Safety Rules

- Back up database and media before every major migration.
- Write dry-run migration commands first.
- Count records before and after migration.
- Run tenant isolation tests after each module conversion.
- Keep AIU workflow smoke tests green.
- Make migrations idempotent when possible.
- Avoid destructive deletion until retention checks are complete.

### 13.4 Migration Verification Checklist

For every converted model:

- [ ] Record has tenant ownership or exists inside tenant schema.
- [ ] Unique constraints are tenant-aware.
- [ ] Querysets are tenant-scoped.
- [ ] API endpoints are tenant-scoped.
- [ ] Serializer validation checks tenant context.
- [ ] File paths are tenant-scoped if files exist.
- [ ] Reports/exports are tenant-scoped.
- [ ] Tests cover cross-tenant access denial.

---

## 14. Security Requirements

### 14.1 Tenant Isolation

Tenant isolation is the highest-priority security requirement.

Required checks:

- Tenant is resolved from trusted domain/subdomain context.
- Users can access only active tenant memberships.
- Querysets never return another tenant's data.
- Object-level permission checks verify tenant ownership.
- File download endpoints verify tenant access.
- Background jobs run inside explicit tenant context.
- Reports and exports are tenant-scoped.
- Admin tools cannot bypass tenant boundaries accidentally.

### 14.2 Authentication

Required:

- Strong password policy.
- Email verification.
- Password reset flow.
- Token/session expiration.
- Refresh-token safety.
- Brute-force protection.
- HttpOnly cookies for browser sessions.
- Refresh-token rotation.
- Secure cookie settings in production.
- MFA for admins and platform users.
- SSO through OpenID Connect.
- SAML later for universities requiring it.
- Account lockout or adaptive risk controls.

### 14.3 Authorization

Use layered authorization:

1. Platform role check.
2. Tenant membership check.
3. Tenant role check.
4. Object-level tenant ownership check.
5. Module entitlement check.
6. Action-specific permission check.

Avoid view-by-view permission inventions. Centralize permission checks.

### 14.4 Audit Logs

Audit these actions:

- Login failures and suspicious access.
- User/role changes.
- Tenant creation/update/suspension.
- Subscription/plan changes.
- Payment webhook events.
- Applicant status changes.
- Result publication.
- Grade changes (including quiz and gradebook grade changes).
- Quiz attempt submission and grading.
- File downloads for sensitive documents.
- Report exports.
- Support impersonation/access.
- Public content publishing.
- Integration credential changes.
- Tenant settings changes.

Audit log fields:

- actor.
- tenant.
- action.
- object type.
- object ID.
- timestamp.
- IP address.
- user agent.
- before/after metadata where safe.
- reason/comment if required.

### 14.5 File Uploads

File rules:

- Store files under tenant-specific paths.
- Validate file type.
- Validate file size.
- Scan files when possible.
- Use signed/private URLs for sensitive files.
- Never expose raw storage paths.
- Audit sensitive downloads.
- Separate public media from private documents.
- Retention rules for applicant documents.

### 14.6 Support Impersonation

Enterprise support access must be controlled.

Rules:

- Require platform support permission.
- Require written reason.
- Require expiry time.
- Show visible banner in UI.
- Write immutable audit log.
- Never reveal passwords/secrets.
- Allow tenant to disable support access for sensitive contracts.

### 14.7 Security Verification Standard

Use OWASP ASVS as the security checklist. The goal should be:

- ASVS Level 1 for early internal demos.
- ASVS Level 2 for production university customers.
- Selected Level 3 controls for high-risk areas such as authentication, tenant isolation, file uploads, audit, and admin functions.

---

## 15. Privacy And Compliance

UMS should be designed for privacy from the beginning.

Required capabilities:

- Tenant-specific data retention policy.
- Applicant data retention rules.
- Export personal data by tenant/user where legally required.
- Delete/anonymize data according to policy.
- Audit who accessed sensitive records.
- Document subprocessors and integrations.
- Separate production/staging data.
- Avoid using real customer data in development.
- Encrypt secrets and sensitive credentials.
- Limit platform staff access.

Suggested future compliance targets:

- GDPR-style data subject request workflow.
- Malaysia PDPA awareness.
- Bangladesh data protection awareness if selling locally.
- FERPA-like education record expectations for US institutions.
- Institutional procurement/security checklist.
- Data processing agreement templates.
- Local education ministry or accreditation rules by country.

---

## 16. Accessibility Requirements

Universities often require accessibility commitments during procurement. UMS should target WCAG 2.2 AA for public pages and authenticated workflows.

Practical requirements:

- Keyboard navigation.
- Visible focus states.
- Sufficient color contrast.
- Accessible form labels and errors.
- Table captions and headers for reports.
- Avoid text inside images.
- Respect reduced motion.
- Screen-reader-friendly status messages.
- Accessible file upload and document review workflows.

Accessibility should be part of acceptance criteria for new modules.

---

## 17. Performance, Scalability, And DevOps

### 17.1 Backend Performance

Required:

- Add indexes for tenant/domain/role-heavy queries.
- Avoid N+1 query problems in dashboards.
- Paginate large lists.
- Cache tenant settings and branding safely.
- Use async/background tasks for heavy exports.
- Rate-limit public and API endpoints.

### 17.2 Frontend Performance

Required:

- Cache tenant branding/public content where safe.
- Avoid loading all module data on dashboard start.
- Use route-level loading states.
- Code-split heavy admin/report pages.
- Keep public pages SEO-friendly.
- Ensure mobile-friendly tenant public website.

### 17.3 Storage

Required:

- Tenant-specific media paths.
- Separate public media and private documents.
- Storage usage metrics by tenant.
- Retention policy by file category.
- Backup and restore strategy.

### 17.4 Environments

Recommended environments:

| Environment | Purpose |
| --- | --- |
| Local | Developer work through Docker |
| Dev | Shared integration testing |
| Staging | Production-like testing and demos |
| Production | Live customer tenants |
| Sandbox tenant | Customer training/demo data |

### 17.5 Deployment Safety

- Keep Docker workflow stable.
- Use environment-specific settings.
- Never commit secrets.
- Run migrations carefully per tenant strategy.
- Use health checks.
- Add rollback plan.
- Monitor errors and background jobs.
- Test backup restore regularly.

### 17.6 Operations And Observability

Enterprise operations should add:

- Health check endpoints.
- Readiness checks.
- Background worker monitoring.
- Error tracking.
- Structured logs with tenant IDs.
- Metrics for request volume, latency, failed jobs, and storage.
- Backup verification.
- Restore drills.
- Tenant usage reports.
- Release notes.
- Migration runbooks.

---

## 18. Integration Strategy

### 18.1 OpenAPI

UMS should publish OpenAPI documentation for tenant APIs.

API docs should include:

- Authentication.
- Tenant context.
- Roles and permissions.
- Admissions endpoints.
- Academic endpoints.
- LMS endpoints (including quiz and gradebook).
- Student services endpoints.
- Operations endpoints.
- Reports endpoints.
- Webhook setup.
- Error format.
- Rate limits.

Start with: public content APIs, admissions APIs, student profile APIs, course and registration APIs, reporting/export APIs, webhook management APIs.

### 18.2 SSO

Enterprise customers may require SSO.

Support later:

- OpenID Connect.
- SAML 2.0.
- Google/Microsoft identity.
- Tenant-specific identity provider configuration.
- Just-in-time user provisioning.
- Role mapping.

### 18.3 LTI

For learning tool compatibility, plan LTI 1.3 / LTI Advantage later.

Use cases:

- External quizzes.
- Virtual labs.
- Proctoring tools.
- Content tools.
- Learning analytics tools.

### 18.4 Webhooks

Webhook events should include:

- applicant.created
- application.submitted
- application.status_changed
- student.created
- course.registration_submitted
- attendance.marked
- result.published
- quiz.attempt_submitted
- quiz.graded
- gradebook.grade_released
- invoice.created
- payment.succeeded
- ticket.created
- ticket.resolved

Webhook requirements:

- Tenant-scoped subscriptions.
- Signed payloads.
- Retry policy.
- Delivery logs.
- Secret rotation.
- Event schema documentation.

---

## 19. Reporting Strategy

Reports should be organized into layers.

### 19.1 Operational Reports

Used by tenant staff:

- Admissions funnel.
- Course registration status.
- Attendance summaries.
- Assignment submission status.
- Quiz completion and grade distribution.
- Gradebook category averages.
- Library loans.
- Hostel occupancy.
- ICT ticket SLA.
- Canteen allowance usage.
- Venue booking utilization.

### 19.2 Executive Reports

Used by university leadership:

- Enrollment trends.
- Programme performance.
- Student retention.
- Academic progress.
- Quiz/gradebook performance by course.
- Finance summaries.
- Service workload.
- Risk indicators.

### 19.3 Platform Reports

Used by UMS operators:

- Tenant usage.
- Active users.
- Storage usage.
- API calls.
- Module adoption.
- Billing health.
- Support load.
- Error rates.

Cross-tenant reports should never expose another tenant's raw student or staff records unless the platform operator has explicit authority and the report is designed for platform operations.

---

## 20. Testing Strategy

### 20.1 Required Test Categories

| Category | Purpose |
| --- | --- |
| Unit tests | Validate services, permissions, utilities |
| API tests | Validate endpoints and serializer behavior |
| Tenant isolation tests | Ensure tenant A cannot access tenant B data |
| Role permission tests | Ensure roles can/cannot perform actions |
| Entitlement tests | Ensure disabled modules are blocked |
| Migration tests | Verify data conversion safety |
| Frontend route tests | Verify role/module navigation |
| E2E smoke tests | Verify core user workflows |
| Security tests | Verify auth, file access, object permissions |
| Performance tests | Verify dashboards/reports at realistic size |
| Quiz engine tests | Attempt flow, grading, review policies, access rules |
| Gradebook tests | Grade entry, override, release, history, audit |

### 20.2 Tenant Isolation Test Matrix

For each module, test:

- list endpoint.
- detail endpoint.
- create endpoint.
- update endpoint.
- delete endpoint.
- file upload.
- file download.
- export/report.
- dashboard statistic.
- background task output.

Example:

| Test | Expected result |
| --- | --- |
| Student from Tenant A requests Tenant B course | 404 or 403 |
| Teacher from Tenant A grades Tenant B submission | 403 |
| Admin from Tenant A exports Tenant B report | 403 |
| Public domain A requests public page slug from domain B | 404 |
| Disabled library module direct API call | 403 or 404 |
| Student from Tenant A attempts Tenant B quiz | 404 |
| Teacher from Tenant A views Tenant B gradebook | 403 |

### 20.3 Targeted Verification Pattern

After each implementation PR:

1. Run affected backend tests.
2. Run affected frontend checks.
3. Run tenant isolation tests for changed module.
4. Run AIU smoke flow.
5. Update Graphify.
6. Update documentation.

---

## 21. Documentation Strategy

UMS needs four documentation sets.

### 21.1 Product Documentation

For sales and stakeholders:

- Product overview.
- Module descriptions.
- Plan comparison.
- Security overview.
- Implementation timeline.
- Integration overview.
- Accessibility statement.

### 21.2 Tenant Admin Documentation

For university admins:

- Tenant setup.
- Branding setup.
- User and role management.
- Academic setup.
- Admissions configuration.
- Module configuration.
- Reports and exports.
- Troubleshooting.

### 21.3 Developer Documentation

For engineering:

- Architecture.
- Tenant context.
- Permission patterns.
- API conventions.
- Model ownership rules.
- Testing patterns.
- Deployment notes.
- Migration runbooks.

### 21.4 Support Documentation

For customer support:

- Tenant onboarding checklist.
- Common issues.
- Support access procedure.
- Incident response.
- Billing support.
- Data export/delete request process.
- Escalation rules.

---

## 22. Phased Implementation Plan

### Phase 0: Discovery And Hardening Baseline

Goal: confirm current project state before architecture changes.

Tasks:

- Inventory hardcoded AIU names, domains, emails, and branding.
- Inventory backend models and classify ownership.
- Inventory frontend routes and classify by module.
- Inventory public content sources.
- Inventory file paths.
- Inventory reports/exports.
- Inventory auth and role checks.
- Create tenant conversion checklist.

Deliverables:

- Tenant conversion matrix.
- Hardcoded AIU cleanup backlog.
- Security and tenant isolation test plan.
- Updated documentation.

### Phase 1: Platform Foundation

Goal: create the SaaS control plane.

Tasks:

- Add platform app.
- Add tenant/domain/branding/settings/plan/entitlement/subscription models.
- Add AIU tenant seed.
- Add tenant resolution.
- Add platform audit logs.
- Add platform admin permissions.

Acceptance criteria:

- AIU is represented as a tenant.
- Unknown domains fail safely.
- Tenant settings can be read by backend code.
- Platform users are separate from university users.

### Phase 2: Auth And Membership

Goal: make identity and roles tenant-aware.

Tasks:

- Add tenant memberships.
- Map existing users to AIU tenant.
- Update login/session output.
- Add tenant switcher behavior.
- Update permissions.
- Add profile isolation tests.

Acceptance criteria:

- User role is scoped to tenant.
- Tenant A cannot view Tenant B users.
- Existing role dashboards still load.

### Phase 3: Branding And Public Website

Goal: remove hardcoded AIU public identity from reusable logic.

Tasks:

- Add tenant branding API.
- Convert public content to tenant-owned data.
- Add public content management by tenant.
- Add slug rules.
- Add media path isolation.
- Add preview/publish states.

Acceptance criteria:

- AIU public site renders from tenant configuration.
- Demo tenant can have different name, logo, colors, and pages.
- Public pages remain accessible without authentication.

### Phase 4: Academic Core

Goal: tenant-scope the academic structure.

Tasks:

- Convert schools, centres, departments, units, programmes, courses, semesters, offerings.
- Update unique constraints.
- Update academic APIs.
- Update imports/exports.
- Add isolation tests.

Acceptance criteria:

- Two tenants can use the same course code.
- Academic APIs return only active tenant data.
- Existing AIU academic pages continue to work.

### Phase 5: Admissions

Goal: make admissions configurable per university.

Tasks:

- Tenant-scope applicants/applications/documents.
- Add tenant-specific intakes.
- Add tenant-specific required documents.
- Add configurable application sections.
- Add applicant-to-student conversion.
- Add admission audit logs.

Acceptance criteria:

- Demo tenant can run admissions with its own programmes/documents.
- AIU admissions still work.
- Applicant documents are isolated per tenant.

### Phase 6: Academic Delivery And LMS

Goal: convert teaching and student workflows.

Tasks:

- Tenant-scope course content.
- Tenant-scope assignments/submissions.
- Tenant-scope attendance.
- Tenant-scope registration.
- Tenant-scope quizzes and question banks.
- Tenant-scope gradebook.
- Tenant-scope results/transcripts.
- Add future LTI planning interfaces.

Acceptance criteria:

- Student sees only active tenant courses.
- Teacher manages only assigned tenant offerings.
- Registration rules remain backend-enforced.
- Quiz and gradebook data are tenant-isolated.

### Phase 7: Operations Modules

Goal: convert student life and operations.

Tasks:

- Tenant-scope library.
- Tenant-scope hostel.
- Tenant-scope canteen.
- Tenant-scope ICT/helpdesk.
- Tenant-scope venue booking.
- Tenant-scope leave.
- Tenant-scope notifications.
- Add entitlement checks.

Acceptance criteria:

- Disabled modules do not expose APIs/actions.
- Tenant isolation tests pass for every module.
- Operational reports are tenant-scoped.

### Phase 8: Finance, Billing, And Entitlements

Goal: make UMS sellable as SaaS.

Tasks:

- Separate platform billing from tenant finance.
- Add plan entitlements.
- Add subscription status checks.
- Add usage tracking.
- Add invoice/payment flow.
- Add gateway adapters.
- Add webhook verification.

Acceptance criteria:

- Tenant can be assigned a plan.
- Disabled modules are blocked by backend entitlement checks.
- Billing events are audited.

### Phase 9: Enterprise Integrations

Goal: support university procurement and integration needs.

Tasks:

- Add OpenAPI docs.
- Add OIDC SSO.
- Add API keys/OAuth clients.
- Add webhooks.
- Add import/export templates.
- Plan LTI 1.3 integration.

Acceptance criteria:

- Tenant-specific SSO can be configured.
- API credentials are tenant-scoped.
- Webhooks are signed and logged.

### Phase 10: Production Readiness

Goal: prepare UMS for real customers.

Tasks:

- Security review.
- Accessibility review.
- Backup/restore verification.
- Observability dashboards.
- Error tracking.
- Tenant onboarding wizard.
- Documentation portal.
- Support runbooks.
- SLA monitoring.

Acceptance criteria:

- New university can be onboarded without code changes.
- Tenant isolation tests pass.
- Backup restore has been tested.
- Security checklist is complete for production scope.

---

## 23. First 90-Day Execution Plan

### Days 1–15: Discovery And Baseline

- Create tenant conversion inventory.
- Find hardcoded AIU names/domains/branding.
- Classify models by ownership.
- Classify routes by module.
- Define platform app model plan.
- Define tenant isolation test matrix.
- Add initial documentation updates.

### Days 16–30: Platform App And Tenant Resolution

- Add platform app.
- Add tenant, domain, branding, settings, plan, entitlement models.
- Create AIU tenant.
- Add tenant context middleware/schema framework.
- Add tests for tenant resolution.

### Days 31–45: Membership And Auth

- Add tenant memberships.
- Convert role resolution.
- Convert login/session output.
- Convert profile access.
- Add tenant switcher for multi-membership users.
- Add profile isolation tests.

### Days 46–60: Branding And Public Website

- Convert branding configuration.
- Convert public site content to tenant-owned data.
- Add tenant media path strategy.
- Add public content isolation tests.
- Render demo tenant public website.

### Days 61–75: Academic Core

- Convert schools/programmes/courses/semesters/offerings.
- Update academic APIs.
- Update frontend academic pages.
- Add academic isolation tests.

### Days 76–90: Admissions Demo Tenant

- Convert admissions and applicant documents.
- Add configurable application requirements.
- Add applicant-to-student conversion.
- Add admissions isolation tests.
- Prepare first demo tenant.

---

## 24. First Implementation PR Sequence

Use small pull requests. Each PR should have one purpose and targeted tests.

1. Add `platform_app` skeleton.
2. Add tenant/domain models.
3. Add tenant branding/settings models.
4. Add plan/entitlement/subscription models.
5. Add AIU tenant seed command or migration.
6. Add tenant resolution middleware.
7. Add tenant context helper.
8. Add tenant-aware test factories.
9. Add tenant membership model.
10. Convert login/session response.
11. Convert profile and role resolution.
12. Add tenant branding API.
13. Convert public site data loading.
14. Convert academic directory models/APIs.
15. Convert admissions models/APIs.
16. Convert course offerings and registration.
17. Convert attendance and assignments.
18. Convert quiz banks, quizzes, and gradebook.
19. Convert results/transcripts.
20. Convert operations modules.
21. Add entitlement checks and module gating.
22. Add platform billing and usage metrics.
23. Add OpenAPI documentation.
24. Add webhook foundation.
25. Add SSO foundation.
26. Add production readiness checks.

---

## 25. Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Tenant data leakage | Critical | Backend tenant checks, schema tenancy, object permissions, isolation tests |
| Big-bang rewrite fails | High | Convert one module at a time, keep AIU as first tenant |
| Hardcoded AIU logic remains | High | Search/inventory hardcoded names, add tenant branding/settings |
| Permissions become inconsistent | High | Centralize membership and permission helpers |
| Reports leak data | Critical | Tenant-scope report queries and exports, add tests |
| Files leak across tenants | Critical | Tenant-specific storage paths and download permissions |
| Billing blocks real users incorrectly | High | Clear lifecycle rules, test suspension/active/trial states |
| Migration corrupts data | Critical | Backups, dry runs, record counts, rollback plan |
| Frontend hides but API allows action | High | Backend entitlement enforcement required |
| Performance drops after tenant layer | Medium | Add indexes, caching, pagination, query profiling |
| Customer setup too hard | Medium | Onboarding wizard, import templates, admin docs |
| Moodle expectations exceed LMS module | Medium | Position UMS clearly; maintain advanced LMS roadmap |
| Quiz/gradebook data cross-tenant leak | Critical | Backend-enforced offering/student/teacher scoping in all quiz and gradebook queries |
| File/upload security bypass | Critical | Centralized upload validation, type/size checks, tenant-scoped paths |

---

## 26. Definition Of Enterprise Ready

UMS is enterprise-ready only when the following are true:

### Product Readiness

- [ ] Tenant can be created without code changes.
- [ ] Tenant can configure branding, public site, users, and modules.
- [ ] Plans and entitlements control available features.
- [ ] AIU works as the first tenant.
- [ ] Demo tenant can be shown with different branding/data.

### Security Readiness

- [ ] Tenant isolation tests pass for all converted modules.
- [ ] Object-level permissions are enforced.
- [ ] File downloads are permission checked.
- [ ] Audit logs exist for sensitive actions.
- [ ] Support access is controlled and logged.
- [ ] OWASP ASVS Level 2 is targeted for production.

### Operational Readiness

- [ ] Backups are automated.
- [ ] Restore has been tested.
- [ ] Monitoring and error tracking exist.
- [ ] Background task failures are visible.
- [ ] Production/staging/dev environments are separated.

### Customer Readiness

- [ ] Tenant onboarding checklist exists.
- [ ] Tenant admin documentation exists.
- [ ] Support runbooks exist.
- [ ] Data migration process is documented.
- [ ] Pricing/module packaging is clear.
- [ ] WCAG 2.2 AA is the target for UI work.

### Engineering Readiness

- [ ] OpenAPI docs exist for customer-facing APIs.
- [ ] Tests cover tenant isolation, roles, entitlements, and migrations.
- [ ] Graphify is updated after major changes.
- [ ] Development workflow remains Docker-compatible.

---

## 27. Immediate Backlog

### Documentation Backlog

- [ ] Create tenant conversion matrix by model.
- [ ] Create frontend route-to-module map.
- [ ] Create API endpoint-to-module map.
- [ ] Create hardcoded AIU cleanup list.
- [ ] Create tenant onboarding checklist.
- [ ] Create support access policy.
- [ ] Create data retention policy draft.

### Engineering Backlog

- [ ] Add `platform_app`.
- [ ] Add tenant/domain/branding/settings models.
- [ ] Add AIU tenant seed.
- [ ] Add tenant resolution.
- [ ] Add tenant membership model.
- [ ] Add permission helper.
- [ ] Add entitlement helper.
- [ ] Add tenant-aware test factories.
- [ ] Convert public site branding.
- [ ] Convert academic core.
- [ ] Convert admissions.
- [ ] Tenant-scope quiz and gradebook data.
- [ ] Add quiz/gradebook tenant isolation tests.

### Product Backlog

- [ ] Finalize UMS module list.
- [ ] Finalize plan packaging.
- [ ] Finalize target customer profile.
- [ ] Finalize demo tenant story.
- [ ] Finalize Moodle comparison messaging.
- [ ] Finalize first customer onboarding process.

---

# Appendix A — Tenant Conversion Matrix Template

Use this table for every model or feature area.

| Item | Current owner | Target owner | Conversion action | Risk | Tests needed |
| --- | --- | --- | --- | --- | --- |
| Users | Global | Global identity + tenant membership | Add membership model | High | login, role, tenant switch |
| Student profile | AIU-specific | Tenant-owned | Link to tenant membership | High | profile isolation |
| Course | Global/AIU | Tenant-owned | Add tenant/schema ownership | High | same course code in two tenants |
| Programme | Global/AIU | Tenant-owned | Tenant-aware unique code | High | programme isolation |
| Application | AIU-specific | Tenant-owned | Tenant-scope applicant flow | High | application isolation |
| Assignment | Course-owned | Tenant-owned through course offering | Verify tenant context | High | cross-tenant submission denied |
| Quiz/QuestionBank | Course-owned | Tenant-owned through course offering | Verify tenant context | High | cross-tenant quiz access denied |
| Gradebook | Course-offering-owned | Tenant-owned | Verify tenant context | High | cross-tenant grade view denied |
| Library book | AIU-specific | Tenant-owned | Tenant-scope inventory | Medium | library isolation |
| ICT ticket | AIU-specific | Tenant-owned | Tenant-scope service workflow | Medium | ticket visibility |
| Public page | AIU public site | Tenant-owned CMS | Tenant slug + publish rules | High | domain-based public pages |
| Report export | AIU-specific | Tenant-owned output | Tenant-scope queries/files | Critical | export leakage test |

---

# Appendix B — Entitlement Matrix Template

| Entitlement key | Type | Used by | Default plan | Backend enforcement point |
| --- | --- | --- | --- | --- |
| `module.admissions` | Module | Applicant/admin admissions APIs | Starter | admissions permissions/service layer |
| `module.sis` | Module | Academic records/registration | Professional | academic/student APIs |
| `module.lms` | Module | Courses/assignments/attendance | Professional | teacher/student course APIs |
| `module.library` | Module | Library operations | Professional | librarian APIs |
| `module.hostel` | Module | Hostel services | Add-on | hostel APIs |
| `module.canteen` | Module | Canteen workflows | Add-on | caterer/accountant APIs |
| `module.quiz` | Module | Quiz engine/attempts | Professional | quiz service/view permissions |
| `module.gradebook` | Module | Gradebook entry/view | Professional | gradebook service/view permissions |
| `feature.sso` | Feature | Login/auth | Enterprise | auth configuration layer |
| `feature.api_access` | Feature | External APIs | Enterprise | API auth/rate limiter |
| `limit.active_students` | Limit | Tenant usage | All plans | user creation/import |
| `limit.storage_gb` | Limit | File uploads | All plans | upload service |

---

# Appendix C — Example Model Sketches

These are conceptual examples only. Adjust to the actual project conventions.

```python
class UniversityTenant(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    lifecycle_state = models.CharField(max_length=32)
    timezone = models.CharField(max_length=64, default="Asia/Kuala_Lumpur")
    locale = models.CharField(max_length=16, default="en")
    created_at = models.DateTimeField(auto_now_add=True)
```

```python
class TenantDomain(models.Model):
    tenant = models.ForeignKey(UniversityTenant, on_delete=models.CASCADE)
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
```

```python
class TenantMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tenant = models.ForeignKey(UniversityTenant, on_delete=models.CASCADE)
    role = models.CharField(max_length=64)
    status = models.CharField(max_length=32, default="active")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "tenant", "role")]
```

---

# Appendix D — API Contract Examples

### Tenant Branding

```http
GET /api/platform/tenant/branding/
```

Returns active tenant branding for the current domain/session.

```json
{
  "tenant": "aiu",
  "display_name": "Albukhary International University",
  "short_name": "AIU",
  "logo_url": "...",
  "colors": {
    "primary": "#1d4ed8",
    "secondary": "#0f172a",
    "accent": "#0891b2"
  },
  "support_email": "support@example.edu"
}
```

### Tenant Entitlements

```http
GET /api/platform/tenant/entitlements/
```

Returns enabled modules/features for active tenant.

```json
{
  "modules": ["core", "admissions", "sis", "lms"],
  "features": ["basic_reports", "email_templates"],
  "limits": {
    "active_students": 5000,
    "storage_gb": 100
  }
}
```

### Webhook Event Example

```json
{
  "event": "application.status_changed",
  "tenant": "aiu",
  "occurred_at": "2026-07-04T10:30:00Z",
  "data": {
    "application_id": "APP-2026-0001",
    "old_status": "reviewing",
    "new_status": "offered"
  }
}
```

---

# Appendix E — Frontend Structure Suggestion

```text
frontend/app/
  (public)/
    page.tsx
    admissions/
    programmes/
    news/
    events/
  (auth)/
    login/
    forgot-password/
  (tenant)/
    dashboard/
    student/
    teacher/
    admin/
    executive/
    librarian/
    technician/
    caterer/
    accountant/
  (platform)/
    tenants/
    billing/
    support/
    audit/
```

Shared frontend packages/components:

```text
frontend/components/tenant/
frontend/components/modules/
frontend/lib/tenant.ts
frontend/lib/entitlements.ts
frontend/lib/permissions.ts
frontend/lib/api-client.ts
```

---

# Appendix F — Tenant Onboarding Checklist

### Before Creating Tenant

- [ ] Contract signed.
- [ ] Plan selected.
- [ ] Domain/subdomain decided.
- [ ] Admin contact confirmed.
- [ ] Data migration scope confirmed.
- [ ] Branding assets collected.

### Platform Setup

- [ ] Create tenant.
- [ ] Add domain/subdomain.
- [ ] Configure plan and entitlements.
- [ ] Configure branding.
- [ ] Configure timezone/locale.
- [ ] Create tenant admin.

### Academic Setup

- [ ] Import schools/departments.
- [ ] Import programmes.
- [ ] Import courses.
- [ ] Create semesters/intakes.
- [ ] Configure grading scale.
- [ ] Configure registration rules.

### Admissions Setup

- [ ] Configure application form.
- [ ] Configure required documents.
- [ ] Configure intakes.
- [ ] Configure review roles.
- [ ] Configure email templates.
- [ ] Test applicant flow.

### Go-Live Checks

- [ ] Login works.
- [ ] Public website works.
- [ ] Admin dashboard works.
- [ ] Student dashboard works.
- [ ] Teacher dashboard works.
- [ ] Enabled modules work (including quiz, gradebook).
- [ ] Disabled modules are blocked.
- [ ] Test report export.
- [ ] Test backup.
- [ ] Confirm support process.

---

# References

- Moodle Workplace multi-tenancy documentation: https://docs.moodle.org/en/Multi-tenancy
- Moodle tenant settings and tenant administration: https://docs.moodle.org/en/Multi-tenancy_Tenants
- django-tenants documentation: https://django-tenants.readthedocs.io/
- PostgreSQL Row-Level Security documentation: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- OWASP Application Security Verification Standard: https://owasp.org/www-project-application-security-verification-standard/
- W3C Web Content Accessibility Guidelines 2.2: https://www.w3.org/TR/WCAG22/
- OpenAPI Specification: https://swagger.io/specification/
- OpenAPI Initiative: https://www.openapis.org/
- 1EdTech Learning Tools Interoperability: https://www.1edtech.org/standards/lti
- OpenID Connect Core: https://openid.net/specs/openid-connect-core-1_0.html

---

## Final Note

The correct path is incremental transformation:

1. Keep AIU working.
2. Add platform foundation.
3. Add tenant context.
4. Convert identity and membership.
5. Convert public branding and academic core.
6. Convert admissions and teaching workflows (including quiz and gradebook).
7. Convert operations and finance.
8. Add enterprise integrations and production readiness.

Do not rebuild the product from zero. The existing portal already contains valuable university workflows including a recently added quiz engine, question bank, gradebook, chatbot infrastructure, and centralized upload security. UMS should package that value into a secure, configurable, tenant-aware SaaS platform.