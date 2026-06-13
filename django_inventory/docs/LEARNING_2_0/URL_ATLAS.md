# URL ATLAS — every route, grouped by app

## TL;DR (1 min)
every route in the app, grouped, with view + gate + purpose.

> Mounts (config/urls.py): `/app/`→accounts · `/production/`→production ·
> `/expense/`→expense · `/raw-materials/`→raw_materials · `/`+`/storefront/`→storefront ·
> `/inventory/`→inventory · `/tracking/`→inventory (tracking_urls, P4.2).
> Columns: route · view · gate · what it does (service/flow). Deep call chains:
> [REQUEST_JOURNEYS/](REQUEST_JOURNEYS/README.md). Permissions: all management
> routes also sidebar-rule gated (menu hidden ⇒ URL blocked).

## accounts (`/app/`) — identity + RBAC
| Route | View | Gate | Purpose |
|---|---|---|---|
| `` / `verify-otp/` / `resend-otp/` | Login/VerifyOTP/ResendOTP | public, rate-limited | OTP login (step1 email → step2 code) |
| `login/password/` | PasswordLoginView | public, rate-limited | password login |
| `logout/` | LogoutView | auth, POST-only | sign out |
| `signup/*` | Signup/Verify/Resend | pre-provisioned only | OTP signup |
| `forgot-password/`, `reset-password/verify/` | ForgotPassword/ResetVerify | public, rate-limited | OTP reset |
| `users/`,`/add/`,`/<pk>/edit/`,`/delete/` | User CRUD | super-admin | manage users |
| `skills/*`, `user-types/*` | Skill/UserType CRUD | super-admin | RBAC masters |

## production (`/production/`) — factory floor
| Route | View | Gate | Purpose |
|---|---|---|---|
| `` | AddaDashboardView | production role | Adda dashboard |
| `costing/` | ProductionCostingView | management | per-Adda cost (ADR-0009 surfaces) |
| `products/`,`/add/`,`/<pk>/edit/`,`/archive/` | Product CRUD | super-admin | product master |
| `products/<pk>/flow/` | ProductFlowEditView | super-admin | **flow editor** (order/rate/grouping/pay-eligibility; TM-1 lands here) |
| `products/<pk>/patterns/`,`/sizes/` | Patterns/Sizes edit | super-admin | per-product config |
| `patterns/*` | ProductPattern CRUD | super-admin | pattern library |
| `addas/` | AddaListView | production role | all Addas |
| `addas/start/` | AddaCreateView | management | **one-click Adda create** (race-safe code) → adda_service |
| `addas/<code>/` | AddaDetailView | production role | Adda 360-ish detail |
| `addas/<code>/stage/<type>/` | StagePanelView | skill+assignment | embedded stage panel |
| `addas/<code>/report/<type>/` | WorkerReportView | assignment | **worker phone report** → worker_task_service |
| `addas/<code>/review-reports/` | AddaReportReviewView | management | **P1 verified-qty correction** |
| `addas/<code>/layering/*` (12) | Layering* | skill+assignment | layering console (start/attach/entries/leftovers/complete/reopen) → stage services |
| `addas/<code>/pattern/*` (10) | Pattern* | skill+assignment | cutting-pattern console (evidence/verify/sizes/complete/reopen) |
| `addas/<code>/cutting/*` (16) | Cutting* | skill+assignment | cutting workspace (breakup/bundles/items/**allocate**/complete/reopen) |
| `addas/<code>/barcode-gen/*` (5) | BarcodeGen* | skill+assignment | barcode generation → barcode_service ranges |
| `stages/*` | Stage CRUD | perm-gated | global Stage library |

## expense (`/expense/`) — money
| Route | View | Gate | Purpose |
|---|---|---|---|
| `my/` | MyEarningsView | auth, self-scoped | worker Expected→Earned→Paid |
| `payroll/` | PayrollOverviewView | management | all-worker board |
| `workers/<pk>/` | WorkerPayrollDetailView | mgmt or self | per-worker money story |
| `workers/<pk>/settle/` | SettlementCreateView | management | **CASH PAYMENT only** (recovery refused) → settlement_service |
| `workers/<pk>/profile/` | WorkerProfileEditView | management | bank/UPI |
| `advances/add/` | AdvanceCreateView | management | loan → advance_service |
| `settlements/` | AddaSettlementListView | management | **settlement queue** (ready/waiting) |
| `settlements/start/<adda_pk>/` | AddaSettlementStartView | management | open/resume draft → adda_settlement_service.create_draft |
| `settlements/<reference>/` | AddaSettlementDetailView | management | **draft preview + finalize/reverse/supersede/discard** |

## raw_materials (`/raw-materials/`) — cloth stock
| Route | View | Gate | Purpose |
|---|---|---|---|
| ``, `cloth/` | dashboards | role | stock views |
| `rolls/`,`/bulk-add/`,`/<pk>/`,`/edit/` | Roll list/bulk/detail/edit | role (price=financial) | rolls → roll_service |
| `rolls/<pk>/assign/` | RollAssignView | management | bind roll→Adda at layering |
| `cloth-types/*`, `cloth-colors/*` | masters CRUD | management | soft-deactivate masters |

## inventory (`/inventory/`) + tracking (`/tracking/`)
| Route group | Views | Gate | Purpose |
|---|---|---|---|
| dashboard, access-control, sidebar-access, role | dashboard/access_hub/role/sidebar | super-admin (dash: all) | role-aware home + RBAC hub |
| `/tracking/` barcode dashboard/export/history | tracking_* (inventory app, P4.2) | role | barcode surfaces |

## storefront (`/`, `/storefront/`)
| Route | View | Gate | Purpose |
|---|---|---|---|
| `/` | public_views | public | homepage (config-composed; ADR-0008 face) |
| `/storefront/*` | listing_views | listing_team | catalog editor (FUTURE: G2 orders land here) |
