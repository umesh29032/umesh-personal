"""URL routes for production app."""
from django.urls import path

from production import views

app_name = 'production'

urlpatterns = [
    path('',                              views.AddaDashboardView.as_view(),   name='dashboard'),

    # Products
    path('products/',                     views.ProductListView.as_view(),     name='product-list'),
    path('products/add/',                 views.ProductCreateView.as_view(),   name='product-create'),
    path('products/<int:pk>/edit/',       views.ProductUpdateView.as_view(),   name='product-update'),
    path('products/<int:pk>/archive/',    views.ProductArchiveView.as_view(),  name='product-archive'),
    path('products/<int:pk>/flow/',       views.ProductFlowEditView.as_view(), name='product-flow'),
    path('products/<int:pk>/patterns/',   views.ProductPatternsEditView.as_view(), name='product-patterns'),

    # Product pattern library — admin manages reusable patterns.
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
    path('addas/<str:code>/layering/reopen/',           views.LayeringReopenView.as_view(),     name='layering-reopen'),

    # Cutting-pattern stage
    path('addas/<str:code>/pattern/',                       views.PatternWorkspaceView.as_view(),  name='pattern-workspace'),
    path('addas/<str:code>/pattern/start/',                 views.PatternStartView.as_view(),      name='pattern-start'),
    path('addas/<str:code>/pattern/save/',                  views.PatternSaveVideoView.as_view(),  name='pattern-save'),
    path('addas/<str:code>/pattern/photos/add/',            views.PatternAddPhotoView.as_view(),   name='pattern-photos-add'),
    path('addas/<str:code>/pattern/photos/<int:pk>/remove/', views.PatternRemovePhotoView.as_view(), name='pattern-photo-remove'),
    path('addas/<str:code>/pattern/complete/',              views.PatternCompleteView.as_view(),   name='pattern-complete'),

    # Cutting stage (single submit)
    path('addas/<str:code>/cutting/',  views.CuttingCompleteView.as_view(),  name='cutting-complete'),

    # Stage library CRUD (Super Admin only). Replaces old /stage-access/ page —
    # access controls now live on the Stage model itself.
    path('stages/',                views.StageListView.as_view(),   name='stage-list'),
    path('stages/add/',            views.StageCreateView.as_view(), name='stage-add'),
    path('stages/<int:pk>/edit/',  views.StageUpdateView.as_view(), name='stage-edit'),
    path('stages/<int:pk>/delete/', views.StageDeleteView.as_view(), name='stage-delete'),
]
