# AIU Portal — Comprehensive Security Audit Report
**Date:** 2026-07-16  
**Auditor:** Antigravity AI  
**Scope:** Full-stack security review — Django/DRF backend, Next.js frontend, Docker infrastructure, authentication, data privacy, API protection, and file handling.

---

## Overall Security Rating: **B+ (Strong for Internal University Portal)**

The system demonstrates a notably mature security posture for a university portal. Most of the OWASP Top 10 concerns are addressed. There are no catastrophic architectural flaws, but there are several real issues that should be fixed before going fully public-internet-facing.

---

## 🟢 STRENGTHS (What is Done Well)

### 1. Authentication & Token Security
- **JWT with short-lived access tokens (3 minutes)** — excellent. Limits the blast radius of a stolen token.
- **7-day refresh tokens with rotation and blacklisting** after each use — prevents refresh token replay attacks.
- **Absolute session expiry** embedded in the JWT (`session_exp` claim) — even if the refresh token is reused, it cannot outlive the original session window.
- **Disabled profile blocks login immediately**, and also blocks token refresh — strong revocation mechanism.
- **Automated test** verifying these invariants (`test_route_permissions.py`) — the security contract is contractually enforced.

### 2. Route-Level Authorization
- **Every registered API route is covered by a permission test** (`test_every_registered_api_route_has_an_explicit_security_policy`). This test asserts >200 views are classified — no unprotected route can slip in unnoticed.
- Role-based permission classes (`IsStudentRole`, `IsTeacherRole`, `IsAdminRole`, etc.) are well separated and applied consistently.
- The default DRF permission class is `IsActiveUmsUser` — so any missed annotation falls back to "authenticated and active user required", not open.

### 3. Frontend Session Security
- Auth tokens stored in **HttpOnly cookies** (`ums_access`, `ums_refresh`) — not localStorage. Immune to XSS-based token theft.
- Custom CSRF implementation with double-submit cookie pattern (`ums_csrf` cookie + `x-csrf-token` header) — protects state-mutating calls.
- Middleware correctly validates Origin header against trusted list before accepting requests.

### 4. HTTP Security Headers
Both Nginx and Next.js middleware set a comprehensive security header stack:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block` (Nginx) / `0` (Next.js — correct modern approach)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- **Content-Security-Policy** — default-src 'self', frame-ancestors none, object-src none
- **Strict-Transport-Security** (HSTS) set in Next.js: `max-age=63072000; includeSubDomains; preload`

### 5. Rate Limiting (Nginx)
- Login endpoint: **3 requests/minute** (`zone=login`) — strong brute-force protection.
- Token refresh: **10 requests/minute** (`zone=auth_token`) — appropriate.
- General API: **20 req/s** with burst of 20 — reasonable for a university portal.
- DRF-level throttling: `anon: 20/minute`, `user: 200/minute` — defense-in-depth.

### 6. File Upload Security
- `SecureFileSystemStorage` strips directory traversal via `os.path.basename()`.
- Magic-byte detection validates the actual file content matches declared extension (JPEG, PNG, WebP, HEIC).
- Pillow is used with `DecompressionBombWarning` treated as an error — protects against zip-bomb-style image attacks (`MAX_IMAGE_PIXELS = 40,000,000`).
- Content-type verification against extension — cannot upload a PHP/HTML file disguised as a JPEG.

### 7. Audit Logging
- All mutating HTTP methods (POST/PUT/PATCH/DELETE) for `admin` and `executive` prefixes are automatically logged via `AuditActionMiddleware`.
- Sensitive field names (password, secret, token, authorization, cookie) are **automatically redacted** from logs.
- Audit logs are paginated and admin-only accessible.

### 8. Password Policy
- Configurable via admin settings: min/max length, require uppercase, require number.
- Uses Django's built-in validators + custom policy enforcement.
- Password reset tokens are stored as **SHA-256 digests** (not plaintext) — safe if the DB is leaked.
- Reset tokens are single-use and have a TTL (default 60 minutes).

### 9. CORS Configuration
- Explicit whitelist of allowed origins — no wildcard.
- Credentials allowed only for the exact listed origins.

### 10. Docker & Infrastructure
- PostgreSQL and Redis are **not exposed** on any host port — internal Docker network only.
- Celery workers run as unprivileged user `65534:65534` (nobody) — good.
- `DJANGO_DEBUG=False` in production `.env`.
- `POSTGRES_PASSWORD` enforced via Docker Compose `:?` syntax — fails loudly if missing.

---

## 🟡 MEDIUM RISKS (Should Be Fixed)

### M1 — Real Credentials Committed in `.env`
**Severity: Medium-High**

The `.env` file contains live production credentials:
- **Gmail app password** (`gliceqbkwekrbefv`) — line 20
- **Database password** — line 11
- **Django secret key** — line 1

```
EMAIL_HOST_PASSWORD=gliceqbkwekrbefv   # ← Active Gmail App Password
PORTAL_DB_PASSWORD=a047e2548c181e56403bf1ca3a8cb1581238d2718d2b7ad7
```

If this `.gitignore` ever fails (or the repo becomes partially public), these credentials are exposed. The Gmail App Password in particular can be used to **send email as your address** and access account data.

**Action:** Rotate the Gmail App Password. Consider using environment injection via Docker secrets or a secrets manager rather than a `.env` file on disk.

---

### M2 — Chatbot Endpoint is Fully Public (No Auth Required)
**Severity: Medium**

`ChatbotQueryView` has `permission_classes = [AllowAny]`. The chatbot is callable by anyone on the internet without authentication. While the agent logic guards private data (checking `user.is_authenticated`), this creates:
- An **LLM abuse vector** if `CHATBOT_LLM_ENABLED=True` — unauthenticated users can drive LLM API costs.
- A **semantic search vector** — the public chatbot exposes the `retrieve_for_chatbot` pathway with no auth gate.
- A potential **information extraction** surface (public knowledge base queries).

**Action:** Require at minimum an `IsActiveUmsUser` permission or add a dedicated rate limit per-IP for the chatbot endpoint.

---

### M3 — No HSTS Header in Nginx (HTTP-Only Deployment)
**Severity: Medium**

Nginx is configured for **HTTP only** (port 80). The Next.js layer sets an HSTS header, but this only takes effect once a browser reaches HTTPS. Since the system runs on HTTP, HSTS is never actually enforced by the browser. A man-in-the-middle attacker on the same network can intercept sessions in plain text.

**Action:** For any deployment beyond localhost, configure TLS in Nginx with a valid certificate. Use Let's Encrypt (Certbot) or a corporate CA. Update `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `SECURE_SSL_REDIRECT` to `True` in the Django settings.

---

### M4 — Django `super_admin/` Panel is Publicly Accessible via Nginx
**Severity: Medium**

The Django admin at `/super_admin/` is proxied through Nginx with only a `limit_req zone=general` rate limit. The Django admin has its own login but:
- It's accessible from the open internet if the server is public-facing.
- It uses session-based auth while the rest of the app uses JWT — different attack surface.
- No IP allowlist or additional auth layer in Nginx.

**Action:** Consider restricting `/super_admin/` to internal IPs only via `allow`/`deny` in Nginx, or place it behind a VPN. At minimum, enable 2FA for the Django admin.

---

### M6 — Password Maximum Length is Capped at 20 Characters
**Severity: Low-Medium**

The `password_max_length` setting has a hard ceiling of `min(value, 20)` — meaning no password can be longer than 20 characters regardless of admin settings. This is below recommended lengths and prevents use of passphrases.

**Action:** Raise the maximum to at least 72 or 128 characters. Modern Django hashes passwords with PBKDF2 so long passwords don't affect performance.

---

---

## 🔴 NOTABLE OBSERVATIONS (Lower Risk but Worth Noting)

### N1 — `upgrade-insecure-requests` in CSP Without HTTPS
The Content-Security-Policy includes `upgrade-insecure-requests`, which tells browsers to upgrade HTTP to HTTPS. This is harmless now but can cause issues when TLS is added later if not all assets are updated. Keep it — it's future-proofing — but confirm assets load correctly when HTTPS is enabled.

### N2 — `unsafe-inline` in script-src
```
script-src 'self' 'unsafe-inline'
```
`unsafe-inline` reduces the effectiveness of CSP as an XSS mitigation. This is typical for Next.js apps (since inline scripts are used for hydration), but it means CSP does not protect against all XSS scenarios. Consider adding a nonce-based approach if Next.js version supports it.

### N3 — Swagger/OpenAPI Docs Accessible to Admin Only
`SPECTACULAR_SETTINGS` correctly restricts docs to `IsAdminRole`. This is good. However, the `/schema/` and `/docs/` endpoints are in the URL config and accessible if the permission check fails. Verify the `SERVE_PUBLIC = False` and `SERVE_PERMISSIONS` setting is always respected.

### N4 — Redis Has No Password
The Redis instance in Docker Compose has no authentication:
```yaml
command: redis-server --appendonly yes
```
There's no `--requirepass` flag. Redis is only accessible within the Docker network, which mitigates this, but if any container is compromised, Redis (which holds session data, cache, and Celery tasks) is fully open.

**Action:** Add `--requirepass <strong_password>` to the Redis command and update `CELERY_BROKER_URL` and cache URL accordingly.

### N5 — Email in Plaintext Notifications
The password reset email is sent as plain text, which includes the username and a reset link. This is functional but consider adding HTML email with clear formatting and an expiry reminder for better phishing resistance.

### N6 — CORS and HTTP Only
CORS is only configured for `http://` origins. If you move to HTTPS, remember to update `DJANGO_CORS_ALLOWED_ORIGINS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to use `https://` prefixes.

---

## Security Score Breakdown

| Category | Score | Notes |
|---|---|---|
| Authentication & Session | 9/10 | Excellent JWT design; short access tokens; rotation; revocation |
| Authorization / RBAC | 9/10 | Comprehensive role checks; automated test coverage |
| Input Validation | 8/10 | Good file validation; password policy enforced |
| Data Privacy | 8/10 | Media files protected; credentials in .env |
| Transport Security | 5/10 | HTTP-only; no TLS; HSTS ineffective |
| Security Headers | 9/10 | Comprehensive; CSP present; minor unsafe-inline |
| Rate Limiting | 9/10 | Login brute-force protected; layered throttling |
| Infrastructure | 7/10 | Redis no password; super_admin publicly accessible |
| Audit & Logging | 9/10 | Comprehensive audit trail; sensitive field redaction |
| Secrets Management | 7/10 | Live credentials in .env; history cleaned of settings.py creds |

**Overall: 80/100 — B+ (Solid, production-ready internally, needs hardening for public internet)**

---

## Priority Action Plan

| Priority | Issue | Effort |
|---|---|---|
| 🔴 Immediate | Rotate Gmail App Password (M1) | 5 min |
| 🟠 High | Add TLS/HTTPS to Nginx (M3) | 2–4 hrs |
| 🟠 High | Add auth to chatbot endpoint (M2) | 30 min |
| 🟡 Medium | Restrict `/super_admin/` to internal IPs (M4) | 1 hr |
| 🟡 Medium | Add Redis password (N4) | 30 min |
| 🟡 Medium | Raise password max length to 128 (M6) | 30 min |
| 🟢 Low | Remove `unsafe-inline` from CSP (N2) | 1–2 days (Next.js nonce) |
