"""Production app URL routes.

Yeh file Django ke URL dispatcher se tie karti hai. `app_name='production'`
namespacing deta hai — templates `{% url 'production:adda-detail' code=... %}`
likh sakte hain.

Path naming convention:
  • Singular noun + verb (e.g. 'pattern-add', 'layering-complete')
  • <str:code> = Adda code (T-SHIRT-001)
  • <int:pk>   = primary key for CRUD on rows

Sections in this file:
  1. Adda dashboard + Product/ProductPattern/Stage CRUDs
  2. Addas list/detail + per-stage embedded panels
  3. Layering workspace + actions + reopen
  4. Cutting-pattern workspace + actions
  5. Cutting complete
  6. Stage library CRUD (perm-gated)
"""
from django.urls import path

from production import views

app_name = 'production'

urlpatterns = [
    path('',                              views.AddaDashboardView.as_view(),   name='dashboard'),
    path('costing/',                      views.ProductionCostingView.as_view(), name='costing'),

    # Products
    path('products/',                     views.ProductListView.as_view(),     name='product-list'),
    path('products/add/',                 views.ProductCreateView.as_view(),   name='product-create'),
    path('products/<int:pk>/edit/',       views.ProductUpdateView.as_view(),   name='product-update'),
    path('products/<int:pk>/archive/',    views.ProductArchiveView.as_view(),  name='product-archive'),
    # Per-product flow editor (workflow stages add/remove/reorder).
    path('products/<int:pk>/flow/',       views.ProductFlowEditView.as_view(), name='product-flow'),
    # Per-product pattern assignment editor — pieces_count per pattern.
    path('products/<int:pk>/patterns/',   views.ProductPatternsEditView.as_view(), name='product-patterns'),
    # Per-product size chart editor (PR5 2026-05-28).
    path('products/<int:pk>/sizes/',      views.ProductSizesEditView.as_view(),    name='product-sizes'),

    # Reusable ProductPattern library CRUD (perm-gated, Super Admin bypass).
    path('patterns/',                     views.ProductPatternListView.as_view(),   name='pattern-list'),
    path('patterns/add/',                 views.ProductPatternCreateView.as_view(), name='pattern-add'),
    path('patterns/<int:pk>/edit/',       views.ProductPatternUpdateView.as_view(), name='pattern-edit'),
    path('patterns/<int:pk>/delete/',     views.ProductPatternDeleteView.as_view(), name='pattern-delete'),

    # Addas
    path('addas/',                  views.AddaListView.as_view(),    name='adda-list'),
    path('addas/start/',            views.AddaCreateView.as_view(),  name='adda-create'),
    path('addas/<str:code>/',       views.AddaDetailView.as_view(),  name='adda-detail'),

    # Per-stage panel — canonical URL for both standalone view and iframe embed.
    # ?embedded=1 strips hero/nav so the panel fits inside iframe / accordion.
    path('addas/<str:code>/stage/<str:stage_type>/',    views.StagePanelView.as_view(),         name='stage-panel'),

    # Layering workflow — workspace (GET) + actions (POST)
    path('addas/<str:code>/layering/',                  views.LayeringWorkspaceView.as_view(),  name='layering-workspace'),
    path('addas/<str:code>/layering/start/',            views.LayeringStartView.as_view(),      name='layering-start'),
    path('addas/<str:code>/layering/attach-roll/',      views.LayeringAttachRollView.as_view(), name='layering-attach-roll'),
    path('addas/<str:code>/layering/quick-create-roll/', views.LayeringQuickCreateAndAttachView.as_view(), name='layering-quick-create-roll'),
    path('addas/<str:code>/layering/full-create-roll/',  views.LayeringFullCreateAndAttachView.as_view(),  name='layering-full-create-roll'),
    path('addas/<str:code>/layering/entries/<int:pk>/', views.LayeringEntryUpdateView.as_view(), name='layering-entry-update'),
    path('addas/<str:code>/layering/entries/<int:pk>/remove/', views.LayeringEntryRemoveView.as_view(), name='layering-entry-remove'),
    path('addas/<str:code>/layering/remaining/<int:pk>/remove/', views.LayeringRemoveRemainingClothView.as_view(), name='layering-remove-remaining'),
    path('addas/<str:code>/layering/complete/',         views.LayeringCompleteView.as_view(),   name='layering-complete'),
    # Admin-only reopen — completed Layering ko unlock karke correction allow.
    path('addas/<str:code>/layering/reopen/',           views.LayeringReopenView.as_view(),     name='layering-reopen'),

    # ── Cutting-Pattern stage (NEW 2026-05-28) ───────────────────────────
    # Sequence: start → save video / add photos (any order) → complete
    # Workspace standalone view + 5 POST action endpoints.
    path('addas/<str:code>/pattern/',                       views.PatternWorkspaceView.as_view(),  name='pattern-workspace'),
    path('addas/<str:code>/pattern/start/',                 views.PatternStartView.as_view(),      name='pattern-start'),
    path('addas/<str:code>/pattern/save/',                  views.PatternSaveVideoView.as_view(),  name='pattern-save'),
    path('addas/<str:code>/pattern/photos/add/',            views.PatternAddPhotoView.as_view(),   name='pattern-photos-add'),
    path('addas/<str:code>/pattern/photos/<int:pk>/remove/', views.PatternRemovePhotoView.as_view(), name='pattern-photo-remove'),
    # Pattern verification + sizes (NEW PR2 2026-05-28)
    path('addas/<str:code>/pattern/verify/',                views.PatternVerifyView.as_view(),     name='pattern-verify'),
    path('addas/<str:code>/pattern/unverify/',              views.PatternUnverifyView.as_view(),   name='pattern-unverify'),
    path('addas/<str:code>/pattern/sizes/',                 views.PatternSetSizesView.as_view(),   name='pattern-set-sizes'),
    path('addas/<str:code>/pattern/complete/',              views.PatternCompleteView.as_view(),   name='pattern-complete'),
    # Admin-only reopen — mirror of layering-reopen.
    path('addas/<str:code>/pattern/reopen/',                views.PatternReopenView.as_view(),     name='pattern-reopen'),

    # Cutting stage — legacy single-submit form (back-compat for simple flows)
    path('addas/<str:code>/cutting/',  views.CuttingCompleteView.as_view(),  name='cutting-complete'),

    # Cutting workspace (PR3 2026-05-28) — per-(size, color, pattern) breakup + barcode metadata
    path('addas/<str:code>/cutting/workspace/',                views.CuttingWorkspaceView.as_view(),         name='cutting-workspace'),
    path('addas/<str:code>/cutting/start/',                    views.CuttingStartView.as_view(),             name='cutting-start'),
    path('addas/<str:code>/cutting/breakup/save/',             views.CuttingBreakupSaveView.as_view(),       name='cutting-breakup-save'),
    path('addas/<str:code>/cutting/breakup/<int:pk>/delete/',  views.CuttingBreakupDeleteView.as_view(),     name='cutting-breakup-delete'),
    # Actual Cutting Bundles (PR8 schema + PR9 two-step flow)
    # Bundle = per-size header; item = pattern × color × count inside.
    path('addas/<str:code>/cutting/bundle/create/',              views.CuttingBundleCreateView.as_view(),     name='cutting-bundle-create'),
    path('addas/<str:code>/cutting/bundle/<int:pk>/add-item/',   views.CuttingBundleAddItemView.as_view(),    name='cutting-bundle-add-item'),
    # PR10: multi-select consume from breakup rows into bundle.
    path('addas/<str:code>/cutting/bundle/<int:pk>/add-pieces/', views.CuttingBundleAddPiecesView.as_view(),  name='cutting-bundle-add-pieces'),
    path('addas/<str:code>/cutting/bundle/item/save/',           views.CuttingBundleItemSaveView.as_view(),   name='cutting-bundle-item-save'),
    path('addas/<str:code>/cutting/bundle/item/<int:pk>/delete/', views.CuttingBundleItemDeleteView.as_view(), name='cutting-bundle-item-delete'),
    path('addas/<str:code>/cutting/bundle/<int:pk>/delete/',     views.CuttingBundleDeleteView.as_view(),     name='cutting-bundle-delete'),
    path('addas/<str:code>/cutting/bundle/item/<int:pk>/allocate/', views.CuttingBundleItemAllocateView.as_view(), name='cutting-item-allocate'),
    path('addas/<str:code>/cutting/allocation/<int:pk>/delete/', views.CuttingAllocationDeleteView.as_view(), name='cutting-allocation-delete'),
    path('addas/<str:code>/cutting/draft/',                    views.CuttingDraftView.as_view(),             name='cutting-draft'),
    path('addas/<str:code>/cutting/workspace/complete/',       views.CuttingWorkspaceCompleteView.as_view(), name='cutting-workspace-complete'),
    path('addas/<str:code>/cutting/reopen/',                   views.CuttingReopenView.as_view(),            name='cutting-reopen'),

    # ── Barcode Generation stage (PR-C 2026-05-29) ───────────────────────
    # Sequence: start → generate → complete
    # Optional per-product workflow stage (legacy products skip; cutting
    # inline-generates for back-compat).
    path('addas/<str:code>/barcode-gen/',          views.BarcodeGenWorkspaceView.as_view(),  name='barcode-gen-workspace'),
    path('addas/<str:code>/barcode-gen/start/',    views.BarcodeGenStartView.as_view(),      name='barcode-gen-start'),
    path('addas/<str:code>/barcode-gen/generate/', views.BarcodeGenGenerateView.as_view(),   name='barcode-gen-generate'),
    path('addas/<str:code>/barcode-gen/complete/', views.BarcodeGenCompleteView.as_view(),   name='barcode-gen-complete'),
    path('addas/<str:code>/barcode-gen/reopen/',   views.BarcodeGenReopenView.as_view(),     name='barcode-gen-reopen'),

    # Stage library CRUD (Super Admin only). Replaces old /stage-access/ page —
    # access controls now live on the Stage model itself.
    path('stages/',                views.StageListView.as_view(),   name='stage-list'),
    path('stages/add/',            views.StageCreateView.as_view(), name='stage-add'),
    path('stages/<int:pk>/edit/',  views.StageUpdateView.as_view(), name='stage-edit'),
    path('stages/<int:pk>/delete/', views.StageDeleteView.as_view(), name='stage-delete'),
]
