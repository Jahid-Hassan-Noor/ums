# AIU Portal Dead-Code Cleanup Backlog

Generated: 15 June 2026  
Revalidated: 1 July 2026
Repository: `/Users/mac/Documents/venv/portal`  
Related report: [`../pdf/portal_dead_code_audit_report.pdf`](../pdf/portal_dead_code_audit_report.pdf)  
Status: Revalidated against the current Docker-backed working tree. This documentation refresh did not change application source code.

## Purpose

This document is an organized maintenance backlog for reviewing and eventually removing unused backend and frontend code.

It should be used as a checklist, not as an instruction to delete every listed item immediately. Some items are confirmed dead code; others are reusable design-system primitives or exports that may be intentionally staged for future work.

## Audit Coverage

| Area                                                                                 | Coverage |
| ------------------------------------------------------------------------------------ | -------: |
| Backend Python source files inspected, excluding migrations                          |      338 |
| Backend classes inspected                                                            |      663 |
| Backend functions and methods inspected                                              |    1,696 |
| Backend test methods detected                                                        |      201 |
| Backend test modules with test methods                                               |       32 |
| Django model classes                                                                 |      117 |
| Frontend TSX files inspected                                                         |      357 |
| Frontend TS files included in dependency analysis                                    |       30 |
| Frontend TS/TSX source lines                                                         |   53,079 |
| Next.js `app/**/page.tsx` routes                                                     |      224 |
| First-party backend URL declarations, excluding generated admin CRUD and debug media |      282 |
| Backend syntax errors                                                                |        0 |

## Classification

| Classification              | Meaning                                                                             | Recommended handling                                    |
| --------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Confirmed dead              | Only its declaration exists, no consumer was found, and it is not framework-invoked | Safe candidate for a focused cleanup PR                 |
| High confidence unreachable | No dependency path exists from a production entrypoint                              | Confirm product intent, then remove as a complete group |
| Export cleanup              | Implementation is used, but an exported API is unused                               | Remove only the unnecessary export                      |
| Scaffolded primitive        | Currently unused reusable UI building block                                         | Keep only if there is a documented near-term use        |
| Protected framework code    | Invoked implicitly by Django, DRF, or Next.js                                       | Do not remove based on static-analysis findings         |

## Recommended Cleanup Strategy

Do not combine all cleanup work into one large change. Use small pull requests that can be reviewed and reverted independently.

## Current Worktree Context Added Since the Prior Backlog

The current checkout includes significant source changes beyond the earlier audit baseline:

- New `accountant_app` backend module with accountant role support, subscription plans, payment attempts, gateway settings, webhook/return flow, and subscription-card PDF output.
- New `chatbot_app` backend module and frontend chatbot component with public/private intent handling.
- New frontend accountant zone, role subscription pages, `/payment-return`, and Next.js `/portal-auth` route handlers for HttpOnly-cookie session proxying.
- Centralized `backend/core/upload_security.py` image validation used by applicant, public content, teacher assignment/content, attendance, profile, and related upload paths.
- DRF throttling, JWT refresh rotation/blacklisting, and production-security setting toggles were added.

Because these changes are not yet part of a clean baseline, keep cleanup commits separate from finance/chatbot/security feature commits.

### Suggested Pull Request Sequence

1. **PR 0: Stabilize and commit the current feature work**
   - Keep accountant, subscriptions/payment, chatbot, upload-security, and session-proxy work in coherent feature commits.
   - Run the focused backend tests for the changed apps and a clean frontend lint/typecheck/build pass.
   - Regenerate Graphify after application source changes are finalized.

2. **PR 1: Safe imports, local symbols, and empty modules**
   - Remove confirmed unused imports.
   - Remove unused imports/types/constants inside active TSX files.
   - Decide whether to delete the two empty dashboard modules.

3. **PR 2: Serializer cleanup verification**
   - The previously listed unused serializer candidates are no longer present as exact declaration-only symbols.
   - Keep serializer cleanup as a verification-only PR unless new dead serializers are introduced.

4. **PR 3: Unreachable frontend feature and utility files**
   - Confirm that homepage preview/settings and food/order utilities are abandoned.
   - Delete confirmed abandoned files as complete dependency islands.
   - Run frontend lint, typecheck, and build.

5. **PR 4: Frontend design-system API cleanup**
   - Review unused UI primitives with the design/frontend owner.
   - Remove unnecessary exports before deleting reusable implementations.
   - Delete scaffolded primitives only when no planned screen needs them.

6. **PR 5: Dependency cleanup**
   - Verify configuration-driven package usage.
   - Remove truly unused dependencies.
   - Add currently used but undeclared dependencies.
   - Patch npm advisories and decide whether to replace `mina-scheduler`.

## Definition of Done for Each Cleanup PR

- [ ] Every removed symbol/file has been searched with an exact-word repository search.
- [ ] Dynamic imports, settings dotted paths, decorators, and framework conventions were checked.
- [ ] Related backend or frontend tests pass.
- [ ] API response shapes remain unchanged unless the change is explicitly approved.
- [ ] No migrations are edited merely to remove unused runtime code.
- [ ] Frontend routes still build and render.
- [ ] The cleanup PR contains only one logical cleanup group.
- [ ] The dead-code audit/backlog is updated after merging.

# Phase 1: Safest Cleanup Candidates

## Confirmed Unused Backend Functions

Each function below has exactly one exact-word occurrence across the backend: its declaration.

- [x] Remove `is_malaysia`
  - File: `backend/applicant_app/countries.py`
  - Lines: `202-203`
  - Risk: Low
  - Verification: Search for nationality normalization behavior and run applicant tests.
  - Status: Removed before the 1 July 2026 revalidation.

- [x] Remove `week_date_from_payload`
  - File: `backend/executive_app/course_schedule.py`
  - Lines: `761-763`
  - Risk: Low
  - Verification: Run executive scheduling tests and search for dynamic imports.
  - Status: Removed before the 1 July 2026 revalidation.

- [x] Remove `_active_registration_count`
  - File: `backend/student_app/registration_service.py`
  - Lines: `130-134`
  - Risk: Low
  - Verification: Run course-registration tests.
  - Status: Removed before the 1 July 2026 revalidation.

## Confirmed Unused Backend Imports

- [ ] Remove `re` from `backend/admin_app/management/commands/seed_aiu_organisation.py:1`
- [ ] Remove `date` from `backend/admin_app/management/commands/seed_schedule_samples.py:1`
- [ ] Remove `post_save` from `backend/admin_app/models.py:5`
- [ ] Remove `receiver` from `backend/admin_app/models.py:6`
- [ ] Remove `Profile` from `backend/admin_app/test_route_permissions.py:9`
- [ ] Remove `status` from `backend/applicant_app/views/applicant_staff.py:4`
- [ ] Remove `CourseOffering` from `backend/chatbot_app/tools.py:7`
- [ ] Remove `date` from `backend/executive_app/course_schedule.py:1`
- [ ] Remove `CourseEvaluationResponse` from `backend/executive_app/evaluation_service.py:8`
- [ ] Remove `BookAcquisitionRequest` from `backend/librarian_app/service.py:6`
- [ ] Remove unused `admin_app.models` import from `backend/student_app/results_service.py:11`
- [ ] Remove `AssignmentSubmission` from `backend/student_app/views/student_assignment_submit.py:24`
- [ ] Remove `AssignmentComment` from `backend/teacher_app/assignment_service.py:16`
- [ ] Remove `AssignmentFeedback` from `backend/teacher_app/assignment_service.py:17`
- [ ] Remove `AssignmentRubric` from `backend/teacher_app/assignment_service.py:18`
- [ ] Remove `CourseResourceFolder` from `backend/teacher_app/course_content_service.py:27`

### Important Exception

Do **not** remove `import admin_app.signals` from `AdminAppConfig.ready()` in `backend/admin_app/apps.py:8`.

Although Ruff reports it as unused, the import is intentionally executed for its side effect: registering Django signal receivers.

## Unused Symbols Inside Active Frontend Files

- [ ] `frontend/components/admin/admin-elections-page.tsx`
  - Remove unused imported type: `SchoolSeat`
  - Also review the `react-hooks/exhaustive-deps` warning for `loadData`.

- [ ] `frontend/components/public/public-site.tsx`
  - Remove unused imports: `GraduationCap`, `LogIn`, `MobileSidebar`, `Button`

- [ ] `frontend/components/admin/admin-public-content-page.tsx`
  - Review the `react-hooks/exhaustive-deps` warning for `loadData`.

### Current ESLint Errors Blocking a Green Frontend Gate

- [ ] `frontend/components/admin/admin-academic-directory-page.tsx:182`
  - Fix `react-hooks/set-state-in-effect` around the mount-time `loadData()` call.
  - Also fix the missing dependency warning for `loadData`.

- [ ] `frontend/components/executive/executive-programs-page.tsx:105`
  - Fix `react-hooks/set-state-in-effect` around the mount-time `loadData()` call.

# Empty and Placeholder Code Management

## Empty Backend Modules

- [ ] Review `backend/admin_app/views/dashboard.py`
  - Current state: Zero-byte file.
  - Repository references: None detected.
  - Recommendation: Delete it if no future dashboard view split is planned.

- [ ] Review `backend/executive_app/views/dashboard.py`
  - Current state: Zero-byte file.
  - Repository references: None detected.
  - Recommendation: Delete it if no future dashboard view split is planned.

### Empty Module Policy

Use the following rules when managing empty Python files:

- Keep empty `__init__.py` files when they define a Python package or preserve compatibility.
- Delete empty feature modules when they are unreferenced and have no documented near-term purpose.
- Do not keep empty files merely as reminders. Track future work in an issue or backlog instead.
- Before deleting an empty module, search for its dotted import path in settings, URL configuration, tests, scripts, and deployment configuration.
- If an empty module is intentionally reserved, add a short module docstring explaining the planned ownership and linked issue.

## Former Placeholder Test Module

- [x] `backend/home_app/tests.py`
  - Current state: Active 116-line public content and image-upload validation test module.
  - Recommendation: Keep it. It is no longer a placeholder cleanup candidate.

## Empty Codeblock and Scaffold Policy

Avoid keeping empty functions, placeholder classes, commented-out implementations, or unused scaffold files in production source directories.

Recommended management rules:

1. Track planned work in issues, not empty source files.
2. Keep a scaffold only when work is scheduled and ownership is clear.
3. Add an issue identifier and intended removal/implementation date when intentionally retaining a scaffold.
4. Remove placeholder code before merging if it is not required for the current feature.
5. Prefer failing explicitly with `NotImplementedError` over silently empty behavior when an interface requires a method.
6. Never replace required Django/DRF hooks with empty placeholders merely to satisfy static tools.

# Phase 2: Backend Serializer Cleanup

## Current Status After 1 July 2026 Revalidation

The earlier serializer deletion backlog is now considered **completed or stale**. Exact class-name scans across the backend, excluding migrations and caches, no longer find declaration-only serializer classes in the active serializer modules. `backend/executive_app/serializers.py` is no longer present.

| File                                   | Serializer classes currently present | Exact declaration-only classes | Recommendation                                                             |
| -------------------------------------- | -----------------------------------: | -----------------------------: | -------------------------------------------------------------------------- |
| `backend/admin_app/serializers.py`     |                                   24 |                              0 | Keep; no current declaration-only cleanup candidate.                       |
| `backend/applicant_app/serializers.py` |                                   14 |                              0 | Keep; new upload/scholarship validation paths reference these serializers. |
| `backend/home_app/serializers.py`      |                                    9 |                              0 | Keep; public content and image validation tests cover active usage.        |
| `backend/student_app/serializers.py`   |                                    2 |                              0 | Keep.                                                                      |
| `backend/teacher_app/serializers.py`   |                                    2 |                              0 | Keep.                                                                      |
| `backend/chatbot_app/serializers.py`   |                                    1 |                              0 | Keep; used by `ChatbotQueryView`.                                          |
| `backend/executive_app/serializers.py` |                                    0 |                              0 | Module removed before this revalidation.                                   |

### Serializer Cleanup Recommendation

- Do not use the old 56-class serializer deletion list; it no longer matches the checkout.
- If future serializer cleanup is needed, regenerate candidates with exact-name usage checks and then inspect dynamic imports, nested serializer usage, tests, API docs, and pending branches.
- Prefer explicit serializer fields for sensitive/public APIs and avoid speculative `fields = "__all__"` serializers without a live endpoint or test.

# Phase 3: Entire Unreachable Frontend Files

## Unreachable TSX Files

These eight files have no dependency path from a Next.js production entrypoint.

- [ ] `frontend/components/charts/trend-line-chart.tsx` - 164 lines
- [ ] `frontend/components/ui/combobox.tsx` - 292 lines
- [ ] `frontend/components/ui/dashboard-skeleton.tsx` - 67 lines
- [ ] `frontend/components/ui/input-group.tsx` - 149 lines
- [ ] `frontend/components/ui/loading-state.tsx` - 36 lines
- [ ] `frontend/components/ui/metric-card.tsx` - 39 lines
- [ ] `frontend/components/ui/quick-actions-card.tsx` - 41 lines
- [ ] `frontend/components/ui/select.tsx` - 193 lines

Total: **981 lines**

### Dependency-Island Note

`combobox.tsx` imports `input-group.tsx`, but neither is reachable from live application code. They form an unreachable dependency island.

Recommendation:

- Review `combobox.tsx`, `input-group.tsx`, and `select.tsx` together.
- If no near-term form redesign needs them, remove the entire island in one PR.
- If they are intentionally retained as design-system primitives, document them in a component catalog and add a basic usage/test story.

## Unreachable TypeScript Files

- [x] ~~`frontend/components/utils/media.ts`~~ - **DELETED**
- [x] ~~`frontend/components/utils/status.ts`~~ - **DELETED**
- [x] ~~`frontend/lib/dashboard.ts`~~ - **DELETED**
- [x] ~~`frontend/lib/food-categories.ts`~~ - **DELETED**
- [x] ~~`frontend/lib/homepage-hybrid-preview.ts`~~ - **DELETED**
- [x] ~~`frontend/lib/homepage-settings.ts`~~ - **DELETED**
- [x] ~~`frontend/lib/order-utils.ts`~~ - **DELETED**

Total: **0 lines remaining** (634 lines removed)

Combined unreachable frontend total: **8 files and 981 lines**.

### Product-Intent Review Questions

Before deleting these files, answer:

- Are homepage hybrid preview and homepage settings features intentionally paused?
- Is food-category/order code part of a future canteen feature?
- Are dashboard/chart primitives planned for a redesign?
- Are these files referenced by a separate application, copied build process, or unpublished branch?
- Should any reusable logic be moved into an actively used module instead of deleted?

## Unreachable File Management Recommendation

- Delete abandoned feature files as complete dependency groups.
- Avoid deleting only a leaf file while leaving an unreachable parent or helper island.
- Do not keep large mock-data/configuration files without an active screen.
- If a file is intentionally staged for future work, add a linked issue and a review date.
- Re-run Knip after each deletion group to expose newly unreachable dependencies.

# Phase 4: Frontend Design-System and Export Cleanup

Current Knip revalidation reports 8 unused files, 2 unused runtime dependencies, 1 unused dev dependency, 2 unlisted dependencies, 72 unused exports, 12 unused exported types, and 13 duplicate export forms.

## Unused Component Implementations Inside Active Files

These implementations are currently neither used internally nor imported elsewhere.

### Alert Dialog

- [ ] Review `AlertDialogTrigger`
  - File: `frontend/components/ui/alert-dialog.tsx`
  - Lines: `13-17`

### Avatar

- [ ] Review `AvatarBadge`
- [ ] Review `AvatarGroup`
- [ ] Review `AvatarGroupCount`
  - File: `frontend/components/ui/avatar.tsx`
  - Lines: `57-97`

### Breadcrumb

- [ ] Review `BreadcrumbEllipsis`
  - File: `frontend/components/ui/breadcrumb.tsx`
  - Lines: `95-115`

### Card

- [ ] Review `CardAction`
  - File: `frontend/components/ui/card.tsx`
  - Lines: `53-64`

### Dropdown Menu

- [ ] Review `DropdownMenuPortal`
- [ ] Review `DropdownMenuCheckboxItem`
- [ ] Review `DropdownMenuRadioGroup`
- [ ] Review `DropdownMenuRadioItem`
- [ ] Review `DropdownMenuShortcut`
- [ ] Review `DropdownMenuSub`
- [ ] Review `DropdownMenuSubTrigger`
- [ ] Review `DropdownMenuSubContent`
  - File: `frontend/components/ui/dropdown-menu.tsx`

### Field

- [ ] Review `FieldSet`
- [ ] Review `FieldLegend`
- [ ] Review `FieldContent`
- [ ] Review `FieldTitle`
- [ ] Review `FieldError`
  - File: `frontend/components/ui/field.tsx`

### Sheet

- [ ] Review `SheetClose`
- [ ] Review `SheetFooter`
  - File: `frontend/components/ui/sheet.tsx`

### Sidebar

- [ ] Review `SidebarRail`
- [ ] Review `SidebarSeparator`
- [ ] Review `SidebarGroupAction`
- [ ] Review `SidebarMenuAction`
- [ ] Review `SidebarMenuBadge`
- [ ] Review `SidebarMenuSkeleton`
  - File: `frontend/components/ui/sidebar.tsx`

Estimated total: **27 unused component implementations and approximately 453 lines**.

### Design-System Recommendation

Do not automatically delete reusable UI primitives simply because the current application does not use them.

Choose one of these policies:

1. **Lean application policy:** Keep only components used by current screens.
2. **Maintained design-system policy:** Keep reusable primitives only when documented, tested, and intentionally supported.

Avoid the middle state where unused primitives remain indefinitely without documentation or ownership.

## Used Internally but Unnecessarily Exported

These implementations are active. Only their external export is unused.

- [ ] Stop exporting `PublicHeader` from `frontend/components/public/public-site.tsx`
- [ ] Stop exporting `AlertDialogOverlay` from `frontend/components/ui/alert-dialog.tsx`
- [ ] Stop exporting `AlertDialogPortal` from `frontend/components/ui/alert-dialog.tsx`
- [ ] Stop exporting `buttonVariants` from `frontend/components/ui/button.tsx`
- [ ] Stop exporting `badgeVariants` from `frontend/components/ui/badge.tsx`
- [ ] Stop exporting `TooltipProvider` from `frontend/components/ui/tooltip.tsx`

Recommendation:

- Remove only the export keyword/export-list entry.
- Keep the internal implementation because it is actively used.
- Re-run Knip after each export cleanup.

## Duplicate Named and Default Exports

The following components expose both named and default exports while only one form is consumed:

- [ ] `AuthCornerHeader`
- [ ] `Header`
- [ ] `Shell`
- [ ] `BaseStatusModal`
- [ ] `ErrorModal`
- [ ] `InfoModal`
- [ ] `SuccessModal`
- [ ] `WarningModal`
- [ ] `ForgotPasswordForm`
- [ ] `LoadingScreen`
- [ ] `NotificationsButton`
- [ ] `ResetPasswordForm`
- [ ] `StatusCard`

Recommendation:

- Standardize on named exports for reusable components.
- Use default exports only where Next.js requires them, such as route pages/layouts.
- Migrate imports first, then remove the unused export form.
- Avoid changing all export styles in one unrelated cleanup PR.

## Unused Library Exports

Review whether these symbols are used internally before deleting their implementations.

### `frontend/lib/auth.ts`

- [ ] `normalizeRole`
- [ ] `getStoredSession`
- [ ] `sendEmailVerificationRequest`
- [ ] `verifyEmailRequest`

### `frontend/lib/apply.ts`

- [ ] `applyLogin`

### `frontend/lib/api-base.ts`

- [ ] `resolveApiBase`

### `frontend/lib/countries.ts`

- [ ] `isMalaysianNationality`

### `frontend/lib/portal-roles.ts`

- [ ] `PORTAL_ROLES`
- [ ] `parsePortalRole`
- [ ] `isPortalRole`

### `frontend/hooks/use-theme.ts`

- [ ] `THEME_STORAGE_KEY`
- [ ] `getPreferredTheme`
- [ ] `applyTheme`

### `frontend/components/utils/format.ts`

- [ ] `formatNumber`
- [ ] `formatCampaignItemQuantity`
- [ ] `formatCampaignAvailability`
- [ ] `formatCurrency`
- [ ] `DEFAULT_DATE_TIME_OPTIONS`

### `frontend/lib/aiu-public-data.ts`

- [ ] `publicNavLinks`
- [ ] `applyLinks`
- [ ] `governanceGroups`
- [ ] `portalRoles`
- [ ] `publicDetailPageMap`

## Unused Exported Types

- [ ] `AdminApplicantSummary`
- [ ] `ReportExportRecord`
- [ ] `SettingChoice`
- [ ] `PublicLink`
- [ ] `ApplyIntake`
- [ ] `ApplyProgramme`
- [ ] `ApplyStatusEvent`
- [ ] `PortalMetric`
- [ ] `PublicDepartment`
- [ ] `ScheduleVariant`
- [ ] `ScheduleCategory`
- [ ] `ScheduleTemplate`

Recommendation:

- If a type is used only inside its defining file, remove `export` but keep the type.
- Delete the type only when it has no internal or external usage.

# Phase 5: Dependency Review

## Apparently Unused Dependencies

- [ ] `react-aria`
- [ ] `react-icons`

## Apparently Unused Development Dependency

- [ ] `@eslint/eslintrc`

## Used but Undeclared Dependencies

- [ ] Add or otherwise resolve `server-only`
- [ ] Add or otherwise resolve `postcss-load-config`

## Dependency Security and Compatibility Findings

- [ ] `npm audit --omit=dev --audit-level=high` reports 12 vulnerabilities: 1 low, 8 moderate, and 3 high.
- [ ] High-severity audit buckets include `next`, `fast-uri`, and `hono`.
- [ ] `qrcode.react@4.2.0` is installed in the frontend container.
- [ ] `npm ls qrcode.react next mina-scheduler uuid --depth=2` still fails with `ELSPROBLEMS` because `mina-scheduler@1.0.4` declares a Next `^14.0.0` peer while the application uses Next `16.2.4`.
- [ ] `mina-scheduler` also pulls `uuid@10.0.0`, which is covered by a moderate npm advisory with no direct fix through that dependency chain.

Recommendation:

- Verify dependency usage in configuration files, dynamic imports, build scripts, and transitive package behavior.
- Remove one dependency group at a time.
- Run `npm install`, lint, typecheck, development startup, and production build after package changes.

# Protected Framework Code: Do Not Remove

The following categories may be reported as unused by generic tools but are required:

- Django migration `Migration` classes, `dependencies`, `operations`, and `schema_editor`.
- Django management command `Command` classes, `help`, and `handle`.
- Django model fields, `Meta`, constraints, indexes, and `clean()`.
- DRF `permission_classes`, `parser_classes`, HTTP methods, serializer `validate*`, and `get_*` methods.
- Django signal receivers and their `sender` arguments.
- Middleware loaded by dotted path from settings.
- `import admin_app.signals` inside `AppConfig.ready()`.
- Test classes and `setUp`/`tearDown`.
- Next.js route, layout, loading, and error exports.

# Current Verification Status

Commands were run against the Docker containers rather than a host virtual environment.

- [x] `docker exec portal_backend python manage.py check`
- [x] `docker exec portal_backend python manage.py test accountant_app.tests chatbot_app.tests`
- [x] `docker exec portal_frontend npm run typecheck`
- [ ] `docker exec portal_frontend npm run lint`
  - Current result: 2 errors and 8 warnings.
  - Blocking errors are `react-hooks/set-state-in-effect` in `admin-academic-directory-page.tsx` and `executive-programs-page.tsx`.
- [ ] `docker exec portal_frontend npm audit --omit=dev --audit-level=high`
  - Current result: 12 vulnerabilities.
- [ ] `docker exec portal_frontend npm ls qrcode.react next mina-scheduler uuid --depth=2`
  - Current result: `qrcode.react@4.2.0` is installed, but `mina-scheduler` has an invalid Next peer range.
- [ ] `docker exec portal_backend python -m ruff ...`
  - Current result: Ruff is not installed in the backend image. The revalidation used `uvx ruff check backend --exclude '*/migrations/*' --select F401 --output-format concise`.

# Suggested Verification Commands

## Backend

```bash
docker exec portal_backend python manage.py check
docker exec portal_backend python manage.py test admin_app.tests
docker exec portal_backend python manage.py test applicant_app.tests
docker exec portal_backend python manage.py test student_app.tests
docker exec portal_backend python manage.py test teacher_app.tests
docker exec portal_backend python manage.py test executive_app.tests
docker exec portal_backend python manage.py test accountant_app.tests chatbot_app.tests
uvx ruff check backend --exclude '*/migrations/*' --select F401 --output-format concise
```

Run narrower tests when cleaning only one app.

## Frontend

```bash
docker exec portal_frontend npm run lint
docker exec portal_frontend npm run typecheck
docker exec portal_frontend npm run build
docker exec portal_frontend npx knip --include-entry-exports
docker exec portal_frontend npm audit --omit=dev --audit-level=high
```

# Maintenance Recommendations

## Preventing New Backend Dead Code

- Add Ruff unused-import checks to CI.
- Run a Django-aware Vulture/dead-code review periodically, not as an automatic deletion tool.
- Require a current consumer or test for newly introduced serializers and service helpers.
- Avoid speculative `ModelSerializer(fields="__all__")` classes.
- Remove obsolete code in the same PR that removes its final caller.

## Preventing New Frontend Dead Code

- Run ESLint with unused-variable warnings treated as CI failures.
- Run Knip in CI or on a scheduled maintenance workflow.
- Standardize component export style.
- Keep a documented design-system inventory if reusable unused primitives are intentionally supported.
- Remove abandoned mock data and preview modules when their feature is cancelled.

## Ownership Recommendation

Assign cleanup ownership by domain:

| Domain                                                                   | Suggested owner               |
| ------------------------------------------------------------------------ | ----------------------------- |
| Backend serializers and service helpers                                  | Backend/API maintainer        |
| Empty view modules and placeholder tests                                 | Relevant Django app owner     |
| Public/homepage unused files                                             | Public-site frontend owner    |
| Canteen food/order utilities                                             | Canteen feature owner         |
| Shared UI primitives and exports                                         | Frontend/design-system owner  |
| Package dependencies, npm advisories, and `mina-scheduler` compatibility | Frontend platform/build owner |

## Final Recommendation

First stabilize and commit the current accountant/subscription, chatbot, upload-security, and session-proxy work. Then start cleanup with Phase 1 unused imports and lint errors because they have the smallest behavioral risk. Treat unreachable frontend files and design-system primitives as product decisions. Keep the serializer phase as a revalidation checkpoint unless new declaration-only serializers appear.
