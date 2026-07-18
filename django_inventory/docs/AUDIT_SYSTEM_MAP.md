---
id: audit-system-map
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# AUDIT_SYSTEM_MAP — Production Readiness Audit · Phase 01 (System Mapping)

> **⚠️ DATED SNAPSHOT (2026-06-14)** — historical audit artifact, NOT a living
> map. The system has moved since (PDD stream R1→A360, pre-R10 polish, freeze
> closeout C-1..C-3 2026-07-05: retro-tag removed, single My-Dashboard, live
> access predicate everywhere). Current truth: [PROJECT_KNOWLEDGE_MAP.md](PROJECT_KNOWLEDGE_MAP.md)
> + app GUIDEs. Kept for the audit record only.

**Generated:** 2026-06-14 · **Branch:** new_flask_app · **Scope:** complete inventory of sidebar items, URLs, pages, actions, forms, workflows, handlers, services.

**Method:** 9 parallel read-only mapping agents (one per app + nav/RBAC + infra). Read-only — no code changed.

## 0. System Totals

| App | URL prefix | URLs | Views | Services | Forms | Templates |
|-----|-----------|-----:|------:|---------:|------:|----------:|
| accounts | `/app/` | 23 | 23 | 3 | 5 | 20 |
| inventory | `/inventory/` | 8 | 8 | 1 | 1 | 12 |
| tracking | `/tracking/` | 12 | 12 | 2 | 0 | 7 |
| Production (config.production) | `/production/` | 68 | 68 | 13 | 16 | 43 |
| raw_materials | `/raw-materials/` | 22 | 22 | 2 | 6 | 11 |
| expense (Payroll / Worker Earnings) | `/expense/` | 9 | 9 | 9 | 3 | 8 |
| storefront | `/storefront/` | 9 | 9 | 1 | 5 | 8 |
| **TOTAL** | | **151** | **151** | **31** | **36** | **109** |

Plus: `core` (abstract base models, no tables), `storefront.public_home` mounted at `/`, Django admin at `/admin/`, allauth at `/accounts/`.

---

## 1. Per-App Inventory

### accounts  (`/app/`)

**URLs (23)**

| Pattern | Name | View | Methods |
|---------|------|------|---------|
| `""` | `login` | LoginView | GET, POST |
| `verify-otp/` | `verify_otp` | VerifyOTPView | GET, POST |
| `resend-otp/` | `resend_otp` | ResendOTPView | GET |
| `login/password/` | `login_password` | PasswordLoginView | GET, POST |
| `home/` | `home` | HomeView | GET |
| `logout/` | `logout` | LogoutView | POST |
| `signup/` | `signup` | SignupView | GET, POST |
| `signup/verify/` | `signup_verify` | SignupVerifyView | GET, POST |
| `signup/resend-otp/` | `signup_resend_otp` | ResendSignupOTPView | GET |
| `forgot-password/` | `forgot_password` | ForgotPasswordView | GET, POST |
| `reset-password/verify/` | `reset_password_verify` | ResetPasswordVerifyView | GET, POST |
| `users/` | `user_list` | UserListView | GET |
| `users/add/` | `user_add` | UserCreateView | GET, POST |
| `users/<int:pk>/edit/` | `user_edit` | UserUpdateView | GET, POST |
| `users/<int:pk>/delete/` | `user_delete` | UserDeleteView | GET, POST |
| `skills/` | `skill_list` | SkillListView | GET |
| `skills/add/` | `skill_add` | SkillCreateView | GET, POST |
| `skills/<int:pk>/edit/` | `skill_edit` | SkillUpdateView | GET, POST |
| `skills/<int:pk>/delete/` | `skill_delete` | SkillDeleteView | GET, POST |
| `user-types/` | `usertype_list` | UserTypeListView | GET |
| `user-types/add/` | `usertype_add` | UserTypeCreateView | GET, POST |
| `user-types/<int:pk>/edit/` | `usertype_edit` | UserTypeUpdateView | GET, POST |
| `user-types/<int:pk>/delete/` | `usertype_delete` | UserTypeDeleteView | GET, POST |

**Views (23)**

| View | Kind | File | Purpose |
|------|------|------|---------|
| LoginView | View | accounts/views.py | Step 1: email entry for OTP login; only sends OTP to existing users (account enumeration protection). |
| ResendOTPView | View | accounts/views.py | Resend login OTP after cooldown; mirrors LoginView logic for account enumeration defense. |
| VerifyOTPView | View | accounts/views.py | Step 2: 6-digit OTP verification to complete login; rate-limited with max 3 attempts per OTP. |
| LogoutView | View (POST-only) | accounts/views.py | POST-only logout with never_cache decorator and explicit Cache-Control headers for CSRF protection. |
| HomeView | LoginRequiredMixin View | accounts/views.py | Protected entry point with role-based landing: management (super_admin/manager) → Operations dashboard, others → My Dashboard. |
| PasswordLoginView | DjangoLoginView subclass | accounts/views.py | Fallback password-based login; throttled per IP+email; prefills email on reset success. |
| UserListView | ListView (Super Admin only) | accounts/views.py | List all users with search (name/email) and skill filtering; includes KPI counts (total/active/inactive); no server-side pagination due to PostgreSQL MVCC volatility. |
| UserCreateView | CreateView (Super Admin only) | accounts/views.py | Super Admin creates new user with full profile, role, and skills; no production side-effects (C-1 2026-07-05: retro-tag removed). |
| UserUpdateView | UpdateView (Super Admin only) | accounts/views.py | Edit user profile; enforces self-edit blockers (no self-demotion/deactivation); syncs skills; updates session if editing self with new password. |
| UserDeleteView | DeleteView (Super Admin only) | accounts/views.py | Delete user via user_service.delete_user; enforces self-delete and last-admin invariants with advisory lock. |
| SignupView | FormView | accounts/views.py | Public self-registration step 1: email+password; signs password with SECRET_KEY before session storage (not plain text); throttled. |
| SignupVerifyView | View | accounts/views.py | Step 2: OTP verification for signup; creates User on success; catches IntegrityError for race-condition email duplicates. |
| ResendSignupOTPView | View | accounts/views.py | Resend signup verification OTP with cooldown check. |
| ForgotPasswordView | View | accounts/views.py | Password reset step 1: email entry; always shows same message regardless of email existence (anti-enumeration). |
| ResetPasswordVerifyView | View | accounts/views.py | Step 2: OTP+new password in one form; validates password with all Django validators; resets all throttles on success; prefills email for login. |
| SkillListView | ListView (Super Admin only) | accounts/views.py | List all skills ordered by name. |
| SkillCreateView | CreateView (Super Admin only) | accounts/views.py | Create new skill (name/label/description). |
| SkillUpdateView | UpdateView (Super Admin only) | accounts/views.py | Edit existing skill. |
| SkillDeleteView | DeleteView (Super Admin only) | accounts/views.py | Delete skill. |
| UserTypeListView | ListView (Super Admin only) | accounts/views.py | List all user types ordered by label. |
| UserTypeCreateView | CreateView (Super Admin only) | accounts/views.py | Create new user type (code/label/description/is_active). |
| UserTypeUpdateView | UpdateView (Super Admin only) | accounts/views.py | Edit existing user type. |
| UserTypeDeleteView | DeleteView (Super Admin only) | accounts/views.py | Delete user type; blocks deletion if users are assigned to it. |

**Services (3)**

- **`auth_service`** — OTP issuance for all login/signup/password-reset flows; centralizes generate→store→email logic to prevent copy-paste drift.  
  _Key:_ issue_otp(request, *, email, prefix, subject) → bool: Generate 6-digit OTP, hash+store in session, email to recipient; returns True on success (email send failure returns False for caller to handle).
- **`user_service`** — Single home for write-side User invariants: self-edit blocking, last-admin deletion protection (race-safe with PG advisory lock), (C-1 2026-07-05: retro-tag removed; accounts has zero production edges).  
  _Key:_ delete_user(user_to_delete, *, actor) → None: Delete user with self-delete + last-admin checks; race-safe via pg_advisory_xact_lock; raises ValidationError on refusal.; self_edit_blockers(actor, *, new_is_superuser, new_is_active, new_role) → list[str]: Pure function; returns list of blocked actions (empty=allowed) for a Super Admin editing their own profile.; count_active_admins(*, exclude_pk=None) → int: Count active Super Admins (is_superuser OR role.code==super_admin); used by delete_user.; sync_user_skills(user) → int: Retro-tag user onto active Layering rosters for their current skills (replaces old m2m_changed signal); lazy-imports production.services to avoid circular imports.
- **`permission_service`** — RBAC core: role-based access control, permission helpers, sidebar menu registry + visibility rules, and role editor sections.  
  _Key:_ user_role_code(user) → str \| None: Return user's primary role code (is_superuser → ROLE_SUPER_ADMIN, else user.role.code).; user_role_codes(user) → set[str]: Return all role codes for user (primary + extra_roles).; user_has_role(user, codes: Iterable[str]) → bool: True if any of user's roles is in codes.; user_has_perm(user, perm_codename) → bool: Full permission check: is_superuser/ROLE_SUPER_ADMIN bypass → role-perm lookup → Django default.; user_can_view_financials(user) → bool: Gate for reading Supplier + Cost Per KG fields.; user_can_edit_financials(user) → bool: Gate for writing Supplier + Cost Per KG fields.; user_principal(user) → dict: Request-cached {role_ids, skill_ids} for the user (computed once per request).; build_menu_for(user, current_path) → list[dict]: Return sidebar sections filtered to user's visible items; applies 3-layer visibility (Super Admin bypass → SidebarItemRule DB → in-code predicate); picks single 'is_active' item by longest match.; can_access_url_name(user, url_name) → bool: Check if user can open page; mirrors sidebar visibility logic (same SidebarItemRule rules).; explain_visibility(user, url_name) → str: Diagnostic explanation of why user can/can't see an item.; permissions_qs_by_app(app_labels) → list: Return Permission queryset restricted to ROLE_EDITABLE_CONTENT_TYPES (curated allowlist).; permissions_sectioned_for_role_editor() → list: Return [(section_label, section_desc, [(model_label, [perm, ...]), ...]), ...].

**Forms (5)**

| Form | Model | Purpose |
|------|-------|---------|
| UserTypeForm | UserType | Create/edit UserType from UI; fields: code (slug), label, description, is_active. |
| SkillForm | Skill | Create/edit Skill from UI; fields: name (slug), label, description. |
| UserEditForm | User | Super Admin edits existing user; optional new_password field (stays as-is if blank); enforces email uniqueness excluding self; validates password with Django validators. |
| UserCreateForm | User | Super Admin creates new user with full profile; password + confirm_password fields; validates early so admins see form errors instead of 500; saves with set_password(). |
| SignupForm | none (plain Form) | Public self-registration; email + password + confirm_password; does NOT check email existence (anti-enumeration; duplicate handled in SignupVerifyView via IntegrityError catch). |

**Workflows (4)**

- OTP-based login flow: LoginView (email) → VerifyOTPView (OTP) → login + redirect to HomeView
- Signup flow: SignupView (email+password) → SignupVerifyView (OTP) → User.create_user() → auto-login
- Password reset flow: ForgotPasswordView (email) → ResetPasswordVerifyView (OTP+new password) → user.set_password() → redirect to login
- User management: UserListView (search/filter) → UserCreateView (new user) or UserUpdateView (edit) or UserDeleteView (with guards)

**Templates (20):** `accounts/base.html`, `accounts/login.html`, `accounts/otp.html`, `accounts/login_password.html`, `accounts/signup.html`, `accounts/signup_otp.html`, `accounts/forgot_password.html`, `accounts/reset_otp.html`, `accounts/home.html`, `accounts/user_list.html`, `accounts/user_create.html`, `accounts/user_form.html`, `accounts/_user_form_styles.html`, `accounts/user_confirm_delete.html`, `accounts/skill_list.html`, `accounts/skill_form.html`, `accounts/skill_confirm_delete.html`, `accounts/usertype_list.html`, `accounts/usertype_form.html`, `accounts/usertype_confirm_delete.html`

**Auditor notes:** CRITICAL AUDIT FINDINGS:

1. RATE LIMITING & THROTTLE:
   - All auth endpoints (OTP send/verify, password login, signup) are throttled via throttle.py cache-backed system.
   - Two-axis tracking: per IP + per identifier (email). Limits tuned for internal team app, NOT public site.
   - Blocks activate after N hits in sliding window; block duration prevents brute force.
   - check_throttle() called near top of every POST auth view; reset_throttle() on success (self-lockout protection).
   - All account-enumeration vectors mitigated: LoginView/ForgotPasswordView show same message for non-existent emails; SignupForm does NOT validate email existence.

2. OTP SECURITY:
   - 6-digit OTP from secrets.randbelow() (cryptographically secure).
   - SHA-256 hashed before session storage (plain OTP never persisted).
   - Verified with hmac.compare_digest() (timing-side-channel resistant).
   - 5-min expiry (OTP_EXPIRY_SECONDS=300); 3 attempt max per OTP (OTP_MAX_ATTEMPTS=3).
   - 1-min resend cooldown (OTP_RESEND_COOLDOWN=60).

3. USER MODEL CUSTOMS:
   - Custom User model (USERNAME_FIELD='email', no username field).
   - Three identity concepts: UserType (display only, not RBAC), Skill (production work classification), Role (FK to accounts.Role, RBAC source of truth).
   - CRITICAL: Never gate access on user_type — Role does that (enforced throughout).
   - M2M relationships: skills, extra_roles (stacks on primary role for additional access).
   - DB indexes: (is_active, role) for RBAC queries.
   - Constraints: salary >= 0 (CheckConstraint + validator).

4. RBAC & PERMISSION CONTROL:
   - Role model: named bundles of Django Permissions; is_system flag prevents deletion of admin/manager/worker.
   - SidebarItemRule: per-menu-item role visibility, DB-backed override for in-code sidebar predicate.
   - Five defined role codes: ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_WORKER, ROLE_LISTING_TEAM, ROLE_ACCOUNTANT.
   - Permission checks: 1. is_superuser → grant all, 2. role.code == ROLE_SUPER_ADMIN → grant all, 3. role.permissions, 4. Django default.
   - Sidebar build: 3-layer precedence: Super Admin bypass → SidebarItemRule DB → in-code MenuItem predicate.
   - All views use permission_service helpers, NOT raw is_superuser (CLAUDE.md rule #6).

5. USER MANAGEMENT (SUPER ADMIN ONLY):
   - self_edit_blockers(): blocks Super Admin from revoking own superuser flag, deactivating self, or changing own RBAC role away from Super Admin in one request (self-lockout protection).
   - delete_user(): enforces "must not delete self" + "must not delete last active Super Admin"; race-safe via pg_advisory_xact_lock(0x4B41444D='KADM').
   - UserListView: no server-side paginate_by (PostgreSQL MVCC UPDATE shifts rows out of first-N window, breaking pagination); client-side DataTables instead; includes KPI counts (total/active/inactive).
   - UserUpdateView: optional password change (new_password field); update_session_auth_hash() if editing self with new password; skill sync retro-tags onto active Layerings.

6. PASSWORD SECURITY:
   - All password creation/reset uses Django's AUTH_PASSWORD_VALIDATORS (min length 8, no common/all-numeric, similarity check).
   - Signup: password signed with django.core.signing (reversible by SECRET_KEY only) before session storage.
   - Reset: password validation + user.set_password() + Django default Argon2 hasher.
   - Edit: optional new_password; clean_new_password validates against user instance for similarity.

7. CROSS-APP INTEGRATION:
   - sync_user_skills(user): retro-tags user onto active Layering rosters when skills change (replaces old m2m_changed signal).
   - Lazy-imported from production.services to avoid circular imports (P4.1, intentionally kept lazy).
   - Called explicitly from: UserCreateView.form_valid(), UserUpdateView.form_valid(), UserAdmin.save_related().
   - NO other signals in accounts (CLAUDE.md rule #4: no signals).

8. MISSING/EMPTY FILES:
   - allauth_adapters.py exists (not read in detail; handles django-allauth integration if present).
   - apps.py, admin.py are minimal.
   - No services for Role/Skill (admin-managed from UI via forms; no service invariants).

9. ROLE EDITOR SECTIONS (CURATED ALLOWLIST):
   - 5 logical sections: Production Flow, Raw Materials, Tracking, Storefront, Administration.
   - Many models excluded (service-only writes): AddaStageRecord, LayeringRollEntry, CuttingRecord, *History, etc.
   - Exposed only to Super Admin via inventory:role_list view.

10. TRANSITIONAL / KNOWN CODE:
    - SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER constants in skills.py; user_has_skill() gates stage transitions.
    - Skill.get_name_display() back-compat shim (replaces old Django choices display).
    - Role editor section structure curated manually to prevent "80+ perms noise" in UI.
    - UserListView comment: "no ORDER BY → undefined row order + MVCC shift on UPDATE → pagination breaks" (documented 2026-05-20).

11. VIEW-LAYER SECURITY:
    - All views use LoginRequiredMixin, SuperuserRequiredMixin (via permission_service, not raw is_superuser).
    - LogoutView: POST-only with never_cache + explicit Cache-Control headers (CSRF + browser cache protection).
    - HomeView: role-based landing (Management → Operations, others → My Dashboard) fixes owner-lands-on-empty-worker view (Phase-C C-1).
    - LoginView: account enumeration defense (same redirect for non-existent emails; session email set regardless).

12. SESSION & CSRF:
    - OTP flows: per-prefix session keys (otp_email, signup_email, reset_email) + per-prefix OTP storage (otp_hash, otp_created_at, otp_attempts, otp_last_sent_at).
    - Signup: password stored as signed token (django.core.signing) not plain text.
    - LogoutView: GET redirects to home (logout must be POST for CSRF protection).

13. THROTTLE LIMITS (from throttle.py):
    - otp_send: 20/10min per IP, 5/10min per email, 15min block.
    - otp_verify: 30/10min per IP, 10/10min per email, 30min block.
    - pw_login: 20/10min per IP, 5/15min per email, 30min block (tightest).
    - signup: 10/10min per IP, 3/15min per email, 15min block.

---

### inventory  (`/inventory/`)

**URLs (8)**

| Pattern | Name | View | Methods |
|---------|------|------|---------|
| `dashboard/` | `inventory_dashboard` | inventory.views.dashboard | GET |
| `my-dashboard/` | `user_dashboard` | inventory.views.user_dashboard | GET |
| `roles/` | `role_list` | inventory.views.RoleListView | GET |
| `roles/add/` | `role_add` | inventory.views.RoleCreateView | GET, POST |
| `roles/<int:pk>/edit/` | `role_edit` | inventory.views.RoleUpdateView | GET, POST |
| `roles/<int:pk>/delete/` | `role_delete` | inventory.views.RoleDeleteView | GET, POST |
| `sidebar-access/` | `sidebar-access` | inventory.views.SidebarAccessListView | GET, POST |
| `access/` | `access-control` | inventory.views.AccessControlHubView | GET |

**Views (8)**

| View | Kind | File | Purpose |
|------|------|------|---------|
| dashboard | FBV (Function-Based View) | /home/tech/umesh-personal/django_inventory/config/inventory/views/dashboard.py | Role-aware dashboard for management users; displays active Addas, active stages, and helper stats; decorated with @login_required. |
| user_dashboard | FBV (Function-Based View) | /home/tech/umesh-personal/django_inventory/config/inventory/views/dashboard.py | Non-management dashboard URL; renders the same unified template as dashboard() with is_admin_view flag for future role-based sections. |
| RoleListView | ListView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/role_views.py | Super Admin only; lists all Role objects ordered by name; prefetches permissions and users M2M relations. |
| RoleCreateView | CreateView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/role_views.py | Super Admin only; creates new Role with RoleForm; passes permissions_sectioned_for_role_editor() context for checkbox grid. |
| RoleUpdateView | UpdateView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/role_views.py | Super Admin only; edits existing Role; passes selected_perm_ids set for fast template checkbox selection. |
| RoleDeleteView | DeleteView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/role_views.py | Super Admin only; deletes Role after validation (system roles + assigned roles blocked); shows error flash messages. |
| SidebarAccessListView | TemplateView (CBV) with POST | /home/tech/umesh-personal/django_inventory/config/inventory/views/sidebar_access_views.py | Super Admin only; renders SidebarItemRule items grouped by section as role/skill checkboxes; POST handler bulk-upserts rules (atomic transaction). |
| AccessControlHubView | TemplateView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/access_hub_views.py | Super Admin only; read-only RBAC overview with 4 matrices: Roles×Sidebar Pages, Skills/Roles×Production Stages, Users roster, Roles summary; deep-links to edit pages. |

**Services (1)**

- **`inventory.services (re-export shim)`** — RBAC gateway — re-exports all role/permission checks from accounts.services.permission_service so existing ~38 import sites remain unchanged after 2026-06 relocation to accounts app.  
  _Key:_ user_has_role(user, codes: set[str]) -> bool — primary RBAC gate; user_role_code(user) -> str\|None — returns user's role code or 'super_admin' if superuser; user_role_codes(user) -> set[str] — returns all role codes (primary + extra_roles); user_has_perm(perm_codename: str) -> bool — checks Django permission with role/super_admin bypass; user_principal(user) -> dict — request-cached user role_ids + skill_ids for sidebar + stage access; build_menu_for(user, path) -> list — filters SIDEBAR menu items per user's roles/skills; can_access_url_name(user, url_name: str) -> bool — checks SidebarItemRule override or in-code predicate; permissions_sectioned_for_role_editor() -> dict — groups all editable Django permissions by app for role form; Role constants: ROLE_SUPER_ADMIN, ROLE_MANAGER, ROLE_WORKER, ROLE_LISTING_TEAM, ROLE_ACCOUNTANT; Role sets: ADMIN_ROLES, MANAGEMENT_ROLES, PRODUCTION_ROLES, FINANCIAL_ROLES, STOREFRONT_ROLES

**Forms (1)**

| Form | Model | Purpose |
|------|-------|---------|
| RoleForm | accounts.models.Role | ModelForm for Role CRUD; multi-select permissions field filtered by ROLE_EDITABLE_APPS + ROLE_EDITABLE_MODELS_EXCLUDED exclusions; validates that system role codes cannot change; auto-adds form-control CSS to all fields. |

**Workflows (4)**

- Role lifecycle (Admin workflow): Create Role → Assign Permissions → Grant to Users; accessible from /roles/ UI.
- Sidebar Access Control workflow (Admin workflow): View /sidebar-access/ → Toggle role/skill checkboxes per menu item → Bulk save; enforced by SidebarAccessMiddleware at request time.
- Dashboard onboarding workflow (User workflow): Dashboard (main entry) → My Active Stages (assigned tasks) → Skilled Accordion (production work) or Status Card (non-skilled) → Action buttons on stages.
- Access Control matrix exploration (Audit workflow): AccessControlHubView shows 4 read-only matrices; Super Admin can click deep-links to edit Role, SidebarItemRule, Stage access, or User Teams without leaving the Hub.

**Templates (12):** `inventory/user_dashboard.html — Main dashboard; hero greeting, My Active Stages (role-aware badges), Skilled accordion (iframe inline panels), Helper Stats (cutting_master_helper only), My Recent Activity cross-Adda timeline, Adda pipeline state.`, `inventory/dashboard.html — Likely a redirect or alias; structure unclear from grep; kept for backward compatibility.`, `inventory/role_list.html — Displays Role table with pagination; includes name, code, description, permission count, user count, action buttons (Edit/Delete); system roles locked.`, `inventory/role_form.html — Role create/edit form; name/code/description fields, large permissions checkbox grid sectioned by app, submit/cancel buttons.`, `inventory/role_confirm_delete.html — Delete confirmation page; warns of system roles + assigned users; cancel button to list view.`, `inventory/access_control.html — Read-only RBAC matrix page; 4 sections (Roles×Sidebar, Skills/Roles×Stages, Users roster, Roles summary); deep-links to edit pages.`, `inventory/sidebar_access_list.html — SidebarItemRule editor; items grouped by section (Main, Storefront, Raw Materials, Production, Tracking, Administration) with role/skill checkboxes per item; bulk save.`, `inventory/_adda_events_accordion.html — Partial template for Adda event accordion (used in user_dashboard).`, `inventory/_roll_events_accordion.html — Partial template for roll event accordion.`, `inventory/_time_log_styles.html — Shared CSS styles for time-related logs/tables.`, `inventory/_nav_icon.html — Partial for sidebar nav icons.`, `inventory/_section_icon.html — Partial for section-header icons.`

**Auditor notes:** [
  "CRITICAL: Role + SidebarItemRule models were relocated from inventory.models to accounts.models in 2026-06. inventory.models.py now re-exports them (import shim) for backward compatibility. All references (Role, SidebarItemRule) live in accounts.models; inventory.services re-exports permission functions so existing imports remain valid.",
  "RBAC Architecture: 3-layer system: (1) Role objects in DB (bundles of Django Permissions per user); (2) Permission constants + role-code rules in permission_service; (3) In-code SIDEBAR registry filtered per request.",
  "Access Control: Super Admin role always grants full access (hardcoded bypass at service layer). Every non-admin check goes through user_has_role() + role.permissions M2M + SidebarItemRule override.",
  "Security: SidebarAccessMiddleware enforces permission_service.can_access_url_name() at request time for all SidebarItemRule-managed URLs; denied requests get flash message + redirect to dashboard (or previous accessible page). Exempt URLs (both dashboards) never blocked to prevent redirect loops.",
  "Middleware + Context Processor: SidebarAccessMiddleware (process_view) + sidebar context processor (build_menu_for) work in tandem: processor filters menu at render; middleware blocks URLs at request.",
  "Dashboard Role-Aware Sections: dashboard() + user_dashboard() call shared _build_dashboard_context() which includes: (a) is_skilled_user = has cutting skill OR management role (drives accordion vs status card); (b) my_active_stages with report badges (submitted/draft/needed); (c) helper_data for cutting_master_helper only; (d) my_activity cross-Adda timeline; (e) active_addas filtered by isolation rule (workers see only assigned, management sees all).",
  "Production Integration: Dashboard gracefully degrades if production tables not migrated (try-except wraps production imports). Production app owns Adda/Stage/WorkerStageTask; inventory just displays in dashboard.",
  "Role Deletion Protection: System roles (is_system=True) + roles with assigned users cannot be deleted (form_valid check + redirect with error message).",
  "Permission Sectioning: permissions_sectioned_for_role_editor() organizes all editable Django Permissions by app_label for role form checkbox groups; excludes specific models via ROLE_EDITABLE_MODELS_EXCLUDED tuple.",
  "SidebarItemRule Override: DB rules override in-code SIDEBAR predicates for managed items. Unmanaged items (new features, perm-only gates) fall back to in-code predicate. If rules table is empty (fresh install), all items use in-code predicates.",
  "User-Type vs Role vs Skill: User.user_type = display/classification ONLY (never gates access). User.role = primary RBAC role. User.extra_roles = M2M for stacking additional access. User.skills = M2M for production-stage work capability (separate from RBAC).",
  "No feature flags or conditional code paths detected in inventory app (production-adjacent features are toggled via role/skill gates, not feature flags).",
  "Tracking app (tracking_*.py, tracking_urls.py) is excluded from this audit per instructions — owned separately (P4.2)."
]

---

### tracking  (`/tracking/`)

**URLs (12)**

| Pattern | Name | View | Methods |
|---------|------|------|---------|
| `/tracking/` | `dashboard` | inventory.views.tracking_dashboard.BarcodeDashboardView | GET |
| `/tracking/barcodes/<str:adda_code>/` | `barcode-list` | inventory.views.tracking_barcodes.BarcodeListForAddaView | GET |
| `/tracking/barcodes/<str:adda_code>/print/` | `barcode-print` | inventory.views.tracking_barcodes.BarcodePrintSheetView | GET |
| `/tracking/barcodes/<str:adda_code>/export/` | `barcode-export` | inventory.views.tracking_dashboard.barcode_export_csv | GET |
| `/tracking/scan/<str:value>/` | `scan` | inventory.views.tracking_barcodes.scan_piece | POST |
| `/tracking/history/roll/<int:roll_pk>/` | `roll-history` | inventory.views.tracking_history.RollHistoryView | GET |
| `/tracking/history/adda/<str:adda_code>/` | `adda-history` | inventory.views.tracking_history.AddaHistoryView | GET |
| `/tracking/exports/` | `export-list` | inventory.views.tracking_exports.ExportListView | GET |
| `/tracking/exports/<str:adda_code>/csv/` | `export-csv` | inventory.views.tracking_exports.ExportCSVView | POST |
| `/tracking/exports/<str:adda_code>/xlsx/` | `export-xlsx` | inventory.views.tracking_exports.ExportXLSXView | POST |
| `/tracking/exports/<str:adda_code>/pdf/` | `export-pdf` | inventory.views.tracking_exports.ExportPDFView | POST |
| `/tracking/exports/<str:export_code>/download/` | `export-download` | inventory.views.tracking_exports.ReDownloadView | GET |

**Views (12)**

| View | Kind | File | Purpose |
|------|------|------|---------|
| BarcodeDashboardView | TemplateView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_dashboard.py | Dashboard listing all Addas with barcode counts (pending/packed/dispatched/missing), filterable by date range |
| barcode_export_csv | FBV @login_required | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_dashboard.py | Legacy CSV export endpoint for quick download without manifest tracking (back-compat pre-completion path) |
| BarcodeListForAddaView | TemplateView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_barcodes.py | Per-Adda barcode batch summary table with piece counts and scanned state |
| BarcodePrintSheetView | TemplateView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_barcodes.py | A4 print sheet of QR codes with configurable size (small/medium/large) and optional status filter |
| scan_piece | FBV @login_required @transaction.atomic | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_barcodes.py | QR scan landing endpoint that resolves barcode via BarcodeBatch, lazy-creates BatchBarcode row, timestamps last_scanned_at/by |
| RollHistoryView | TemplateView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_history.py | ClothRoll audit timeline with RBAC: management sees all, workers only rolls on their assigned Addas |
| AddaHistoryView | TemplateView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_history.py | Adda stage transitions + state changes audit log with RBAC isolation (workers see only assigned Addas) |
| ExportListView | ListView (CBV) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_exports.py | Global recent-exports dashboard (paginated 50/page) showing all barcode export batches |
| ExportCSVView | View (CBV POST-only) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_exports.py | POST trigger to generate CSV export, creates BarcodeExportBatch manifest, gates on barcode_generation stage completion |
| ExportXLSXView | View (CBV POST-only) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_exports.py | POST trigger to generate XLSX export, creates BarcodeExportBatch manifest, gates on barcode_generation stage completion |
| ExportPDFView | View (CBV POST-only) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_exports.py | POST trigger to generate PDF summary export, creates BarcodeExportBatch manifest, gates on barcode_generation stage completion |
| ReDownloadView | View (CBV GET-only) | /home/tech/umesh-personal/django_inventory/config/inventory/views/tracking_exports.py | Re-download existing export by export_code, regenerates from live barcode data (audit-safe re-delivery) |

**Services (2)**

- **`barcode_service`** — Per-piece scan state, QR rendering, and barcode value parsing/resolution without production imports (R1 §8 boundary compliance)  
  _Key:_ parse_value(value: str) → tuple[adda_code, seq] or None; resolve_value(value: str) → tuple[BarcodeBatch, seq] or None; get_or_create_piece(batch, seq) → BatchBarcode [idempotent, atomic]; mark_status(user, barcode_value, status) → BatchBarcode [atomic, status update]; qr_data_uri(barcode_or_value, base_url, box_size) → data URI PNG [ECC-Q, ISO18004 quiet zone]
- **`history_service`** — Single-writer audit log entries following CLAUDE.md §5 ledger pattern (no signals, no model overrides, only service calls)  
  _Key:_ log_roll(roll, change_type, actor, field_name, old_value, new_value, note) → ClothRollHistory; log_adda(adda, change_type, actor, stage_from, stage_to, roll, note, metadata, stage_record) → AddaHistory; log_product(product, change_type, actor, field_name, old_value, new_value) → ProductHistory

**Templates (7):** `tracking/barcode_dashboard.html`, `tracking/barcode_list.html`, `tracking/barcode_print_sheet.html`, `tracking/export_list.html`, `tracking/scan_detail.html`, `tracking/history/adda_history.html`, `tracking/history/roll_history.html`

**Auditor notes:** ARCHITECTURAL NOTES:

1. OWNERSHIP & NAMESPACE PRESERVATION (P4.2, Jun 2026):
   - Views live in inventory.views.tracking_* (inventory-owned, production-isolation)
   - URL namespace 'tracking:' is preserved (all templates + reverse() calls unchanged)
   - Routing: config/urls.py → path('tracking/', include('inventory.tracking_urls'))
   - Models + services remain in tracking/ app (tracking.models, tracking.services)

2. NO FORMS:
   - Tracking app has zero Form/ModelForm classes. All data mutations via service layer (barcode_service.mark_status) or production stage handlers.

3. NO SIDEBAR CONTRIBUTIONS:
   - Tracking does not register SidebarItemRule entries. Access via /tracking/ root URL or via Adda detail drill-down links from production app.

4. DATA MODELS (4 core tables):
   a) BarcodeBatch: Range header (contiguous seq blocks per color/size combo). One-shot bulk creation from Cutting stage (CuttingPieceBreakup).
   b) BatchBarcode: Per-piece scan state (lazy-created on first scan). Frozen denorm: size, color, pattern, roll FKs. Status ∈ {pending, packed, dispatched, missing}.
   c) ClothRollHistory: ClothRoll audit (ChangeType: created/status_changed/location_moved/weight_updated/archived). FieldChangeMixin for old/new values.
   d) AddaHistory: Adda lifecycle audit (ChangeType: created/stage_advanced/stage_reopened/status_changed/roll_assigned/roll_removed/completed/cost_frozen/stage_started/workers_assigned/bundle_created/barcodes_generated/exported/settlement_finalized/settlement_reversed/settlement_superseded). stage_from/stage_to FK, stage_record FK, metadata JSONField for event-specific payload.
   e) ProductHistory: Product field-level edits (ChangeType: created/updated/archived). FieldChangeMixin.
   f) BarcodeExportBatch: Manifest header for barcode exports (CSV/XLSX/PDF). Frozen at creation: total_labels denorm. Re-download idempotent (regenerates from live BarcodeBatch data). export_code unique (EXP-YYYY-NNN format, race-safe SELECT FOR UPDATE counter).

5. RBAC ENFORCEMENT:
   - All views gate on PRODUCTION_ROLES (accounts.services.user_has_role check).
   - History views (RollHistoryView, AddaHistoryView) add secondary isolation:
     * Management (MANAGEMENT_ROLES) → see all
     * Workers (non-management) → only Addas/Rolls they are actively assigned to (WorkerStageTask check, exclude CANCELLED status).
   - scan_piece: Fixed in RBAC review (2026-06-02) — added PRODUCTION_ROLES gate (was bare @login_required, allowed office/normal users to stamp audit fields).

6. SINGLE-WRITER PATTERN:
   - History tables (ClothRollHistory/AddaHistory/ProductHistory) written ONLY via history_service.log_*() functions.
   - NO signal handlers, NO model.save() overrides, NO view-side direct .create().
   - Enforces audit trail integrity (CLAUDE.md §5 rule).

7. BARCODE GENERATION & EXPORT LIFECYCLE:
   - BarcodeBatch rows created by production.stages.barcode_generation.assembly.generate_for_cutting() — not in tracking.
   - BarcodeExportBatch rows created by production.stages.barcode_generation.export_service.generate_{csv,xlsx,pdf}() — manifest layer ensures stage-completion gate.
   - Service functions moved to production.stages (P4.2) to keep tracking app import-pure (no production dependencies).

8. LAZY BARCODE PIECE CREATION (PR6, 2026-05-28):
   - BarcodeBatch: range header (small O(N) storage per Adda). 500-piece Adda ≈ 5 batches, not 500 rows.
   - BatchBarcode: created on first scan via get_or_create_piece(). Untouched pieces have no DB row (range covered by BarcodeBatch).
   - Lookup: parse_value(value) → resolve_value() queries BarcodeBatch range (start_seq ≤ seq ≤ end_seq) ∈ O(1).

9. SCAN ATOMICITY (AUDIT FIX, 2026-05-29):
   - scan_piece() wrapped in @transaction.atomic.
   - get_or_create_piece() itself atomic (internal).
   - Post-create, select_for_update() lock applied to serialize parallel scans on same piece.
   - last_scanned_at/by update atomically in same transaction (no race window for concurrent stamp + status interleave).

10. QR SPECIFICATION:
    - Format: {BASE_URL}/tracking/scan/{ADDA}-{SEQ:04d}/ (e.g. T-SHIRT-001-0042)
    - ECC level Q (25% damage tolerance — sticker soiled/torn still scannable).
    - 4-module quiet zone per ISO 18004.
    - Rendered via qr_data_uri() → PNG base64 data URI (no storage).
    - BarcodePrintSheetView offers 3 sizes: small (54/page, 22mm), medium (35/page, 30mm), large (24/page, 42mm).

11. EXPORT MANIFEST (PR-D, 2026-05-29):
    - BarcodeExportBatch row created per export trigger. export_code unique (race-safe via SELECT FOR UPDATE).
    - total_labels denormalized + frozen at creation (audit invariant). Re-download regenerates file bytes (idempotent).
    - Service layer gates on barcode_generation stage completion (prevents pre-completion export).
    - Legacy barcode_export_csv endpoint (FBV) skips manifest creation (quick-download path, pre-completion diagnostics).

12. TRANSITIONAL NOTES:
    - Legacy batches (pre-PR6) have NULL batch_id on BatchBarcode rows. get_or_create_piece() defensively populates batch FK if missing.
    - Legacy NIKKAR-style Addas (single-batch, no breakup metadata) have NULL color/size on BarcodeBatch. New barcodes populate all 4 denorm FKs (size/color/pattern/roll).
    - ProductHistory.FieldChangeMixin inherits from core.models (shared base).

13. MODELS PROTECTION:
    - BarcodeBatch.adda: on_delete=PROTECT (Adda delete blocked if barcode batches exist).
    - BatchBarcode.adda: on_delete=PROTECT (Adda delete blocked if barcodes scanned).
    - BarcodeBatch.bundle: on_delete=PROTECT (nullable for legacy, null=True).
    - BarcodeExportBatch.adda: on_delete=PROTECT (export audit critical).
    - History FKs: on_delete=PROTECT (except stage_record which is SET_NULL to preserve audit on rare stage-record delete).

14. QUERY OPTIMIZATION:
    - BarcodeDashboardView uses Sum('barcode_batches__total_pieces') to avoid N+1 on piece counts.
    - Conditional Count via filter=Q(...) for per-status breakdowns in single query.
    - scan_piece uses select_related(adda, product, color, size) on resolve_value() BarcodeBatch fetch.
    - History views use select_related(actor, stage_from, stage_to, roll, roll__cloth_type, roll__cloth_color) to avoid N+1 on timeline renders.

15. KNOWN ISSUES / AUDITOR ALERTS:
    - barcode_export_csv FBV (legacy endpoint) has no manifest row; production.stages.barcode_generation.export_service._render_csv_bytes() imported inline (hidden dependency).
    - History access gates rely on WorkerStageTask.status != CANCELLED check (worker lifecycle sync point).
    - roll__cloth_type + roll__cloth_color denormalization in AddaHistoryView needed because template displays roll metadata (no JOIN, but manual pre-fetch overhead).

---

### Production (config.production)  (`/production/`)

**URLs (68)**

| Pattern | Name | View | Methods |
|---------|------|------|---------|
| `` | `dashboard` | AddaDashboardView | GET |
| `stalled/` | `stalled-addas` | StalledAddaListView | GET |
| `pending-reports/` | `pending-reports` | PendingReportListView | GET |
| `costing/` | `costing` | ProductionCostingView | GET |
| `products/` | `product-list` | ProductListView | GET |
| `products/add/` | `product-create` | ProductCreateView | GET,POST |
| `products/<int:pk>/edit/` | `product-update` | ProductUpdateView | GET,POST |
| `products/<int:pk>/archive/` | `product-archive` | ProductArchiveView | GET,POST |
| `products/<int:pk>/flow/` | `product-flow` | ProductFlowEditView | GET,POST |
| `products/<int:pk>/patterns/` | `product-patterns` | ProductPatternsEditView | GET,POST |
| `products/<int:pk>/sizes/` | `product-sizes` | ProductSizesEditView | GET,POST |
| `patterns/` | `pattern-list` | ProductPatternListView | GET |
| `patterns/add/` | `pattern-add` | ProductPatternCreateView | GET,POST |
| `patterns/<int:pk>/edit/` | `pattern-edit` | ProductPatternUpdateView | GET,POST |
| `patterns/<int:pk>/delete/` | `pattern-delete` | ProductPatternDeleteView | GET,POST |
| `addas/` | `adda-list` | AddaListView | GET |
| `addas/start/` | `adda-create` | AddaCreateView | GET,POST |
| `addas/<str:code>/` | `adda-detail` | AddaDetailView | GET |
| `addas/<str:code>/stage-rates/` | `stage-rates` | StageRateListView | GET |
| `addas/<str:code>/stage-rates/<int:sr_id>/<int:role_id>/correct/` | `stage-rate-correct` | StageRateCorrectView | GET,POST |
| `addas/<str:code>/stage/<str:stage_type>/` | `stage-panel` | StagePanelView | GET |
| `addas/<str:code>/report/<str:stage_type>/` | `worker-report` | WorkerReportView | GET,POST |
| `addas/<str:code>/review-reports/` | `adda-report-review` | AddaReportReviewView | GET,POST |
| `addas/<str:code>/layering/` | `layering-workspace` | LayeringWorkspaceView | GET |
| `addas/<str:code>/layering/start/` | `layering-start` | LayeringStartView | POST |
| `addas/<str:code>/layering/attach-roll/` | `layering-attach-roll` | LayeringAttachRollView | POST |
| `addas/<str:code>/layering/quick-create-roll/` | `layering-quick-create-roll` | LayeringQuickCreateAndAttachView | POST |
| `addas/<str:code>/layering/full-create-roll/` | `layering-full-create-roll` | LayeringFullCreateAndAttachView | POST |
| `addas/<str:code>/layering/entries/<int:pk>/` | `layering-entry-update` | LayeringEntryUpdateView | POST |
| `addas/<str:code>/layering/entries/<int:pk>/remove/` | `layering-entry-remove` | LayeringEntryRemoveView | POST |
| `addas/<str:code>/layering/remaining/<int:pk>/remove/` | `layering-remove-remaining` | LayeringRemoveRemainingClothView | POST |
| `addas/<str:code>/layering/complete/` | `layering-complete` | LayeringCompleteView | POST |
| `addas/<str:code>/layering/reopen/` | `layering-reopen` | LayeringReopenView | POST |
| `addas/<str:code>/pattern/` | `pattern-workspace` | PatternWorkspaceView | GET |
| `addas/<str:code>/pattern/start/` | `pattern-start` | PatternStartView | POST |
| `addas/<str:code>/pattern/save/` | `pattern-save` | PatternSaveVideoView | POST |
| `addas/<str:code>/pattern/photos/add/` | `pattern-photos-add` | PatternAddPhotoView | POST |
| `addas/<str:code>/pattern/photos/<int:pk>/remove/` | `pattern-photo-remove` | PatternRemovePhotoView | POST |
| `addas/<str:code>/pattern/verify/` | `pattern-verify` | PatternVerifyView | POST |
| `addas/<str:code>/pattern/unverify/` | `pattern-unverify` | PatternUnverifyView | POST |
| `addas/<str:code>/pattern/sizes/` | `pattern-set-sizes` | PatternSetSizesView | POST |
| `addas/<str:code>/pattern/complete/` | `pattern-complete` | PatternCompleteView | POST |
| `addas/<str:code>/pattern/reopen/` | `pattern-reopen` | PatternReopenView | POST |
| `addas/<str:code>/cutting/` | `cutting-complete` | CuttingCompleteView | GET,POST |
| `addas/<str:code>/cutting/workspace/` | `cutting-workspace` | CuttingWorkspaceView | GET |
| `addas/<str:code>/cutting/start/` | `cutting-start` | CuttingStartView | POST |
| `addas/<str:code>/cutting/breakup/save/` | `cutting-breakup-save` | CuttingBreakupSaveView | POST |
| `addas/<str:code>/cutting/breakup/<int:pk>/delete/` | `cutting-breakup-delete` | CuttingBreakupDeleteView | POST |
| `addas/<str:code>/cutting/bundle/create/` | `cutting-bundle-create` | CuttingBundleCreateView | POST |
| `addas/<str:code>/cutting/bundle/<int:pk>/add-item/` | `cutting-bundle-add-item` | CuttingBundleAddItemView | POST |
| `addas/<str:code>/cutting/bundle/<int:pk>/add-pieces/` | `cutting-bundle-add-pieces` | CuttingBundleAddPiecesView | POST |
| `addas/<str:code>/cutting/bundle/item/save/` | `cutting-bundle-item-save` | CuttingBundleItemSaveView | POST |
| `addas/<str:code>/cutting/bundle/item/<int:pk>/delete/` | `cutting-bundle-item-delete` | CuttingBundleItemDeleteView | POST |
| `addas/<str:code>/cutting/bundle/<int:pk>/delete/` | `cutting-bundle-delete` | CuttingBundleDeleteView | POST |
| `addas/<str:code>/cutting/bundle/item/<int:pk>/allocate/` | `cutting-item-allocate` | CuttingBundleItemAllocateView | POST |
| `addas/<str:code>/cutting/allocation/<int:pk>/delete/` | `cutting-allocation-delete` | CuttingAllocationDeleteView | POST |
| `addas/<str:code>/cutting/draft/` | `cutting-draft` | CuttingDraftView | POST |
| `addas/<str:code>/cutting/workspace/complete/` | `cutting-workspace-complete` | CuttingWorkspaceCompleteView | POST |
| `addas/<str:code>/cutting/reopen/` | `cutting-reopen` | CuttingReopenView | POST |
| `addas/<str:code>/barcode-gen/` | `barcode-gen-workspace` | BarcodeGenWorkspaceView | GET |
| `addas/<str:code>/barcode-gen/start/` | `barcode-gen-start` | BarcodeGenStartView | POST |
| `addas/<str:code>/barcode-gen/generate/` | `barcode-gen-generate` | BarcodeGenGenerateView | POST |
| `addas/<str:code>/barcode-gen/complete/` | `barcode-gen-complete` | BarcodeGenCompleteView | POST |
| `addas/<str:code>/barcode-gen/reopen/` | `barcode-gen-reopen` | BarcodeGenReopenView | POST |
| `stages/` | `stage-list` | StageListView | GET |
| `stages/add/` | `stage-add` | StageCreateView | GET,POST |
| `stages/<int:pk>/edit/` | `stage-edit` | StageUpdateView | GET,POST |
| `stages/<int:pk>/delete/` | `stage-delete` | StageDeleteView | GET,POST |

**Views (68)**

| View | Kind | File | Purpose |
|------|------|------|---------|
| AddaDashboardView | TemplateView | views/dashboard.py | KPI dashboard (in_progress/on_hold/completed counts, stage breakdown, recent Addas, operations digest for management) |
| StalledAddaListView | TemplateView | views/dashboard.py | Management drill-down for stalled Addas (H-2B); worker isolation applies (non-mgmt see only their assigned stages) |
| PendingReportListView | TemplateView | views/dashboard.py | Management drill-down for pending worker reports (F-3); worker isolation (non-mgmt see only their queue) |
| ProductionCostingView | TemplateView | views/costing_views.py | Manufacturing cost rollup dashboard (management only); per-Adda cost, pieces, worker earnings, margin gap, unpriced surfaces |
| ProductListView | ListView | views/product_views.py | Product catalog list (management only); filterable by status/code |
| ProductCreateView | CreateView | views/product_views.py | Create new Product (Super Admin only); seeds Layering stage auto-attach; normalizes code format |
| ProductUpdateView | UpdateView | views/product_views.py | Edit Product name/description (Super Admin only); code locked after creation |
| ProductArchiveView | View | views/product_views.py | Archive/soft-delete Product (POST confirmation); prevents new Adda creation; existing Addas unaffected |
| ProductFlowEditView | TemplateView | views/flow_views.py | Per-Product workflow stage editor (Super Admin only); add/remove/reorder stages, set cost method and rate per stage |
| ProductPatternsEditView | TemplateView | views/pattern_views.py | Per-Product pattern assignment editor; add/remove/update pieces_count for ProductPatternAssignment rows |
| ProductSizesEditView | TemplateView | views/product_views.py | Per-Product size chart editor (PR5); add/remove/update/reactivate ProductSize rows |
| ProductPatternListView | ListView | views/pattern_views.py | Reusable pattern library list (perm-gated); shows pattern name, code, reference image, usage count |
| ProductPatternCreateView | CreateView | views/pattern_views.py | Create reusable ProductPattern (code, name, reference image); code locked after creation |
| ProductPatternUpdateView | UpdateView | views/pattern_views.py | Edit ProductPattern name/description (code locked); perm-gated |
| ProductPatternDeleteView | DeleteView | views/pattern_views.py | Delete ProductPattern (refuses if assigned to products); perm-gated |
| AddaListView | ListView | views/adda_views.py | Filterable Adda batch list (status/stage_type); paginated 50/page; select_related + prefetch optimizations |
| AddaCreateView | FormView | views/adda_views.py | One-click Adda creation from Product picker; calls create_adda service (atomic counter increment, auto-layering bootstrap) |
| AddaDetailView | DetailView | views/adda_views.py | Central Adda dashboard (tabbed by stage); pre-renders all stages server-side; JS toggles visibility; per-stage RBAC gate; activity feed; stage snapshots |
| StageRateListView | TemplateView | views/rate_views.py | Per-Adda stage role-rates list (S1.1, super-admin only); shows locked/settled status; links to correction form |
| StageRateCorrectView | FormView | views/rate_views.py | Correct per-(stage_record, role) rate before settlement; reasons audit trail; auto-recalc unsettled earnings (S1.1) |
| StagePanelView | TemplateView | views/stage_views.py | Unified embedded panel for ANY stage (layering/cutting/pattern/barcode-gen); shared _build_*_context pattern; ?embedded=1 strips chrome for iframe; @xframe_options_sameorigin |
| WorkerReportView | View | views/worker_report_views.py | Schema-driven worker self-report form (V2-1c-iii pt.2b); GET=render (editable or locked), POST=save draft or submit; object-level isolation (own task only) |
| AddaReportReviewView | View | views/worker_report_views.py | Management quantity review/correction before settlement (P1/F5-lite); shows reported vs verified; read-only contributions, write verified_quantity |
| LayeringWorkspaceView | TemplateView | views/stage_views.py | Layering stage full-page workspace (GET only); shows roll picker, entries, remaining cloth, breakup summary; skill-gated via StageViewAccessMixin |
| LayeringStartView | View | views/stage_views.py | POST action: manager assigns workers to Layering stage; calls start_layering service |
| LayeringAttachRollView | View | views/stage_views.py | POST action: attach cloth roll with verified width/weight; filters picker by color/type/width; calls attach_roll_to_layering service |
| LayeringQuickCreateAndAttachView | View | views/stage_views.py | POST action: inline create + attach roll (qty=1); bulk_create_rolls (raw_materials) + attach_roll_to_layering in one shot; bypasses picker |
| LayeringFullCreateAndAttachView | View | views/stage_views.py | POST action: full roll creation form (purchase date, cost fields) + attach; delegates to raw_materials bulk_create_rolls + attach_roll_to_layering |
| LayeringEntryUpdateView | View | views/stage_views.py | POST action: edit verified width/weight/notes on LayeringRollEntry OR quick per-row layer-count save (via layers_on_roll mini-form) |
| LayeringEntryRemoveView | View | views/stage_views.py | POST action: detach roll from layering (entry deleted, ClothRoll back to NOT_USED status) |
| LayeringRemoveRemainingClothView | View | views/stage_views.py | POST action: delete leftover/remaining cloth entry (only if not yet consumed in cutting) |
| LayeringCompleteView | View | views/stage_views.py | POST action: finalize layering + advance to next stage; iframe-safe redirect (stage-panel?embedded=1&advanced=1 if from iframe) |
| LayeringReopenView | View | views/stage_views.py | POST action: management unlock completed Layering stage (guards prevent if scanned/exported); same iframe-safe redirect |
| PatternWorkspaceView | TemplateView | views/pattern_stage_views.py | Cutting-pattern stage full-page workspace (GET only); shows video/photos, verification checklist, size allocations; skill-gated |
| PatternStartView | View | views/pattern_stage_views.py | POST action: manager assigns workers to cutting-pattern stage; calls start_pattern_stage service |
| PatternSaveVideoView | View | views/pattern_stage_views.py | POST action: upload/replace pattern video + notes (multipart); optional video, optional notes; AJAX-aware (auto-save debounce) |
| PatternAddPhotoView | View | views/pattern_stage_views.py | POST action: attach one or more photos to pattern record (multipart name='photos[]'); lazily bootstraps CuttingPatternRecord |
| PatternRemovePhotoView | View | views/pattern_stage_views.py | POST action: detach photo (uploader or management only, locked if stage completed); deletes file from storage |
| PatternVerifyView | View | views/pattern_stage_views.py | POST action: verify pattern assignment (toggle ON); links optional photo + verification note |
| PatternUnverifyView | View | views/pattern_stage_views.py | POST action: remove pattern verification (toggle OFF) |
| PatternSetSizesView | View | views/pattern_stage_views.py | POST action: full-replace size allocations (proportion_pct per size); multi-row form; sum != 100 ok at draft, enforced at complete |
| PatternCompleteView | View | views/pattern_stage_views.py | POST action: finalize cutting-pattern (verifications complete, sizes sum=100) + advance; same iframe-safe redirect |
| PatternReopenView | View | views/pattern_stage_views.py | POST action: management unlock completed pattern stage; same iframe-safe redirect |
| BarcodeGenWorkspaceView | TemplateView | views/barcode_gen_views.py | Barcode Generation stage workspace (GET only); shows barcodes preview, generated batches, counts; skill-gated |
| BarcodeGenStartView | View | views/barcode_gen_views.py | POST action: manager assigns workers (cutting_master/helper) to barcode generation stage |
| BarcodeGenGenerateView | View | views/barcode_gen_views.py | POST action: one-shot trigger BarcodeBatch creation from breakdown (PR-C); race-guarded (IntegrityError → informative message) |
| BarcodeGenCompleteView | View | views/barcode_gen_views.py | POST action: validate barcode counts match breakdown + advance; same iframe-safe redirect; management/helper-skill gate |
| BarcodeGenReopenView | View | views/barcode_gen_views.py | POST action: management unlock barcode generation (refuses if scanned/exported); same iframe-safe redirect |
| CuttingCompleteView | View | views/stage_views.py | Legacy single-form cutting complete (back-compat); GET=render form, POST=validate pieces_cut + submit |
| CuttingWorkspaceView | TemplateView | views/stage_views.py | Cutting stage workspace (PR3); shows breakup rows, bundles, allocations, barcode preview; skill-gated |
| CuttingStartView | View | views/stage_views.py | POST action: manager assigns workers to cutting stage |
| CuttingBreakupSaveView | View | views/stage_views.py | POST action: save/upsert per-(size, color, pattern) breakup rows; multi-row form arrays |
| CuttingBreakupDeleteView | View | views/stage_views.py | POST action: delete breakup row (refuses if bundles already created from it) |
| CuttingBundleCreateView | View | views/stage_views.py | POST action: create new cutting bundle (header with size); PR8 schema two-step flow |
| CuttingBundleAddItemView | View | views/stage_views.py | POST action: add one item (pattern + color + count) to bundle |
| CuttingBundleAddPiecesView | View | views/stage_views.py | POST action: multi-select consume from breakup rows into bundle (PR10 bulk-add) |
| CuttingBundleItemSaveView | View | views/stage_views.py | POST action: update bundle item (pattern/color/count inline edit) |
| CuttingBundleItemDeleteView | View | views/stage_views.py | POST action: delete bundle item row (reverses consumption if needed) |
| CuttingBundleDeleteView | View | views/stage_views.py | POST action: delete entire bundle (refunds items back to breakup pool) |
| CuttingBundleItemAllocateView | View | views/stage_views.py | POST action: allocate bundle item to worker (era-A SWA creation via expense.allocate_stage_work); LEVER-gated (V2-3) |
| CuttingAllocationDeleteView | View | views/stage_views.py | POST action: void worker allocation (expense.void_allocation); removes SWA link and unfreezes item |
| CuttingDraftView | View | views/stage_views.py | POST action: save draft (notes, breakup, bundles) without completing stage |
| CuttingWorkspaceCompleteView | View | views/stage_views.py | POST action: finalize cutting workspace (from bundles path) + advance to next stage; iframe-safe redirect |
| CuttingReopenView | View | views/stage_views.py | POST action: management unlock completed cutting stage; same iframe-safe redirect |
| StageListView | ListView | views/access_views.py | Global Stage library list (Super Admin only); shows stage code, name, access (skills/roles), is_active, usage in products |
| StageCreateView | CreateView | views/access_views.py | Create new Stage (code, name, description, access_by_skill M2M, access_by_role M2M); Super Admin only |
| StageUpdateView | UpdateView | views/access_views.py | Edit Stage (name/description/access chips); code locked after creation (service-level lookups depend on it) |
| StageDeleteView | DeleteView | views/access_views.py | Delete Stage (refuses if in any Product flow); Super Admin only |

**Services (13)**

- **`adda_service`** — Adda lifecycle (create with atomic per-product counter, bootstrap Layering, advance to next stage)  
  _Key:_ create_adda(user, product) → Adda; advance_to_next_stage(adda) → None
- **`product_service`** — Product CRUD (create with auto-Layering seed, update name/description, archive)  
  _Key:_ create_product(user, code, name, description) → Product; update_product(user, product, name, description) → Product; archive_product(user, product) → None
- **`product_size_service`** — Per-product size chart management (add, archive, reactivate, update)  
  _Key:_ add_product_size(user, product, code) → ProductSize; archive_product_size(user, size) → None; reactivate_product_size(user, size) → None; update_product_size(user, size, label, display_order) → ProductSize
- **`flow_service`** — Product workflow stage management (add/remove/reorder stages, set cost method and rate, validate monotonicity)  
  _Key:_ add_stage_to_product_flow(user, product, stage) → WorkflowStage; remove_stage_from_product_flow(user, workflow_stage) → None; move_stage_in_product_flow(user, workflow_stage, direction) → None; set_stage_cost(user, workflow_stage, cost_method, cost_rate, cost_billed_at_id) → None; set_stage_grain(user, workflow_stage, allocation_dimensions) → WorkflowStage
- **`access_service`** — Stage access control (reads Stage model access_by_skill/access_by_role; super_admin/manager hardcoded grant)  
  _Key:_ user_can_access_stage(user, stage_code) → bool; stage_access_map(user, stage_codes) → dict[str, bool]
- **`activity_service`** — Per-user, per-Adda activity timeline (unified event feed from AddaHistory, ClothRollHistory, LayeringRollEntry, AddaStageRecord)  
  _Key:_ adda_activity(adda, limit=50) → list[ActivityEvent]; user_activity_across_addas(user, limit=50) → list[ActivityEvent]
- **`operations_digest`** — Management morning pulse (6 tiles: stalled Addas, pending reports, active Addas, completed today, pending payable, advance exposure)  
  _Key:_ operations_digest() → dict; stalled_stage_records() → QuerySet; pending_report_tasks() → QuerySet
- **`cost_service`** — Stage cost management (freeze, clear)  
  _Key:_ clear_stage_cost(user, workflow_stage) → None
- **`worker_task_service`** — SOLE writer of WorkerStageTask + WorkerStageContribution (V2-1 → V2-3); reported_quantity immutable, verified_quantity management-correctable  
  _Key:_ set_stage_workers(stage_record, worker_ids, cancel_note) → None; add_stage_worker(stage_record, worker_id) → None; save_draft_contributions(task, lines, actor) → None; complete_worker_task(task, actor) → None; set_verified_quantity(contribution, new_val, actor) → None; resolve_stage_tasks_on_complete(stage_record) → None
- **`stage_rate_service`** — Stage role-rate correction (S1.1, super-admin only); auto-recalc unsettled earnings on rate change  
  _Key:_ rerate_stage_role(stage_record, role, new_rate, actor, reason) → tuple(AddaStageRoleRate, int)
- **`pool_service`** — Piece-pool allocation (reserve, materialize, allocate, void, bounds checking, soft warnings)  
  _Key:_ pool_good(stage_record, allocation) → bool; materialize_stage_pool(stage_record) → None; allocate(stage_record, worker, items, confirm=False) → StageWorkAssignment; void_allocation(allocation) → None; available(stage_record) → dict; worker_allocated(worker, stage_record) → dict; check_allocation_bound(stage_record) → bool; preview_bound_violations(stage_record) → list; bound_soft_warning(task) → str; clear_stage_pool(stage_record) → None
- **`reconciliation_service`** — Post-settlement data reconciliation (validates settlement integrity, detects discrepancies)  
  _Key:_ TBD (integration pending)
- **`_shared`** — Shared authorization helpers (ensure_can_manage checks, internal helpers)  
  _Key:_ _ensure_can_manage(user) → raises PermissionDenied if not production role

**Forms (16)**

| Form | Model | Purpose |
|------|-------|---------|
| ProductForm | Product | Create/edit Product (code, name, description); code locked on edit |
| AddaCreateForm | None (Form) | Simple product picker to create new Adda (service allocates code) |
| StartLayeringForm | None (Form) | Manager refines workers on auto-created Layering stage_record (requires Cutting Master) |
| AttachRollForm | None (Form) | Roll picker + verified width/weight for Layering (width_inch choice, weight_kg decimal) |
| EditRollEntryForm | None (Form) | Correct width/weight/notes on LayeringRollEntry (optional fields allow selective update) |
| CompleteLayeringForm | None (Form) | Finalize Layering (overall layer length, duration, notes); legacy single-form variant |
| RemainingClothForm | None (Form) | Record leftover cloth piece after Layering (width_inch, weight_kg, notes) |
| CuttingForm | None (Form) | Legacy single-shot cutting complete (pieces_cut + worker checkboxes + notes) |
| CuttingStartForm | None (Form) | Manager assigns workers to Cutting stage (Cutting Master + Helper eligible) |
| CuttingBreakupRowForm | None (Form) | One row of size/color/pattern/count breakup table (view instantiates per-row from POST arrays) |
| CuttingBundleForm | None (Form) | Create cutting bundle with size header (PR8 schema) |
| CuttingDraftForm | None (Form) | Save draft notes (non-form; minimal POST fields) |
| PatternVerifyForm | None (Form) | Pattern assignment verification (assignment_id required, photo_id + note optional) |
| SizeAllocationForm | None (Form) | Size allocation form (multi-row: size_id + proportion_pct pairs); validates sum=100 at complete |
| StageForm | Stage | Stage create/edit (code, name, description, access_by_skill M2M, access_by_role M2M) |
| StageRateCorrectionForm | None (Form) | Rate correction form (new_rate decimal, reason required); freezes settled rates (S1.1) |

**Workflows (10)**

- Adda lifecycle: create (atomic counter + Layering bootstrap) → stage panels → each stage: start (workers assign) → actions (attach/upload/bundle/etc) → complete (advance) → repeat until finished
- Layering (Stage 1): attach rolls → verify width/weight → record remaining cloth → save breakup → complete + advance to Cutting
- Cutting-Pattern (Stage 2b, optional): start → upload video/photos → verify patterns → allocate sizes → complete + advance
- Cutting (Stage 2): breakup (size/color/pattern/count) → create bundles → add items → allocate to workers → complete + advance
- Barcode Generation (Stage 2c, optional): start → generate batches → complete + advance
- Worker self-report (any payable stage): GET form (schema-driven, own task only) → POST draft (re-editable) or submit (locks task, freezes contributions)
- Management quantity review (P1): review reported contributions per Adda → correct verified_quantity before settlement
- Stage rate correction (S1.1): super-admin corrects per-(sr, role) rate → auto-recalcs unsettled earnings
- Product flow editing: add/remove/reorder stages, set cost method (FIXED/QUANTITY/WEIGHT), validate grain monotonicity
- Pattern library management: CRUD ProductPattern rows, assign patterns per product with pieces_count

**Templates (43):** `production/adda_dashboard.html`, `production/adda_list.html`, `production/adda_detail.html`, `production/adda_form.html`, `production/adda_report_review.html`, `production/product_list.html`, `production/product_form.html`, `production/product_confirm_archive.html`, `production/product_patterns_edit.html`, `production/product_sizes_edit.html`, `production/product_flow.html`, `production/pattern_list.html`, `production/pattern_form.html`, `production/pattern_confirm_delete.html`, `production/pattern_workspace.html`, `production/stage_list.html`, `production/stage_form.html`, `production/stage_confirm_delete.html`, `production/stage_panel_standalone.html`, `production/stage_panel_embedded.html`, `production/_stage_panel_layering.html`, `production/_stage_panel_cutting.html`, `production/_stage_panel_cutting_pattern.html`, `production/_stage_panel_barcode_gen.html`, `production/_stage_panel_collapse.html`, `production/layering_workspace.html`, `production/_layering_summary.html`, `production/cutting_workspace.html`, `production/cutting_form.html`, `production/barcode_gen_workspace.html`, `production/worker_report.html`, `production/worker_report_embedded.html`, `production/_worker_report_body.html`, `production/_worker_report_styles.html`, `production/stage_rate_list.html`, `production/stage_rate_correct.html`, `production/costing.html`, `production/stalled_addas.html`, `production/pending_reports.html`, `production/_activity_feed.html`, `production/_workers_widget.html`, `production/_form_styles.html`, `production/_autosave.html`

**Auditor notes:** CRITICAL AUDIT NOTES: (1) STAGE ARCHITECTURE: each stage (layering/cutting/pattern/barcode-gen) has isolated views + services in separate files; adding a new stage requires NO edits to existing stage code (open-closed principle). StagePanelView unifies embedded-panel rendering across all stages. (2) SINGLE-WRITER ENFORCEMENT: WorkerStageTask + WorkerStageContribution written ONLY via worker_task_service (CI gate [4/4]); reported_quantity immutable, verified_quantity management-correctable (P1). (3) PERMISSION GATES: Super Admin bypasses all Django perms + role checks (user_has_perm); production.view/add/change/delete_stage perms assignable per role via Roles editor. ManagementRoleMixin + SuperAdminOnlyMixin block non-super-admin. ProductionRoleMixin + StageViewAccessMixin enforce skill (Stage.access_by_skill/access_by_role) + assignment-level isolation (V2-1c-iv). (4) RBAC ISOLATION: AddaDetailView gates tabs per stage skill; WorkerReportView enforces own-task-only (object-level isolation). (5) ATOMIC SAFETY: create_adda uses SELECT FOR UPDATE on Product row (race-safe counter). set_stage_workers locks active tasks with select_for_update (roster full-replace). (6) IFRAME SEAM: stage-panel ?embedded=1 strips chrome for iframes; completion redirects to stage-panel?embedded=1&advanced=1 so parent JS reloads (postMessage bridge). @xframe_options_sameorigin allows same-origin iframes. (7) ASYNC/AUTO-SAVE: PatternSaveVideoView detects X-Requested-With=XMLHttpRequest for debounced notes auto-save. (8) HISTORY INTEGRATION: tracking.services.log_* called post-write for audit trail (AddaHistory, ProductHistory, ClothRollHistory). (9) FOUNDATION TRANSITIONAL: SWA (StageWorkAssignment) allocation UI is V2-2 pending (expense→settlement edge); pool_service + cost_service independent of it. (10) PERFORMANCE: Extensive prefetch_related + select_related in querysets (no N+1 in dashboard/detail views). attach_layering_snapshots bulk-attaches snapshots (P5.1). (11) FORMS VALIDATION: ProductForm/PatternForm/StageForm lock `code` field on edit (form.fields['code'].disabled=True) to prevent orphaning existing references. (12) ERROR HANDLING: Service ValidationError → user-friendly messages via form.add_error() or messages.error(); PermissionDenied → 403; IntegrityError → informative "already exists" message. (13) STAGE-SPECIFIC HANDLERS: production.stages.base.registry maps stage_code → StageHandler (contribution_schema, snapshot, pool_grain, etc); no hardcoded stage conditionals in views/templates (data-driven). (14) COST FREEZE: ProcessingCost frozen at complete (per AddaStageRecord); ADR-0009 "honest-NULL" surfaces unpriced stages. (15) WORKER ISOLATION: dashboard + history filtered for non-management (own tasks/Addas only). Management sees factory-wide digest. (16) ALLOCATION DIMENSIONS (S4): piece-pool grain coarsens downstream (COLOR_SIZE → QUANTITY ok, QUANTITY → COLOR_SIZE NOT ok); validated at flow edit. (17) REOPEN GUARDS: services refuse reopen if stage scanned/exported/settled (V2-3 guards); admin errors logged. (18) MULTI-ROW FORMS: cutting breakup/bundle items parsed from POST arrays; CuttingBreakupRowForm instantiated per-row; validation delegated to service. (19) MISSING FILE: no stage-specific allocation ledger in production (V2-2 pending; pool_service + cost_service are the interim). (20) KNOWN UNKNOWNS: full end-to-end testing of iframe stage-panel reloads + cross-stage data integrity checks deferred to Phase 8 (touch-time remediation).

---

### raw_materials  (`/raw-materials/`)

**URLs (22)**

| Pattern | Name | View | Methods |
|---------|------|------|---------|
| `` | `dashboard` | RawMaterialDashboardView | GET |
| `cloth/` | `cloth-dashboard` | ClothDashboardView | GET |
| `rolls/` | `roll-list` | RollListView | GET |
| `rolls/bulk-add/` | `roll-bulk-create` | RollBulkCreateView | GET, POST |
| `rolls/<int:pk>/` | `roll-detail` | RollDetailView | GET |
| `rolls/<int:pk>/edit/` | `roll-edit` | RollUpdateView | GET, POST |
| `rolls/<int:pk>/assign/` | `roll-assign` | RollAssignView | GET, POST |
| `cloth-types/` | `cloth-type-list` | ClothTypeListView | GET |
| `cloth-types/add/` | `cloth-type-create` | ClothTypeCreateView | GET, POST |
| `cloth-types/<int:pk>/edit/` | `cloth-type-update` | ClothTypeUpdateView | GET, POST |
| `cloth-types/<int:pk>/archive/` | `cloth-type-archive` | ClothTypeArchiveView | GET, POST |
| `cloth-types/<int:pk>/delete/` | `cloth-type-delete` | ClothTypeDeleteView | GET, POST |
| `cloth-colors/` | `cloth-color-list` | ClothColorListView | GET |
| `cloth-colors/add/` | `cloth-color-create` | ClothColorCreateView | GET, POST |
| `cloth-colors/<int:pk>/edit/` | `cloth-color-update` | ClothColorUpdateView | GET, POST |
| `cloth-colors/<int:pk>/archive/` | `cloth-color-archive` | ClothColorArchiveView | GET, POST |
| `cloth-colors/<int:pk>/delete/` | `cloth-color-delete` | ClothColorDeleteView | GET, POST |
| `storage-locations/` | `storage-list` | StorageLocationListView | GET |
| `storage-locations/add/` | `storage-create` | StorageLocationCreateView | GET, POST |
| `storage-locations/<int:pk>/edit/` | `storage-update` | StorageLocationUpdateView | GET, POST |
| `storage-locations/<int:pk>/archive/` | `storage-archive` | StorageLocationArchiveView | GET, POST |
| `storage-locations/<int:pk>/delete/` | `storage-delete` | StorageLocationDeleteView | GET, POST |

**Views (22)**

| View | Kind | File | Purpose |
|------|------|------|---------|
| RawMaterialDashboardView | TemplateView | raw_materials/views/dashboard.py | Overall raw material index—cloth live status & counts, future material placeholders (elastic/rib/sui/dhaga), recent roll history. |
| ClothDashboardView | TemplateView | raw_materials/views/dashboard.py | Cloth-only dashboard with Type × Color breakup, date + color filters, by-location count, recent rolls & history log. |
| RollListView | ListView | raw_materials/views/roll_views.py | Paginated roll list (50 per page) with status/type/location/color filters, active filter chips, recent roll history. |
| RollBulkCreateView | FormView | raw_materials/views/roll_views.py | Super Admin only—bulk intake form captures cloth type, location, purchase date, (color, qty) breakup, supplier, cost. Creates N rolls in one transaction via service. |
| RollDetailView | DetailView | raw_materials/views/roll_views.py | Single roll detail page—read-only summary of roll_id, type, color, width, weight, location, status, financials (gated to financial roles). Edit button shown only for NOT_USED rolls. |
| RollUpdateView | UpdateView | raw_materials/views/roll_views.py | Stock-level edit for a NOT_USED roll—width, weight, location, purchase date, supplier (financial roles), cost (financial roles). Delegates to update_roll_details service for audit trail per field. |
| RollAssignView | FormView | raw_materials/views/assign_views.py | Assign single roll to Layering-stage in-progress Adda—captures weight & width at assignment time, resolves Adda code from dropdown, delegates to assign_roll_to_adda service. |
| ClothTypeListView | ListView | raw_materials/views/master_views.py | Master data list—all ClothType rows (active + archived), edit/archive/delete/create actions. |
| ClothTypeCreateView | CreateView | raw_materials/views/master_views.py | Create new ClothType (name only)—redirects to list on success. |
| ClothTypeUpdateView | UpdateView | raw_materials/views/master_views.py | Edit ClothType name—redirects to list on success. |
| ClothTypeArchiveView | View | raw_materials/views/master_views.py | Soft-delete (is_active=False) / restore for ClothType via POST—confirmation page on GET. |
| ClothTypeDeleteView | DeleteView | raw_materials/views/master_views.py | Hard-delete ClothType if no FK references exist—service raises ValidationError if roll FK exists, surfaces as user-friendly message. |
| ClothColorListView | ListView | raw_materials/views/master_views.py | Master data list—all ClothColor rows (name + hex_code swatch), edit/archive/delete/create actions. |
| ClothColorCreateView | CreateView | raw_materials/views/master_views.py | Create new ClothColor (name + optional hex code)—redirects to list on success. |
| ClothColorUpdateView | UpdateView | raw_materials/views/master_views.py | Edit ClothColor name and hex code—redirects to list on success. |
| ClothColorArchiveView | View | raw_materials/views/master_views.py | Soft-delete (is_active=False) / restore for ClothColor via POST—confirmation page on GET. |
| ClothColorDeleteView | DeleteView | raw_materials/views/master_views.py | Hard-delete ClothColor if no FK references exist—service raises ValidationError if roll FK exists, surfaces as user-friendly message. |
| StorageLocationListView | ListView | raw_materials/views/master_views.py | Master data list—all StorageLocation rows (name + code column), edit/archive/delete/create actions. |
| StorageLocationCreateView | CreateView | raw_materials/views/master_views.py | Create new StorageLocation (name + uppercase code)—redirects to list on success. |
| StorageLocationUpdateView | UpdateView | raw_materials/views/master_views.py | Edit StorageLocation name and code—redirects to list on success. |
| StorageLocationArchiveView | View | raw_materials/views/master_views.py | Soft-delete (is_active=False) / restore for StorageLocation via POST—confirmation page on GET. |
| StorageLocationDeleteView | DeleteView | raw_materials/views/master_views.py | Hard-delete StorageLocation if no FK references exist—service raises ValidationError if roll FK exists, surfaces as user-friendly message. |

**Services (2)**

- **`master_service`** — Master data CRUD operations for ClothType, ClothColor, StorageLocation—soft-delete (archive), restore, and hard-delete with FK protection.  
  _Key:_ archive_master(user, instance) — sets is_active=False, idempotent, atomic; restore_master(user, instance) — sets is_active=True; hard_delete_master(user, instance) — permanent delete, wraps ProtectedError as ValidationError if FKs exist
- **`roll_service`** — ClothRoll lifecycle—bulk intake, assignment to Adda at Layering stage, stock-level field editing with audit trail, leftover consumption tracking.  
  _Key:_ _next_roll_id() — postgres cloth_roll_seq sequence → CR-000142 format; bulk_create_rolls(user, cloth_type, storage_location, purchased_date, breakup, supplier, cost_per_kg) — N rolls in one transaction, logs ClothRollHistory CREATED per roll; update_roll_details(user, roll, width_inch, weight_kg, storage_location, purchased_date, supplier, cost_per_kg) — field-level diff, NOT_USED guard, logs history per changed field; assign_roll_to_adda(user, roll, adda, weight_kg, width_inch) — attach to Layering Adda, sets status=USED, logs ClothRollHistory STATUS_CHANGED + AddaHistory ROLL_ASSIGNED; consume_leftover(user, leftover, adda, notes) — records reuse of RemainingClothOfClothRoll piece (not yet UI exposed)

**Forms (6)**

| Form | Model | Purpose |
|------|-------|---------|
| ClothTypeForm | ClothType | Master data CRUD—editable name only (is_active soft-deleted via service). |
| ClothColorForm | ClothColor | Master data CRUD—editable name + optional hex_code (browser pattern validation #RRGGBB). |
| StorageLocationForm | StorageLocation | Master data CRUD—editable name + uppercase code (normalized via clean_code). |
| BulkRollForm | N/A (abstract) | Bulk intake form (cloth_type, storage_location, purchased_date, supplier, cost_per_kg). Accepts (color, qty) parallel arrays via raw_breakup list, validates & structures into breakup list of dicts. Supplier/cost fields pop'd for non-financial roles in __init__. |
| RollEditForm | ClothRoll | Stock-level field editing—width_inch, weight_kg, storage_location, purchased_date (all roles), supplier + cost_per_kg (financial roles only, pop'd in __init__). NOT_USED guard enforced by service. |
| AssignRollForm | N/A (abstract) | Roll-to-Adda assignment—weight_kg (Decimal), width_inch (ChoiceField 36-44), adda_code (CharField, dynamic choices injected by view for Layering in-progress Addas). |

**Workflows (4)**

- Cloth Intake Workflow — Super Admin only. BulkRollForm captures (cloth_type, location, purchase_date, supplier, cost) + N rows (color, qty breakup). Submits to RollBulkCreateView.form_valid() → bulk_create_rolls service → creates N ClothRoll rows + sequence increments + ClothRollHistory CREATED per roll.
- Roll-to-Adda Assignment Workflow — Multi-role. RollAssignView renders dropdown of in-progress Layering Addas. Form captures weight_kg + width_inch at assignment time (not at intake). Submits to form_valid() → assign_roll_to_adda service → ClothRoll.status='used', adds adda FK, logs ClothRollHistory STATUS_CHANGED + AddaHistory ROLL_ASSIGNED, redirects to production:adda-detail.
- Stock-level Roll Edit Workflow — Multi-role. RollUpdateView form shows width, weight, location, purchase_date (all), supplier + cost (financial roles only). Service-driven update_roll_details performs field-level diff, logs ClothRollHistory per changed field, NOT_USED guard enforced.
- Master Data CRUD Workflow (ClothType / ClothColor / StorageLocation) — Shared pattern across three models. List view shows all (active + archived). Create/update redirect to list. Archive POST toggles is_active + logs (via archive_master/restore_master service). Hard-delete checks FK references, raises ValidationError if protected FKs exist.

**Templates (11):** `raw_materials/raw_material_dashboard.html`, `raw_materials/cloth_dashboard.html`, `raw_materials/roll_list.html`, `raw_materials/roll_bulk_form.html`, `raw_materials/roll_detail.html`, `raw_materials/roll_edit_form.html`, `raw_materials/roll_assign_form.html`, `raw_materials/master_list.html`, `raw_materials/master_form.html`, `raw_materials/master_confirm_archive.html`, `raw_materials/master_confirm_delete.html`

**Auditor notes:** Role-gating: All views except RollBulkCreateView protected by ProductionRoleMixin (requires PRODUCTION_ROLES: super_admin/manager/karigar/worker). RollBulkCreateView restricted to SuperAdminOnlyMixin (super_admin only). Financial fields (supplier, cost_per_kg) are form-level gated in BulkRollForm.__init__() and RollEditForm.__init__() for non-financial users (defence in depth; service re-checks). ClothRollHistory tracking is comprehensive—every roll create/assign/edit operation logs via tracking.services.log_roll(). Master data uses soft-delete (is_active=False) never hard-delete except when no FKs exist. Roll ID generation is Postgres-only via cloth_roll_seq sequence (RuntimeError on SQLite). AssignRollView is the sole entry point for roll-to-Adda binding from the raw_materials app (Layering workspace in production app drives the actual in-progress Adda selection). Leftover consumption (consume_leftover service) is written but not exposed via UI yet—reserves write semantics for Phase 6 material costing (ADR-0009). All master data forms share template: master_list.html, master_form.html, master_confirm_archive.html, master_confirm_delete.html (code-reuse via base _Master*View classes). Roll list & dashboards include ClothRollHistory event log (30 recent events shown)—tracking.models.ClothRollHistory lazy-imported to avoid circular dependency. No migrations present in audit (handled separately). No test files included in this audit (config/raw_materials/tests/ exists but not detailed per READ-ONLY specification).

---

### expense (Payroll / Worker Earnings)  (`/expense/`)

**URLs (9)**

| Pattern | Name | View | Methods |
|---------|------|------|---------|
| `my/` | `my-earnings` | MyEarningsView | GET |
| `payroll/` | `payroll-overview` | PayrollOverviewView | GET |
| `workers/<int:pk>/` | `worker-detail` | WorkerPayrollDetailView | GET |
| `workers/<int:pk>/settle/` | `settlement-create` | SettlementCreateView | GET, POST |
| `workers/<int:pk>/profile/` | `worker-profile` | WorkerProfileEditView | GET, POST |
| `advances/add/` | `advance-add` | AdvanceCreateView | GET, POST |
| `settlements/` | `adda-settlement-list` | AddaSettlementListView | GET |
| `settlements/start/<int:adda_pk>/` | `adda-settlement-start` | AddaSettlementStartView | POST |
| `settlements/<str:reference>/` | `adda-settlement-detail` | AddaSettlementDetailView | GET, POST |

**Views (9)**

| View | Kind | File | Purpose |
|------|------|------|---------|
| MyEarningsView | TemplateView | /home/tech/umesh-personal/django_inventory/config/expense/views.py | Worker's own payroll dashboard (always self-scoped, never role-gated). Shows earnings ladder, unsettled expected, production stats, stage earnings, assignments, settlements, and advances. |
| PayrollOverviewView | TemplateView | /home/tech/umesh-personal/django_inventory/config/expense/views.py | Management-only aggregated payroll board. Lists all workers with live ledger balances (earnings/payable/settled), advance exposure, and production pieces. |
| WorkerPayrollDetailView | TemplateView | /home/tech/umesh-personal/django_inventory/config/expense/views.py | Per-worker detailed payroll view. Worker sees only self; management sees any. Shows summary, ledger, assignments, settlements, and outstanding advances. |
| SettlementCreateView | TemplateView | /home/tech/umesh-personal/django_inventory/config/expense/views.py | Payment-only settlement form (V2-2). Management enters cash paid; advance recovery moved to Adda settlement finalize. Validates recovery inputs are rejected if present. |
| AdvanceCreateView | FormView | /home/tech/umesh-personal/django_inventory/config/expense/views.py | Management records an immutable worker advance (loan). Creates WorkerAdvance row; recovery happens later at settlement. |
| WorkerProfileEditView | FormView | /home/tech/umesh-personal/django_inventory/config/expense/views.py | Management edits worker payroll metadata (bank/UPI account, joining date, opening advance, is_active, notes). |
| AddaSettlementListView | TemplateView | /home/tech/umesh-personal/django_inventory/config/expense/views.py | V2-2 settlement queue. Shows ready Addas (all payable stages complete, uncredited lines exist) and waiting Addas (incomplete stages). Lists recent settlements + their chain. |
| AddaSettlementStartView | View | /home/tech/umesh-personal/django_inventory/config/expense/views.py | POST-only: opens a DRAFT settlement for one Adda or resumes an existing draft. Redirects to detail screen. |
| AddaSettlementDetailView | TemplateView | /home/tech/umesh-personal/django_inventory/config/expense/views.py | Adda settlement lifecycle view. Draft mode: shows settleable lines (era-A/B skip reasons), variance inputs, per-advance recovery choices, finalize/discard. Finalized: read-only snapshot + reverse/supersede buttons. |

**Services (9)**

- **`adda_settlement_service`** — V2-2 Adda-centric earning + recovery-decision event (sole writer of AddaSettlement + AddaSettlementItem, era-B StageWorkAssignment lines). Drafts are recomputable scratchpads; finalize books stage_earning credits + advance_recovery debits via ledger. Drafts have no money, no frozen rows. Finalize is atomic: locks advisory 5374 → adda row → stage records → per-worker profiles/advances. Reverse never edits — it writes compensating entries + optionally creates successor draft.  
  _Key:_ create_draft(adda, user, notes) → AddaSettlement; preview_lines(settlement) → (lines, skip_a, skip_b); settlement_queue() → {ready, waiting}; discard_draft(settlement, user); finalize_adda_settlement(settlement, user, variance, recoveries, reconciliation_override); record_reconciliation_evidence(settlement, adda, override_reason, overridden_by) → int; reverse_adda_settlement(settlement, user, supersede, notes) → (settlement, successor_draft)
- **`settlement_service`** — Payment-only service (V2-2 Model A). Sole writer of PayrollSettlement + PayrollSettlementItem ledger debits. Creates cash payment + snapshots payable/advance-outstanding for audit. Advance recovery RE-HOMED to adda_settlement_service.finalize. Immutable: corrections = reverse ledger debits + fresh settlement. Derived: balances never read from snapshots, always recomputed live.  
  _Key:_ create_settlement(user, worker, amount_paid, recoveries, settlement_date, method, notes) → PayrollSettlement; _next_reference() → str (SETL-0001, …); _q(amount) → Decimal
- **`allocation_service`** — Sole writer of StageWorkAssignment + allocation-time STAGE_EARNING credits. Earnings are ALLOCATION-DRIVEN (quantity × rate frozen at allocation time, NOT cost ÷ workers). Gated by flag LEDGER_CREDIT_AT_ALLOCATION (default False = settlement-first). Double-credit guards both directions (era-A coarse, era-B exact). Locks bundle item (item allocation only) + updates ledger.  
  _Key:_ allocate_stage_work(user, stage_record, worker, allocated_quantity, bundle_item, bundle, size, color, pattern, notes, entry_date) → StageWorkAssignment; void_allocation(assignment, user); item_allocation_summary(bundle_item) → {allocated, remaining}
- **`ledger_service`** — Sole writer of WorkerLedgerEntry (append-only, immutable money ledger). Balance = SUM(credits) − SUM(debits), NEVER stored. Corrections = reverse_entry (opposite-direction REVERSAL row linked by `reverses`). No UPDATE/DELETE ever. Logging to stdlib logger for money writes.  
  _Key:_ log_credit(worker, category, amount, entry_date, created_by, assignment, notes) → WorkerLedgerEntry; log_debit(worker, category, amount, entry_date, created_by, advance, settlement, notes) → WorkerLedgerEntry; reverse_entry(entry, actor, notes) → WorkerLedgerEntry; worker_balance(worker) → Decimal
- **`payroll_service`** — Read-only aggregations + per-worker access scoping. Everything derived live (never stored). Key functions: worker_summary (earnings/payable/settled/advance snapshots), worker_balance_breakdown (itemized derivation), worker_adda_earnings (per-Adda breakup), unsettled_expected (uncredited contribution lines), worker_production_stats (pieces/Adda counts). Advance outstanding calculated as given − recovered.  
  _Key:_ payroll_totals() → {pending_payable, advance_exposure}; worker_summary(worker, since, until) → {total_earnings, advance_outstanding, total_settled, pending_payable, …}; worker_balance_breakdown(worker) → {gross_earnings, earnings_reversed, debits_by_category, pending_payable}; worker_ledger(worker, limit) → QuerySet; worker_assignments(worker, limit) → QuerySet; worker_adda_earnings(worker, limit) → [{adda_code, product, stages, total_pieces, total_earned}]; worker_stage_earnings(worker) → [{stage, earned, qty}]; worker_production_stats(worker) → {pieces_produced, assigned_addas, active_addas, completed_addas}; unsettled_expected(worker) → Decimal; advance_outstanding(worker) → Decimal; advance_remaining(advance) → Decimal; outstanding_advances(worker) → [{advance, amount, recovered, remaining}]; worker_advances(worker, limit) → QuerySet; worker_settlements(worker, limit) → QuerySet; can_view_worker(viewer, worker_id) → bool
- **`reconciliation_service`** — Worker-pay integrity control (quantity-based, not money). Compares allocated work vs. stage frozen output. Flags: unpaid (no worker credited), under_allocated (< output), over_allocated (> produced — always defect), grouped_paid (billed-elsewhere stage has allocations), unpriced_paid. Read-only; reads production.AddaStageRecord + expense.StageWorkAssignment. M-6 settlement WARN (S1.1, H1) = over_allocated only. S5 may block finalize with tolerance + audited override.  
  _Key:_ reconcile_stage_pay(adda=None) → [{adda, stage, processing_cost, output_qty, allocated_qty, earnings, qty_delta, flag}]; summarize(rows) → dict
- **`settlement_resolver`** — Single place that decides which quantity a settlement pays for a WorkerStageContribution. Extracts quantity policy so future policies (packed/hybrid) plug in here without touching money-write. Default STAGE_GOOD = verified_quantity if set else good_quantity (S3 payable-good truth).  
  _Key:_ settlement_quantity(contribution, policy=STAGE_GOOD) → Decimal
- **`advance_service`** — Sole writer of WorkerAdvance (immutable advance records). Separate loan pool — does NOT post to payable ledger. Only creates row; recovery happens later at settlement by owner's choice.  
  _Key:_ record_advance(user, worker, amount, advance_date, notes, attachment) → WorkerAdvance
- **`_shared`** — Shared auth gates for the expense app. No DB writes.  
  _Key:_ _ensure_management(user) → PermissionDenied if not manager/super_admin

**Forms (3)**

| Form | Model | Purpose |
|------|-------|---------|
| AdvanceForm | WorkerAdvance (implicit) | Records an advance: worker (dropdown), amount, optional advance_date, notes, attachment. |
| SettlementForm | PayrollSettlement (implicit) | Settlement header fields only (per-advance recoveries parsed in view): amount_paid (defaults to full payable), optional settlement_date, method (Cash/Bank/UPI/Other), notes. |
| WorkerProfileForm | WorkerProfile | Management edits worker payroll metadata: phone, bank_account_name, bank_account_number, bank_ifsc, upi_id, joining_date, opening_advance, is_active, notes. |

**Workflows (6)**

- Worker Earnings Ladder: my-earnings shows total_earnings, advance_outstanding, pending_payable, earnings_in_window — snapshot for self-service visibility.
- Advance Entry Workflow: management records an advance (advance_form) → immutable WorkerAdvance created → recovery deferred to settlement.
- Payment-Only Settlement (V2-2 Model A, Legacy Path): settlement-create shows pending payable + outstanding advances → management enters amount_paid + per-advance recovery_amount (now rejected, moved to Adda settlement) → create_settlement writes PayrollSettlement + settlement_payment debit.
- V2-2 Adda Settlement Lifecycle: adda-settlement-list (queue: ready/waiting) → POST to adda-settlement-start opens DRAFT → adda-settlement-detail (GET: preview mode shows settleable lines + skipped era-A/B + variance/recovery inputs; POST: finalize/reverse/supersede/discard) → finalize is atomic: locks advisory 5374 → freezes SWAs (earning lines per contribution, D-S grain) → books stage_earning credits + advance_recovery debits + PayrollSettlementItems + AddaSettlementItems + settlement totals → reverse unfolds all debits/credits + stamps PSI.reversed_at (no edit) + optionally creates successor DRAFT.
- Settlement Correction Flow (V2-2 Truth): never edit finalized settlement → reverse (compensating entries + SWA void + settlement status→REVERSED) → optionally supersede (create successor DRAFT with supersedes FK pointing back) → UI chains reversals for audit.
- Worker Profile Metadata: worker-profile edit form allows bank/UPI account setup + joining date + opening_advance (seeds advance outstanding for pre-system loans).

**Templates (8):** `expense/my_earnings.html`, `expense/payroll_overview.html`, `expense/worker_detail.html`, `expense/worker_profile_form.html`, `expense/advance_form.html`, `expense/settlement_form.html`, `expense/adda_settlement_list.html`, `expense/adda_settlement_detail.html`

**Auditor notes:** ARCHITECTURE: V2-2 Model A = Adda settlement (earning + recovery decision) is SEPARATE from payment. Payment is now PAYMENT-ONLY (cash debit only). Advance recovery RE-HOMED to adda_settlement_service.finalize (owner-chosen per-advance at review).

CRITICAL LOCKS (deadlock-free by order):
- Advisory transaction lock 5374 (shared with settlement_service) serializes reference allocation.
- Per-Adda finalize: advisory 5374 → AddaSettlement → AddaStageRecord rows → per-worker WorkerProfile (FIFO worker_id order) → WorkerAdvance rows (FIFO order).
- Production-side task/rate writes do NOT lock settlements; stage_rate_service.rerate_stage_role (F1) acquires 5374 FIRST to join serialization without deadlock.

SINGLE-WRITER GATES (ADR-0002):
- ledger_service: sole writer of WorkerLedgerEntry (append-only, immutable).
- adda_settlement_service: sole writer of AddaSettlement, AddaSettlementItem, era-B StageWorkAssignment earning lines.
- allocation_service: sole writer of era-A StageWorkAssignment allocation lines (flag-gated, default OFF = settlement-first).
- settlement_service: sole writer of PayrollSettlement, PayrollSettlementItem (legacy recovery lines only; new recoveries go to adda_settlement_service).
- advance_service: sole writer of WorkerAdvance.

ERA DISTINCTION (ADR-0007 V2-2 cutover lever: LEDGER_CREDIT_AT_ALLOCATION flag, default False):
- ERA-A (allocation-era): SWA.adda_settlement = NULL; credits booked at allocation-time if flag ON (refusal if OFF).
- ERA-B (settlement-era): SWA.adda_settlement = <AddaSettlement>; credits booked at settlement finalize (structural era marker).
- Cross-era double-credit guards:
  * Coarse (era-A): if this worker-stage has a non-voided settlement SWA, allocating it again refuses.
  * Fine (era-B): contribution lines with non-voided settlement_line SWA skipped exactly; era-A pairs (worker, stage_record) with non-voided non-settlement SWAs skip all their contributions coarsely.

MONEY TRUTH:
- Balance = SUM(credits) − SUM(debits), live-computed from ledger, NEVER stored.
- Snapshots (payable_before, advance_outstanding_before on settlements, frozen totals on AddaSettlement/Item) are audit-only; never read as source of truth.
- Corrections = append-only reversal entries (opposite direction, reverses FK), never UPDATE/DELETE.

SETTLEMENT QUANTITY POLICY (settlement_resolver.py):
- STAGE_GOOD (only implemented): uses verified_quantity if set (management correction) else good_quantity (payable-good production truth, S3).
- Future policies (packed/hybrid) plug into settlement_quantity() here without touching money-write.

RECONCILIATION (M-6, S1.1):
- reconciliation_service: read-only, quantity-based (not money). Compares allocated vs. output_qty.
- Flags: unpaid, under_allocated (soft, PAY-2 gap expected), over_allocated (hard, B-1 leak), grouped_paid, unpriced_paid, no_output_qty.
- SETTLEMENT_WARN_FLAGS = {over_allocated} only (H1); other HARD_FLAGS are separate concerns.
- SettlementReconciliationEvidence: persisted at finalize (append-only, never log-scraped) for every over_allocated stage. S5 may BLOCK on evidence + tolerance + audited override.

FIELD GATING:
- S5: super-admin gets reconciliation_override field on AddaSettlementDetailView finalize form when ENFORCE_SETTLEMENT_RECONCILIATION=True and evidence exists.
- All management URLs sidebar-rule gated: menu hidden ⇒ URL blocked (accounts.services.permission_service).

FEATURE FLAGS:
- LEDGER_CREDIT_AT_ALLOCATION (default False): allocate_stage_work refuses if OFF (settlement-first).
- ENFORCE_SETTLEMENT_RECONCILIATION (default False): finalize blocks on over_allocated if True, unless audited override.
- SETTLEMENT_RECONCILIATION_TOLERANCE (default '0'): over_allocated overage tolerance in Decimal.

PAYMENT METHODS: Cash, Bank Transfer, UPI, Other (PayrollSettlement.Method choices).

WORKER PROFILE: auto-created on demand (get_or_create); `opening_advance` seeds advance outstanding for pre-system loans.

VIEWS NEVER:
- Touch WorkerLedgerEntry/StageWorkAssignment/Settlement directly (delegate to services).
- Read expected_*-as-money (ADR-0005).
- Sum processing_cost + earnings (ADR-0009).
These are service responsibilities only.

VIEWS ALWAYS:
- Gate via _ManagementOnly mixin (unless explicitly self-scoped like MyEarningsView).
- Delegate to ONE service, redirect + message on result.
- Trust service refusals and surface their messages.

PAYMENT WORKFLOW REFUSAL (V2-2):
- SettlementCreateView.post() loudly refuses any recover_* POST inputs (checks stray tab from old flow) with message: "Advance recovery now happens when you settle the Adda — this screen only pays cash."

ADVANCE LIFECYCLE:
- record_advance() → WorkerAdvance (immutable, full audit: amount, advance_date, notes, attachment, entered_by).
- Advance outstanding = Σ given − Σ recovered (derived, never stored).
- Recovery happens at AddaSettlement.finalize (adda_settlement_service processes owner-chosen per-advance amounts) → PayrollSettlementItem (parent = AddaSettlement) + ledger_service.log_debit(ADVANCE_RECOVERY).
- Legacy recovery lines (pre-V2-2) parent to PayrollSettlement (XOR constraint: exactly one parent).

LOGGING:
- stdlib logger (module logger): ledger_service, settlement_service, adda_settlement_service log money writes (entry_id, worker_id, type, category, amount, reference, etc.).
- tracking.log_adda() called on settlement finalize/reverse (Adda-360 timeline event with metadata: reference, expected_total, workers, lines, skipped_era_a/b).

EXISTING GAPS / TRANSITIONED CODE:
- WorkerLedgerEntry categories ADVANCE, PAYMENT are legacy (replaced by SETTLEMENT_PAYMENT, ADVANCE_RECOVERY).
- Allocations booked at allocation-time only if flag ON; default OFF (settlement-first), refusing with clear message.
- V2-2 cutover complete: no more "earn at allocation, recover at payment" coupling.

---

### storefront  (`/storefront/`)

**URLs (9)**

| Pattern | Name | View | Methods |
|---------|------|------|---------|
| `^$` | `public_home` | storefront.views.public_home (FBV) | GET |
| `^storefront/products/$` | `storefront:product_list` | ProductListView | GET |
| `^storefront/products/add/$` | `storefront:product_add` | ProductCreateView | GET, POST |
| `^storefront/products/<int:pk>/edit/$` | `storefront:product_edit` | ProductUpdateView | GET, POST |
| `^storefront/products/<int:pk>/delete/$` | `storefront:product_delete` | ProductDeleteView | GET, POST |
| `^storefront/categories/$` | `storefront:category_list` | CategoryListView | GET |
| `^storefront/categories/add/$` | `storefront:category_add` | CategoryCreateView | GET, POST |
| `^storefront/categories/<int:pk>/edit/$` | `storefront:category_edit` | CategoryUpdateView | GET, POST |
| `^storefront/categories/<int:pk>/delete/$` | `storefront:category_delete` | CategoryDeleteView | GET, POST |

**Views (9)**

| View | Kind | File | Purpose |
|------|------|------|---------|
| public_home | FBV | /home/tech/umesh-personal/django_inventory/config/storefront/views/public_views.py | Public homepage (no auth) — reads HomePageConfig, Category, FeaturedProduct, HeroShowcaseCard, WhyUsCard, FooterLink, NavLink; renders with fallback SVGs. |
| ProductListView | ListView (CBV) | /home/tech/umesh-personal/django_inventory/config/storefront/views/listing_views.py | Authenticated (listing_team role) — lists FeaturedProducts with server-side badge/active filters, KPI counts, DataTables client-side search/sort. |
| ProductCreateView | CreateView (CBV) | /home/tech/umesh-personal/django_inventory/config/storefront/views/listing_views.py | Create new FeaturedProduct via form with CroppableImageWidget, image processing, success message; redirects to product_list. |
| ProductUpdateView | UpdateView (CBV) | /home/tech/umesh-personal/django_inventory/config/storefront/views/listing_views.py | Edit existing FeaturedProduct with form, image reprocessing, success message; redirects to product_list. |
| ProductDeleteView | DeleteView (CBV) | /home/tech/umesh-personal/django_inventory/config/storefront/views/listing_views.py | Confirm and delete FeaturedProduct by pk; shows product name in confirmation; redirects to product_list. |
| CategoryListView | ListView (CBV) | /home/tech/umesh-personal/django_inventory/config/storefront/views/listing_views.py | Authenticated (listing_team role) — lists Category with server-side active filter, KPI counts, DataTables client-side search/sort. |
| CategoryCreateView | CreateView (CBV) | /home/tech/umesh-personal/django_inventory/config/storefront/views/listing_views.py | Create new Category via form with CroppableImageWidget, image processing, success message; redirects to category_list. |
| CategoryUpdateView | UpdateView (CBV) | /home/tech/umesh-personal/django_inventory/config/storefront/views/listing_views.py | Edit existing Category with form, image reprocessing, success message; redirects to category_list. |
| CategoryDeleteView | DeleteView (CBV) | /home/tech/umesh-personal/django_inventory/config/storefront/views/listing_views.py | Confirm and delete Category by pk; shows linked product count with warning (products unlinked, not deleted); redirects to category_list. |

**Services (1)**

- **`image_service`** — Single-home for Pillow crop/resize pipeline — decoupled from forms so seed scripts, imports, and future APIs can reuse. Only processes NEW UploadedFile instances; leaves existing FieldFile untouched.  
  _Key:_ process_and_attach(instance, field_specs, *, cleaned_data, form_data) — for each (field_name, target_w, target_h): if uploaded file exists, process via Pillow (crop_json or auto center-crop + resize), assign back to instance

**Forms (5)**

| Form | Model | Purpose |
|------|-------|---------|
| HomePageConfigForm | HomePageConfig | Edit singleton hero section, CTA banner, section headings, footer text, images (hero_background_image, brand_logo). Calls image_service.process_and_attach on save. |
| CategoryForm | Category | Create/edit Category (name, subtitle, item_count_label, image, icon_svg, display_order, is_active). CroppableImageWidget(400x200). Calls image_service.process_and_attach on save. |
| FeaturedProductForm | FeaturedProduct | Create/edit FeaturedProduct (name, category, category_label, description, price, original_price, sizes, badge, image, icon_svg, display_order, is_active). CroppableImageWidget(400x300). Calls image_service.process_and_attach on save. |
| HeroShowcaseCardForm | HeroShowcaseCard | Create/edit HeroShowcaseCard (title, description, price_label, image, icon_svg, display_order, is_active). CroppableImageWidget(200x200). Calls image_service.process_and_attach on save. |
| WhyUsCardForm | WhyUsCard | Create/edit WhyUsCard (title, description, image, icon_svg, display_order, is_active). CroppableImageWidget(200x200). Calls image_service.process_and_attach on save. |

**Workflows (4)**

- public_home (no auth) — queries HomePageConfig + Category + FeaturedProduct + HeroShowcaseCard + WhyUsCard + FooterLink + NavLink (all is_active=True); groups footer_links by column; supplies default SVGs for icon-less cards; renders single page
- Product CRUD workflow (authenticated, listing_team role): list → filter by badge/active (server) + text search (client DataTables) → add (Create) → edit (Update) → delete (Confirm → Delete) → back to list
- Category CRUD workflow (authenticated, listing_team role): list → filter by active status (server) + text search (client DataTables) → add (Create) → edit (Update) → delete (Confirm with linked product count) → back to list
- Image upload workflow (all CUD forms): CroppableImageWidget → file input → Cropper.js modal (auto-opened) → crop coordinates JSON → form.save() calls image_service.process_and_attach() → Pillow crop/resize → InMemoryUploadedFile → field assigned

**Templates (8):** `storefront/listing/product_list.html`, `storefront/listing/product_form.html`, `storefront/listing/product_confirm_delete.html`, `storefront/listing/category_list.html`, `storefront/listing/category_form.html`, `storefront/listing/category_confirm_delete.html`, `storefront/widgets/croppable_image.html`, `public_home.html (mounted at /)`

**Auditor notes:** 1. ROUTING: public_home (FBV) mounted at root "/" via config/config/urls.py; authenticated storefront CRUD at /storefront/ (app_name='storefront'). Media serving via /media/storefront/<path> custom handler.

2. RBAC: All authenticated views (ProductListView, ProductCreateView, etc.) require LoginRequiredMixin + ListingTeamMixin (custom UserPassesTestMixin). ListingTeamMixin gates to ROLE_LISTING_TEAM or ROLE_SUPER_ADMIN via user_has_role() from accounts.services.

3. IMAGE PROCESSING: Single service (image_service) orchestrates Pillow crop/resize. Processors.py provides pure Pillow helpers (process_image, _parse_crop_data, _center_crop). All forms call image_service.process_and_attach in save() method, which only processes NEW UploadedFile (not existing FieldFile). Dimensions locked in IMAGE_SPECS registry + form-level CroppableImageWidget specs.

4. PUBLIC/PRIVATE BOUNDARY (ADR-0008): public_home is read-only (no writes, no login required) — renders HomePageConfig + config rows. Explicitly avoids commerce money/quantities. Fallback SVGs (DEFAULT_TSHIRT_SVG, DEFAULT_CATEGORY_SVG, DEFAULT_SHIELD_SVG) provide UX when no custom icons uploaded.

5. DATA RELATIONSHIPS: FeaturedProduct → Category (FK, on_delete=SET_NULL, related_name='products'). Category.products.count() used in delete confirmation. Reverse FK allows filtering products by category.

6. DJANGO ADMIN: Forms (HomePageConfigForm, CategoryForm, FeaturedProductForm, etc.) live in forms.py but not registered in admin.py — only backend listing views use them. HomePageConfig is singleton (save() forces is_active=True exclusivity).

7. FORM CONTROLS: Server-side filter form (GET method) on ProductListView & CategoryListView (badge, active status for products; active status for categories). Text search handled by DataTables JS client-side (initFancyDataTable js helper in base.html). DataTables configured with pageLength=15, orderable=false on action columns.

8. DELETE INVARIANTS: ProductDeleteView deletes product row only. CategoryDeleteView unlinks (SET_NULL) related FeaturedProducts — products NOT deleted. Confirmation templates show linked product count warning.

9. MESSAGES: All CUD views use django.contrib.messages for success feedback (messages.success with object name).

10. FIELDS NOT IN STOREFRONT LISTING VIEWS: HomePageConfigForm, HeroShowcaseCardForm, WhyUsCardForm defined but not exposed in storefront URL routes — likely managed via Django admin. Audit of /storefront/ routes shows only Product + Category CBVs.

11. FILE PATHS (all storefront models): ImageField upload_to paths use 'storefront/hero/', 'storefront/categories/', 'storefront/products/', 'storefront/showcase/', 'storefront/whyus/', 'storefront/brand/'. Public access via /media/storefront/<path> middleware. No private storage.

12. TEMPLATE STRUCTURE: All authenticated views extend accounts/base.html (role-gated base with DataTables vendor includes, CSS/JS form helpers, sidebar). Public homepage (public_home.html) is standalone (custom CSS, no accounts base inheritance). Confirmation templates use reusable .confirm-card CSS class pattern.

13. MODELS INVENTORY (8 total): HomePageConfig (singleton config), Category (storefront categories), FeaturedProduct (homepage featured products), HeroShowcaseCard (hero section right-side cards), WhyUsCard (feature cards), FooterLink (footer column links grouped by column choice), NavLink (navbar links), plus related_name='products' on Category FK.

14. MISSING/NOT EXPOSED: HomePageConfig, HeroShowcaseCard, WhyUsCard, FooterLink, NavLink are queryable in public_home FBV but have no authenticated admin/listing views under /storefront/. These are read-only in public view or edited via Django admin (not shown in this audit scope).

15. SINGLE-ROW DELETE: Old "ListingService" (mentioned in ProductDeleteView comment as removed cargo-culted pass-through) is gone. Django's DeleteView directly handles one-row deletes. image_service is the ONLY side-effecting service in storefront (per rule #4 comment in listing_views.py).

---

## 2. Navigation + RBAC

# PRODUCTION AUDIT: NAVIGATION + RBAC SYSTEM

## 1. SIDEBAR ITEM REGISTRY & MENU TREE

The sidebar is driven by two parallel systems:
1. **Hardcoded `SIDEBAR` registry** in `permission_service.py` (the master definition)
2. **SidebarItemRule database table** (override/admin UI via "Sidebar Access" page)

### Full Sidebar Menu Tree (as seeded)

**SECTION: Main**
- **My Dashboard** → `inventory:inventory_dashboard` | Roles: `manager` only
- **My Dashboard** → `inventory:user_dashboard` | Roles: `worker`, `listing_team`, `accountant` (non-management users)
- **My Earnings** → `expense:my-earnings` | Roles: All authenticated (no explicit gate, self-scoped view)

**SECTION: Production** | Section-level predicate: `manager` OR `worker` OR `super_admin`
- **Operations** → `production:dashboard`
- **Manufacturing Costing** → `production:costing` | Roles: `manager` only
- **Addas** → `production:adda-list`
- **Products** → `production:product-list` | Roles: `manager` only (worker dropped)
- **Product Patterns** → `production:pattern-list` | Permissions: `production.view_productpattern` OR `production.change_productpattern`

**SECTION: Raw Materials** | Section-level predicate: `manager` OR `worker` OR `super_admin`
- **Raw Material Dashboard** → `raw_materials:dashboard`
- **Cloth Dashboard** → `raw_materials:cloth-dashboard`
- **Cloth Rolls** → `raw_materials:roll-list`
- **Cloth Types** → `raw_materials:cloth-type-list`
- **Cloth Colors** → `raw_materials:cloth-color-list`
- **Storage Locations** → `raw_materials:storage-list`

**SECTION: Storefront** | Section-level predicate: `super_admin` OR `listing_team`
- **Featured Products** → `storefront:product_list`
- **Categories** → `storefront:category_list`

**SECTION: Tracking** | Section-level predicate: `manager` OR `worker` OR `super_admin`
- **Barcode Dashboard** → `tracking:dashboard`

**SECTION: Payroll** | Section-level predicate: `manager` OR `super_admin` (workers never see)
- **Payroll** → `expense:payroll-overview` | Roles: `manager` OR `super_admin`
- **Adda Settlements** → `expense:adda-settlement-list` | Roles: `manager` OR `super_admin`
- **Record Advance** → `expense:advance-add` | Roles: `manager` OR `super_admin`

**SECTION: Administration** | Section-level predicate: `super_admin` OR holds `production.view_stage` OR `production.change_stage`
- **Access Control** → `inventory:access-control` | Roles: `super_admin` only
- **Team Members** → `accounts:user_list` | Roles: `super_admin` only
- **User Skills** → `accounts:skill_list` | Roles: `super_admin` only
- **Roles & Permissions** → `inventory:role_list` | Roles: `super_admin` only
- **Stages** → `production:stage-list` | Permissions: `production.view_stage` OR `production.change_stage`
- **Sidebar Access** → `inventory:sidebar-access` | Roles: `super_admin` only

---

## 2. RBAC MODEL: ROLES, EXTRA ROLES, AND SUPER ADMIN BYPASS

### Role Codes (Seeded System Roles)

| Code | Display Name | Description | is_system |
|------|--------------|-------------|-----------|
| `super_admin` | Super Admin | Full access to every feature. User + role management exclusive. | True |
| `manager` | Manager | Runs day-to-day production: batches, workers, inventory. No role/payment editing. | True |
| `worker` | Worker | Factory worker. Sees their profile, assigned stages, own earnings (renamed from `karigar` 2026-06-02). | True |
| `listing_team` | Listing Team | Manages storefront product + category listings. | True |
| `accountant` | Accountant | Can view + edit Supplier and Cost Per KG on cloth rolls. | True |

### Role Groupings (Constants)

```python
ADMIN_ROLES                = {super_admin}
MANAGEMENT_ROLES           = {super_admin, manager}
STOREFRONT_ROLES           = {super_admin, listing_team}
PRODUCTION_ROLES           = {super_admin, manager, worker}
FINANCIAL_ROLES            = {super_admin, accountant}
```

### How Role + Extra Roles Combine

**User Model Fields:**
- `role` (ForeignKey) → Primary role (e.g., manager)
- `extra_roles` (ManyToManyField) → Additional role grants stacked on top

**Role Resolution Functions:**

1. **`user_role_code(user)`** → Returns **single role code** (primary only)
   - If `is_superuser=True` → returns `'super_admin'` (always wins)
   - Else if `user.role` exists → returns `role.code`
   - Else → `None`

2. **`user_role_codes(user)`** → Returns **set of ALL role codes** (primary + extra)
   - Includes primary `role.code` if set
   - Appends all `extra_roles.code` values
   - Returns empty set if unauthenticated

3. **`user_has_role(user, codes: Iterable[str])`** → Boolean check
   - Returns `True` if ANY of user's role codes are in the provided set
   - Used by all sidebar predicates and access checks

### Super Admin Bypass

**Hardcoded Everywhere:**

```python
if user.is_superuser:
    return True  # Grant all access
```

**AND:**

```python
if user.role and user.role.code == 'super_admin':
    return True  # Super Admin role = implicit grant (permission matrix not required)
```

**No Escape Hatch:** Once marked `is_superuser=True` or assigned the Super Admin role, they cannot be locked out—even if all checkboxes in the Role editor are unchecked.

---

## 3. PERMISSION SERVICE: `user_has_perm()` & `user_has_role()`

### Location
`/home/tech/umesh-personal/django_inventory/config/accounts/services/permission_service.py`

### `user_has_perm(user, perm_codename: str) → bool`

**Purpose:** Check if user has a Django permission (e.g., `'production.change_stage'`).

**Check Order (cumulative):**
1. Not authenticated? → `False`
2. `is_superuser=True`? → `True` (Django built-in bypass)
3. `user.role.code == 'super_admin'`? → `True` (project rule: avoid permission matrix bloat)
4. User's role has the codename in its permission set? → `True` (via request-cached `_role_perm_codenames`)
5. Django default `user.has_perm()` (groups + direct perms)? → Result

**Note on Role Permissions:**
- Super Admin role implicitly grants ALL perms (no need to check every box)
- Other roles must have explicit permissions assigned via Role editor
- The Role editor surfaces only "curated" models (ROLE_EDITABLE_CONTENT_TYPES)

### `user_has_role(user, codes: Iterable[str]) → bool`

**Purpose:** Check if user holds ANY of the given role codes (primary or extra).

**Logic:**
```python
return bool(user_role_codes(user) & set(codes))  # set intersection
```

**Example:**
```python
user_has_role(user, [ROLE_SUPER_ADMIN, ROLE_MANAGER])  # True if either
user_has_role(user, MANAGEMENT_ROLES)                   # True if manager or super_admin
```

### Request Caching

Both helpers cache on the user instance to avoid repeated queries per request:
- `_rbac_perm_codes` → set of permission codenames from role
- `_rbac_principal` → dict with `{'role_ids': set, 'skill_ids': set}`

---

## 4. ACCESS SERVICE: `user_can_access_stage()` (Skill Gating for Production)

### Location
`/home/tech/umesh-personal/django_inventory/config/production/services/access_service.py`

### `user_can_access_stage(user, stage_code: str) → bool`

**Purpose:** Control visibility of Adda stage panels + stage records (e.g., cutting, stitching).

**Logic Order:**
1. Unauthenticated? → `False`
2. Has role `super_admin` OR `manager`? → `True` (hardcoded, cannot be removed)
3. Stage with code exists and is active?
   - **Skill overlap** (user's skills ∩ stage's `access_by_skill` FK set)? → `True`
   - **Role overlap** (user's primary + extra roles ∩ stage's `access_by_role` FK set)? → `True`
4. Else → `False` (fail-closed)

**Stage Model Fields:**
- `access_by_skill` (M2M to Skill) → Skills that unlock this stage
- `access_by_role` (M2M to Role) → Roles that unlock this stage

### `stage_access_map(user, stage_codes: Iterable[str]) → dict[str, bool]`

Batched helper for templates (avoids N queries when rendering 7+ stages). Returns `{stage_code: bool}`.

**Defense in Depth:**
- Even if Stage row is corrupted/deleted, Management roles still have implicit access
- Prevents system deadlock if a stage record is accidentally removed

---

## 5. SIDEBAR ACCESS MIDDLEWARE: URL ENFORCEMENT

### Location
`/home/tech/umesh-personal/django_inventory/config/inventory/middleware.py` (`SidebarAccessMiddleware`)

### The Coupling: "Hide Menu = Block URL"

**Principle:** If the sidebar hides a link, the view is still reachable by typing the URL. This middleware closes that gap.

**Process:**

1. **On every request:**
   - User authenticated? (else pass through, let `LoginRequired` handle)
   - Request has a resolved `url_name`? (else pass through)
   - URL in exempt list (`inventory:inventory_dashboard`, `inventory:user_dashboard`)? (else check)

2. **Call `can_access_url_name(user, url_name)` (permission_service)**
   - Anonymous user? → `True` (pass through)
   - Super Admin? → `True` (always pass)
   - SidebarItemRule for this url_name exists in DB?
     - YES → Role/skill overlap decides (use `user_principal` cached roles/skills)
     - NO → `True` (unmanaged item; view's own mixin gates it = defense in depth)

3. **If denied:**
   - AJAX request? → JSON 403 `{'detail': "You don't have the access to this page."}`
   - Regular request? → Flash error message + redirect:
     - Try referer if same-host and accessible? → Redirect to referer
     - Else → Redirect to user's safe home (manager → inventory dashboard, others → user dashboard)

### Exempt URLs (Never Blocked)
```python
_EXEMPT_URL_NAMES = {
    'inventory:inventory_dashboard',
    'inventory:user_dashboard',
}
```
(Prevents redirect loops; both are identical content for cosmetic role routing)

### SidebarItemRule (DB-Driven Override)

**How it works:**
1. Sidebar Access page shows all menu items + checkboxes for allowed roles/skills
2. Admin checks roles/skills → saves to DB
3. On render, `build_menu_for()` checks if rule exists:
   - If yes, DB set determines visibility
   - If no rule (new feature or perm-only item), hardcoded predicate falls back
4. Middleware re-checks the same rule → blocks URL if menu link is hidden

**Super Admin Special:**
- Super Admin is **never seeded into allowed_roles** (hardcoded bypass in service)
- Admin cannot accidentally lock themselves out

---

## 6. SIDEBAR RENDERING FLOW (Template + Service)

### Context Processor
`/home/tech/umesh-personal/django_inventory/config/inventory/context_processors.py`

```python
def sidebar(request):
    return {
        'sidebar_menu': build_menu_for(user, request.path) if user and user.is_authenticated else [],
        'current_role_code': user_role_code(user),
    }
```

Every template receives pre-filtered `sidebar_menu` (list of dicts).

### Template Rendering
`/home/tech/umesh-personal/django_inventory/config/accounts/templates/accounts/base.html` (lines 2064–2086)

```html
{% for section in sidebar_menu %}
<div class="nav-section" data-section="{{ section.label }}">
    <p class="nav-section-label">
        <span>{{ section.label }}</span>
        <svg class="nav-chevron">...</svg>
    </p>
    <div class="nav-section-items">
        {% for item in section.items %}
        <a href="{{ item.url }}" class="nav-link{% if item.is_active %} active{% endif %}">
            {% include 'inventory/_nav_icon.html' %}
            {{ item.label }}
        </a>
        {% endfor %}
    </div>
</div>
{% endfor %}
```

**Sections are collapsible** (JS in base.html, lines 2234–2254):
- Click label → toggle collapse
- State persists in `sessionStorage`
- Section with active link always stays open

### `build_menu_for(user, current_path: str) → list[dict]`

**Visibility Decision (per item):**

1. Item URL won't resolve? → Skip silently
2. Super Admin? → Always visible
3. **SidebarItemRule exists for this url_name?**
   - YES → Role/skill overlap in DB rule decides visibility
   - NO → Fall back to hardcoded MenuItem/MenuSection predicate
4. Hardcoded predicate checks:
   - MenuSection.predicate(user) AND MenuItem.predicate(user)
   - Factory: `_any_role(*codes)`, `_any_perm(*codenames)`

**Active Tab Logic:**
- Iterates all visible items
- Picks ONE winner: the item whose `match` substring has the longest overlap with `current_path`
- Avoids multiple items lighting up when prefixes collide

**Output:** `[{label: str, items: [{label, url, url_name, is_active, match}, ...]}, ...]`

---

## 7. ROLE EDITOR SECTIONS (Curated Permissions UI)

The Role editor doesn't show all 80+ Django permissions. Instead, it curates 5 logical sections so admins aren't overwhelmed.

### Sections

| Section | Models |
|---------|--------|
| **Production Flow** | product, productpattern, stage, workflowstage, adda |
| **Raw Materials** | clothroll, clothtype, clothcolor, storagelocation |
| **Tracking** | batchbarcode |
| **Storefront** | homepageconfig, category, featuredproduct, heroshowcasecard, whyuscard, footerlink, navlink |
| **Administration** | role, sidebaritemrule, skill |

### Hidden Models (Service-only writes)
- AddaStageRecord, LayeringRollEntry, CuttingPatternRecord, CuttingRecord
- RemainingClothOfClothRoll, ProductPatternAssignment
- All `*History` tables

---

## SUMMARY TABLE: Access Control Layers

| Layer | Driver | Enforcement | Bypass |
|-------|--------|-------------|--------|
| **Sidebar Visibility** | MenuSection + MenuItem predicates (hardcoded) OR SidebarItemRule DB | build_menu_for() filters before render | Super Admin always visible |
| **URL Access** | SidebarItemRule DB (if exists) OR view's own mixin | SidebarAccessMiddleware + can_access_url_name() | Super Admin + unauthenticated users |
| **View Permissions** | Role.permissions M2M (Django Permission objects) | View mixins (e.g., LoginRequired, custom decorators) | is_superuser OR role.code='super_admin' |
| **Stage Panel Access** | Stage.access_by_role/skill + built-in manager bypass | user_can_access_stage() | Manager OR super_admin (hardcoded) |
| **Financial Fields** | Role membership (FINANCIAL_ROLES = {super_admin, accountant}) | user_can_view/edit_financials() | Super Admin bypass |

---

## KEY ARCHITECTURE RULES

1. **Role grants access, NEVER UserType.** UserType is display/classification only.
2. **Super Admin is a dual system:** `is_superuser=True` (Django) AND `role.code='super_admin'` (project). Either one grants all perms.
3. **Extra roles stack on primary role.** A Manager can also get listing_team access without losing manager scope.
4. **"Hide menu = block URL."** Sidebar filtering + middleware enforce the same rule so removing a link in the admin UI blocks the view.
5. **Defense in depth:** Unmanaged URLs (no SidebarItemRule) fall back to view mixins. New features are never silently invisible.
6. **Caching on request scope:** `_rbac_principal` and `_rbac_perm_codes` cache on user instance so repeated checks don't re-query.
7. **Skill gating on stages, role gating on modules.** Skills unlock production work (cutting, stitching); roles unlock sidebar sections.

---

## FILES AUDITED

- `/config/accounts/models.py` – User, Role, SidebarItemRule, Skill, UserType
- `/config/accounts/services/permission_service.py` – user_has_perm, user_has_role, build_menu_for, can_access_url_name
- `/config/accounts/migrations/0016_seed_default_roles.py` – Role seeding
- `/config/accounts/migrations/0017_seed_sidebar_rules.py` – SidebarItemRule seeding
- `/config/inventory/migrations/0015_seed_sidebar_item_rules.py` – Initial sidebar seed (pre-relocation)
- `/config/inventory/migrations/0019_rename_karigar_role_to_worker.py` – Role code rename
- `/config/inventory/middleware.py` – SidebarAccessMiddleware
- `/config/inventory/context_processors.py` – Sidebar context injection
- `/config/production/services/access_service.py` – Stage skill/role gating
- `/config/accounts/templates/accounts/base.html` – Sidebar HTML + collapsible JS


---

## 3. Infrastructure + Root Routing

# Django ERP Infrastructure & Routing Audit — Phase 01

**Project:** Kapil Enterprises Inventory System  
**Audit Date:** 2026-06-14  
**Status:** READ-ONLY Exploration (No modifications)

---

## 1. Root URL Mounts (prefix → app)

**Primary URL routing** defined in `/home/tech/umesh-personal/django_inventory/config/config/urls.py`:

| Prefix | App/Target | Purpose |
|--------|-----------|---------|
| `/admin/` | Django contrib admin | Built-in Django admin panel |
| `/` (root) | `storefront.views.public_home` | Anonymous storefront homepage |
| `/app/` | `accounts.urls` | Authenticated user login/account mgmt (allauth integration) |
| `/accounts/` | `allauth.urls` | Django-allauth: email/password + Google OAuth flows |
| `/inventory/` | `inventory.urls` | RBAC dashboards + sidebar access rules |
| `/storefront/` | `storefront.urls` | Customer-facing storefront management (authenticated) |
| `/raw-materials/` | `raw_materials.urls` | Cloth rolls, types, colors, storage locations (master data) |
| `/production/` | `production.urls` | Adda batches, workflow stages, stage records, Adda lifecycle |
| `/tracking/` | `inventory.tracking_urls` | Piece-level barcodes (QR) + per-domain audit history |
| `/expense/` | `expense.urls` | Worker payroll: earnings, advances, settlements, allocations |

### Media Serving (Two-Tier + Login-Required)

**Public media** (`/media/storefront/*`):
- Served directly without authentication
- Root: `settings.MEDIA_ROOT / 'storefront'`
- Used for: homepage assets (logo, category/product images)
- Handler: `django.views.static.serve`

**Protected media** (`/media/*`):
- Requires `@login_required`
- Root: `settings.MEDIA_ROOT`
- Used for: business evidence (pattern photos, advance attachments, profile pictures)
- Handler: `login_required(django.views.static.serve)`

**Future exits** (documented, not implemented):
- S3 via `STORAGES` swap + delete routes
- nginx X-Accel-Redirect (swap `serve()` for header)

**Current limitation:** `django.serve()` has no HTTP Range support (pattern videos cannot scrub/seek; acceptable at current scale).

### Error Handlers (P0-2)

All three handlers point to Django's **default views** (not custom) to render branded templates when `DEBUG=False`:

| Status | Handler | Template | Notes |
|--------|---------|----------|-------|
| 403 | `django.views.defaults.permission_denied` | `templates/403.html` | Renders with EMPTY context (no DB access) |
| 404 | `django.views.defaults.page_not_found` | `templates/404.html` | Prevents cascading errors |
| 500 | `django.views.defaults.server_error` | `templates/500.html` | Minimal context; never triggers secondary error |

---

## 2. MIDDLEWARE Stack (In Order)

**Execution order:** Request flows DOWN; response flows UP.

| Position | Middleware | Custom? | Purpose |
|----------|-----------|---------|---------|
| 1 | `django.middleware.security.SecurityMiddleware` | No | HTTPS redirect, security headers |
| 2 | `core.observability.RequestIDMiddleware` | **Yes** | **P0.4:** Bind request ID for log correlation + echo in response header `X-Request-ID` |
| 3 | `whitenoise.middleware.WhiteNoiseMiddleware` | No | Serve static files (CSS/JS) directly without external web server |
| 4 | `django.contrib.sessions.middleware.SessionMiddleware` | No | Make `request.session` available; DB-backed sessions |
| 5 | `django.middleware.common.CommonMiddleware` | No | URL trailing slash handling, `ALLOWED_HOSTS` validation |
| 6 | `django.middleware.csrf.CsrfViewMiddleware` | No | CSRF token validation on form submissions |
| 7 | `django.contrib.auth.middleware.AuthenticationMiddleware` | No | Make `request.user` available |
| 8 | `allauth.account.middleware.AccountMiddleware` | No | Django-allauth account processing |
| 9 | `django.contrib.messages.middleware.MessageMiddleware` | No | Flash messages (`request.messages`) |
| 10 | `django.middleware.clickjacking.XFrameOptionsMiddleware` | No | `X-Frame-Options: DENY` header (prevent iframe hijacking) |
| 11 | `inventory.middleware.SidebarAccessMiddleware` | **Yes** | **Defense in depth:** Enforce URL-level access control (not just sidebar hiding). Denies/redirects if `SidebarItemRule` blocks the view, AFTER auth + messages available. Exempts landing pages (dashboards). |

**Custom Middleware Details:**
- `core.observability.RequestIDMiddleware`: Honors inbound `X-Request-ID` header; generates short UUID (12 hex chars) if missing. Stores in ContextVar for thread-safe logging. Echoes back in response header for tracing.
- `inventory.middleware.SidebarAccessMiddleware`: Resolves request URL to `url_name`; checks against `SidebarItemRule` using `permission_service.can_access_url_name()`. Super-admin always allowed. AJAX → 403 JSON; regular → flash error + redirect to safe dashboard.

---

## 3. Feature Flags & Settings (Auditor Checklist)

**All read from `.env` file** using `decouple.config()`. Environment variables override defaults.

### Ledger & Settlement Enforcement

| Flag | Default | Scope | Purpose | Notes |
|------|---------|-------|---------|-------|
| `LEDGER_CREDIT_AT_ALLOCATION` | `False` | expense app | When `True`: credit earnings at allocation time (era-A, legacy). When `False`: credit only at Adda settlement (era-B, current). **ADR-0007 executed (D-V3.1, 2026-06-11).** Kill-switch for rollback. Symmetric double-credit guard ensures both directions are safe. Physical deletion of legacy path soak-gated in separate PR. |
| `ENFORCE_ALLOCATION_BOUND` | `False` | production app | When `True`: pool-participant stages reject completions where Σ(good+alter+missing) > active allocated quantity. **S4 foundation.** Production-capacity rule only; reads no rate/earning/settlement data. Default OFF = back-compat (existing flows untouched). Kill-switch to disable instantly. |
| `ENFORCE_SETTLEMENT_RECONCILIATION` | `False` | expense app | When `True`: block finalize if stage settled more units than it produced (Σ settled good > `cost_quantity_snapshot`) beyond tolerance. Requires super-admin override reason for blocked cases. **S5 / M-6 feature.** Default False = WARN-only (today: over-allocated settlement recorded + warned, never blocked). |
| `SETTLEMENT_RECONCILIATION_TOLERANCE` | `'0'` | expense app | Absolute piece margin (global) before reconciliation block fires when `ENFORCE_SETTLEMENT_RECONCILIATION=True`. Default 0 = strict. Absorbs rounding / minor discrepancies. |
| `STALLED_ADDA_DAYS` | `3` | production app | Days threshold. Addas whose current open stage hasn't moved in this many days are flagged "stalled" on Operations landing. **P1-1 operations digest.** Tunable constant (not hardcoded in query). |

### Authentication & Security

| Setting | Default / Value | Purpose |
|---------|-----------------|---------|
| `SECRET_KEY` | **Required** from `.env` | Session cookies, CSRF tokens, signing. Crash if missing (except test/migrate). No insecure fallback in production. |
| `ALLOWED_HOSTS` | `'localhost,127.0.0.1'` (local) / from `.env` (prod) | Host Header Attack defense. Production pulled from env (comma-separated). Local dev: `['*']` for convenience. |
| `PASSWORD_HASHERS` | **Argon2** (primary), PBKDF2, BCrypt (compat) | Argon2PasswordHasher listed first; new passwords use Argon2. Older PBKDF2 hashes continue to verify. Django auto-upgrades on next successful login. OWASP recommendation. |
| `AUTH_PASSWORD_VALIDATORS` | 4-tier | UserAttributeSimilarity, MinimumLength (8 chars), CommonPassword, NumericOnly. |
| `SITE_ID` | `1` | Django sites framework; allauth uses for domain in email links. |
| `AUTH_USER_MODEL` | `'accounts.User'` | Custom User model (not Django default). Set early; never change. |
| `SESSION_ENGINE` | `'django.contrib.sessions.backends.db'` | DB-backed sessions (revocable, server-side). Not cookie-only. |
| `SESSION_COOKIE_AGE` | `28800` (8 hours) | Session expiry after inactivity. |
| `SESSION_COOKIE_HTTPONLY` | `True` | JavaScript cannot read session cookie (XSS defense). |
| `SESSION_COOKIE_SAMESITE` | `'Lax'` | Cookie sent only on same-site requests (CSRF defense). |
| `SESSION_SAVE_EVERY_REQUEST` | `False` | Performance: write to DB only when data changes, not every GET. Views/services must set `request.session.modified = True` on mutations. |

### Email & Allauth

| Setting | Default / Value | Purpose |
|---------|-----------------|---------|
| `EMAIL_BACKEND` | `'django.core.mail.backends.smtp.EmailBackend'` (prod), console in dev | SMTP (Gmail) for real emails. Console backend for local testing. |
| `EMAIL_HOST` | `'smtp.gmail.com'` | Gmail SMTP endpoint. |
| `EMAIL_PORT` | `587` | TLS port. |
| `EMAIL_USE_TLS` | `True` | Encrypted connection. |
| `EMAIL_HOST_USER` | From `.env` | Gmail address. |
| `EMAIL_HOST_PASSWORD` | From `.env` | Gmail app password (credentials in .env, never hardcoded). |
| `ACCOUNT_AUTHENTICATION_METHOD` | `'email'` | Email is the login identifier (no username field). |
| `ACCOUNT_EMAIL_REQUIRED` | `True` | Email mandatory for signup. |
| `ACCOUNT_USERNAME_REQUIRED` | `False` | No username field. |
| `ACCOUNT_EMAIL_VERIFICATION` | `'none'` (local) / `'optional'` (prod) | Local dev: skip email verification for speed. Prod: verification optional (user can skip or complete). |
| `SOCIALACCOUNT_AUTO_SIGNUP` | `False` | **Custom rule:** random Google accounts cannot self-onboard. Super-admin must pre-provision User row first. See `accounts/allauth_adapters.py`. |
| `SOCIALACCOUNT_EMAIL_AUTHENTICATION` | `True` | Attempt to find existing account by Google email. |
| `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT` | `True` | Auto-link matched email to Google account. |
| `SOCIALACCOUNT_ADAPTER` | `'accounts.allauth_adapters.RestrictedSocialAccountAdapter'` | Custom adapter enforcing pre-provisioning rule. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | From `.env` | Google OAuth credentials (never hardcoded). |

### Static Files & Media

| Setting | Value | Purpose |
|---------|-------|---------|
| `STATIC_URL` | `'/static/'` | Browser URL prefix for CSS/JS. |
| `STATICFILES_DIRS` | `[BASE_DIR / 'accounts/static']` | Development source folders. |
| `STATIC_ROOT` | `BASE_DIR / 'staticfiles'` | `collectstatic` destination (production). |
| `STORAGES['staticfiles']` | `'whitenoise.storage.CompressedManifestStaticFilesStorage'` | Compresses CSS/JS, cache-busts filenames, production-ready. |
| `STORAGES['default']` | `'django.core.files.storage.FileSystemStorage'` | Local disk storage for user uploads. |
| `MEDIA_URL` | `'/media/'` | Browser URL prefix for user uploads. |
| `MEDIA_ROOT` | `BASE_DIR / 'media'` | Disk path for user uploads. |

### Database

| Setting | Local | Production |
|---------|-------|-----------|
| Connection | Separate vars: `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Single `DATABASE_URL` env var (Neon/Render/Heroku style) |
| Engine | `'django.db.backends.postgresql'` (default) | PostgreSQL |
| SSL | No (localhost safe) | `ssl_require=True` (cloud providers) |
| `CONN_MAX_AGE` | `600` (10 min) | `600` (10 min) — connection pool reuse |
| Defaults (local) | `inventory_db`, `postgres`, `localhost`, `5432` | — |

### Debug & Observability

| Setting | Local | Production | Purpose |
|---------|-------|-----------|---------|
| `DEBUG` | `True` | `False` | Full traceback + variables (dev) vs minimal "500" error page (prod). |
| `SENTRY_DSN` | Optional from `.env` | Optional from `.env` | Error aggregation (Sentry). Zero overhead if DSN not set. |
| Logging Level | `INFO` | `INFO` | App + Django logs to console + file (local) or stdout (prod). |
| Log Rotation | `RotatingFileHandler` (5 MB × 5 backups) | `StreamHandler` (platform collects stdout) | Security + app logs in separate files (local). |

### Production Hardening (production.py only)

| Setting | Value | Purpose |
|---------|-------|---------|
| `SECURE_SSL_REDIRECT` | `True` | HTTP → HTTPS redirect. |
| `SESSION_COOKIE_SECURE` | `True` | Session cookie on HTTPS only. |
| `CSRF_COOKIE_SECURE` | `True` | CSRF token on HTTPS only. |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True` | Prevent MIME sniffing attacks. |
| `X_FRAME_OPTIONS` | `'DENY'` | Prevent clickjacking (no iframes). |
| `SECURE_HSTS_SECONDS` | `31536000` (1 year) | Enforce HTTPS for 1 year in browsers. |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` | HSTS applies to subdomains. |
| `SECURE_HSTS_PRELOAD` | `True` | Add to browser HSTS preload list. |
| `SECURE_PROXY_SSL_HEADER` | `('HTTP_X_FORWARDED_PROTO', 'https')` | Trust reverse proxy's forwarded-proto header (required if behind TLS proxy; **NEVER expose gunicorn directly with this set**). |
| `CACHES['default']` | `RedisCache` at `REDIS_URL` | Shared cache for rate limiter (auth) counters. **Required in production** (LocMem per-process would weaken it). Fail-fast if `REDIS_URL` unset. |
| `CSRF_TRUSTED_ORIGINS` | From `.env` (comma-separated, scheme-included) | Trusted origins for HTTPS POST/CORS. |

---

## 4. Core App: Abstract Base Models (No Tables)

**Location:** `/home/tech/umesh-personal/django_inventory/config/core/`

The `core` app is **abstract-only**: all models use `abstract = True` in Meta, so no DB tables are created. No migrations. Shared across all apps via import.

### TimeStampedModel (Abstract)
```python
created_at = models.DateTimeField(auto_now_add=True)  # Set once at INSERT
updated_at = models.DateTimeField(auto_now=True)      # Updated on every SAVE
```
- **Purpose:** All entities track creation + last modification timestamps.
- **Pattern:** Append-only history models have `updated_at == created_at` (harmless).
- **Usage:** Inherited by production, expense, raw_materials, tracking apps.

### ActiveManager (Custom Manager)
```python
Model.objects.all()      # All rows (including archived)
Model.active.all()       # Only is_active=True rows
```
- **Purpose:** Soft-delete pattern. Master data models flag archived rows `is_active=False` instead of hard-delete.
- **Pattern:** Default `.objects` is NOT swapped (regression risk). Apps OPT-IN via `active = ActiveManager()`.
- **Limitation:** Only works on models with `is_active` field; will raise `FieldError` if field missing.
- **Usage:** Wherever soft-archiving is needed (inventory, raw materials, production).

### AbstractHistoryEntry (Abstract)
```python
actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
```
- **Purpose:** Audit log base for per-domain history tables (tracking.ClothRollHistory, production.AddaHistory, production.ProductHistory).
- **Pattern:** Shared `actor` field + domain-specific `change_type` + FK/index per subclass for fast queries.
- **FK Strategy:** `PROTECT` (audit row user deletion blocked) + `related_name='+'` (no reverse accessor clutter).

### FieldChangeMixin (Abstract)
```python
field_name, old_value, new_value = CharField(max_length)
```
- **Purpose:** Field-level audit triple (what changed, from/to values).
- **Usage:** ClothRoll, Product history (field-diff tracking). NOT used by AddaHistory (stage transitions, not scalar diffs).

**Summary:** core provides the **single source of truth** for cross-app audit patterns, timestamps, and soft-delete; eliminates duplication risk.

---

## 5. Management Commands

All commands are **read-only audits or data setup**. Location: `<app>/management/commands/<name>.py`.

| Command | App | Purpose | Exit Code |
|---------|-----|---------|-----------|
| `reconcile_pay` | expense | **PAY-4 reconciliation report.** Compare worker pay vs frozen stage cost. Lists each completed stage with defects (over-allocation, unpaid). Exit 1 if HARD defect (pre-deploy check / cron). Exit 0 for SOFT flags (known gaps). | 0 or 1 |
| `preview_allocation_bound` | production | **S5 / S4-005 audit before enforcement.** Lists COMPLETED contributions that would fail allocation bound if `ENFORCE_ALLOCATION_BOUND` were enabled (over-bound or unallocated on pool-participant stages). Exit 1 if violations found; exit 0 when clean. **RUN THIS + clear violations BEFORE flipping ENFORCE_ALLOCATION_BOUND on.** | 0 or 1 or 2 |
| `reconcile_denorm` | production | **P5.3 / DM-4 counter validation.** Verify denormalized counters (Adda totals, etc.) against source-of-truth SUMs. READ-ONLY. Exit 1 if drift detected (cron/CI alert). Exit 0 when clean. | 0 or 1 |
| `seed_homepage` | storefront | **Initialize storefront homepage content.** Creates HomePageConfig, NavLinks, Categories, FeaturedProducts, HeroShowcase, WhyUsCards, FooterLinks with SVG icons. Safe to re-run (skips if data exists). | 0 |

---

## Summary: Audit Findings

### Strengths
1. **Layered middleware + custom access enforcement:** RequestIDMiddleware (observability) + SidebarAccessMiddleware (URL-level defense-in-depth).
2. **Feature flags discipline:** All behavioral gates (`LEDGER_CREDIT_AT_ALLOCATION`, `ENFORCE_*`) are kill-switchable via `.env`; documented in base.py with clear defaults and ADR links.
3. **Production hardening:** Full HSTS, secure cookies, HTTPS redirect, MIME-sniff prevention, proxy trust headers (documented risk).
4. **Abstract base models:** Core app eliminates duplication; single source for TimeStampedModel, ActiveManager, audit bases.
5. **Pre-flight audits:** Management commands allow dry-run validation before flipping critical flags (e.g., `preview_allocation_bound`).
6. **Logging correlation:** Request ID ContextVar + filter ensures full request trace via `grep <id> logs/`.

### Critical Items for Auditor
1. **`ENFORCE_SETTLEMENT_RECONCILIATION`** is kill-switchable but default OFF (permissive). Understand tolerance thresholds before enabling.
2. **`SECURE_PROXY_SSL_HEADER` in production:** Only safe behind TLS-terminating reverse proxy; exposing gunicorn directly would allow header spoofing.
3. **`REDIS_URL` required in production:** Rate limiter needs shared cache; LocMem would silently weaken under multi-worker gunicorn.
4. **Google OAuth pre-provisioning:** Super-admin must create User rows before employees can OAuth; not open self-signup.
5. **Media serving split:** Public (storefront) unauthenticated; protected (/media/*) requires login. No S3 yet (future exit documented).
6. **Session size discipline:** DB-backed sessions on 8-hour TTL; views must explicitly set `request.session.modified = True` or performance suffers.

---

**End of Audit Report — Phase 01**
