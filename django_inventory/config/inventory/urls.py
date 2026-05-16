from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='inventory_dashboard'),

    # Product CRUD
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    # Cloth Roll CRUD
    path('cloth/list/', views.ClothRollListView.as_view(), name='cloth_roll_list'),
    path('cloth/add/', views.ClothRollCreateView.as_view(), name='cloth_roll_add'),
    path('cloth/edit/<int:pk>/', views.ClothRollUpdateView.as_view(), name='cloth_roll_edit'),
    path('cloth/delete/<int:pk>/', views.ClothRollDeleteView.as_view(), name='cloth_roll_delete'),

    # Batch CRUD + Detail
    path('batches/list/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/add/', views.BatchCreateView.as_view(), name='batch_add'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/edit/<int:pk>/', views.BatchUpdateView.as_view(), name='batch_edit'),
    path('batches/delete/<int:pk>/', views.BatchDeleteView.as_view(), name='batch_delete'),
    path('batches/<int:pk>/transition/', views.BatchTransitionView.as_view(), name='batch_transition'),

    # Batch Cloth Assignments
    path('batches/<int:batch_pk>/cloth/add/', views.BatchClothAssignmentCreateView.as_view(), name='batch_cloth_add'),
    path('batches/<int:batch_pk>/cloth/<int:pk>/edit/', views.BatchClothAssignmentUpdateView.as_view(), name='batch_cloth_edit'),

    # Batch User Assignments
    path('batches/<int:batch_pk>/workers/add/', views.BatchUserAssignmentCreateView.as_view(), name='batch_worker_add'),
    path('batches/<int:batch_pk>/workers/<int:pk>/edit/', views.BatchUserAssignmentUpdateView.as_view(), name='batch_worker_edit'),
    path('batches/<int:batch_pk>/workers/<int:pk>/remove/', views.BatchUserAssignmentDeleteView.as_view(), name='batch_worker_remove'),

    # Batch Operations
    path('batches/<int:batch_pk>/operations/add/', views.BatchOperationCreateView.as_view(), name='batch_operation_add'),
    path('batches/<int:batch_pk>/operations/<int:pk>/edit/', views.BatchOperationUpdateView.as_view(), name='batch_operation_edit'),
    path('batches/<int:batch_pk>/operations/<int:pk>/delete/', views.BatchOperationDeleteView.as_view(), name='batch_operation_delete'),

    # Stage CRUD
    path('stages/', views.StageListView.as_view(), name='stage_list'),
    path('stages/add/', views.StageCreateView.as_view(), name='stage_add'),
    path('stages/<int:pk>/edit/', views.StageUpdateView.as_view(), name='stage_edit'),
    path('stages/<int:pk>/delete/', views.StageDeleteView.as_view(), name='stage_delete'),

    # Machine CRUD
    path('machines/', views.MachineListView.as_view(), name='machine_list'),
    path('machines/add/', views.MachineCreateView.as_view(), name='machine_add'),
    path('machines/<int:pk>/edit/', views.MachineUpdateView.as_view(), name='machine_edit'),
    path('machines/<int:pk>/delete/', views.MachineDeleteView.as_view(), name='machine_delete'),

    # Batch Type CRUD + stage template editor
    path('batch-types/', views.BatchTypeListView.as_view(), name='batch_type_list'),
    path('batch-types/add/', views.BatchTypeCreateView.as_view(), name='batch_type_add'),
    path('batch-types/<int:pk>/edit/', views.BatchTypeUpdateView.as_view(), name='batch_type_edit'),
    path('batch-types/<int:pk>/delete/', views.BatchTypeDeleteView.as_view(), name='batch_type_delete'),
    path('batch-types/<int:pk>/stages/', views.BatchTypeStagesView.as_view(), name='batch_type_stages'),
    path('batch-types/<int:pk>/stages/add/', views.BatchTypeStageAddView.as_view(), name='batch_type_stage_add'),

    # Vendor CRUD
    path('vendors/', views.VendorListView.as_view(), name='vendor_list'),
    path('vendors/add/', views.VendorCreateView.as_view(), name='vendor_add'),
    path('vendors/<int:pk>/edit/', views.VendorUpdateView.as_view(), name='vendor_edit'),
    path('vendors/<int:pk>/delete/', views.VendorDeleteView.as_view(), name='vendor_delete'),

    # Dispatch CRUD
    path('dispatches/', views.DispatchListView.as_view(), name='dispatch_list'),
    path('dispatches/add/', views.DispatchCreateView.as_view(), name='dispatch_add'),
    path('dispatches/<int:pk>/edit/', views.DispatchUpdateView.as_view(), name='dispatch_edit'),
    path('dispatches/<int:pk>/delete/', views.DispatchDeleteView.as_view(), name='dispatch_delete'),

    # Payments (Super Admin only)
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/add/', views.PaymentCreateView.as_view(), name='payment_add'),
    path('payments/<int:pk>/edit/', views.PaymentUpdateView.as_view(), name='payment_edit'),
    path('payments/<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),

    # Roles & Permissions (Super Admin only)
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/add/', views.RoleCreateView.as_view(), name='role_add'),
    path('roles/<int:pk>/edit/', views.RoleUpdateView.as_view(), name='role_edit'),
    path('roles/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='role_delete'),

    # Karigar personal dashboard
    path('my-work/', views.MyWorkView.as_view(), name='my_work'),
]
