from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render

from ..models import ClothRoll, Product, Batch, StockLedger, Stage
from ..models import BatchClothAssignment


@login_required
def dashboard(request):
    """
    Inventory dashboard with high-level KPIs.
    All queries use aggregation — no N+1 issues.
    """
    # KPI 1: Total cloth in stock (meters, excluding exhausted)
    total_cloth_length = (
        ClothRoll.objects.exclude(status='EXHAUSTED')
        .aggregate(total=Sum('remaining_length'))['total'] or 0
    )

    # KPI 2: Total finished products
    total_products = Product.objects.aggregate(total=Sum('quantity'))['total'] or 0

    # KPI 3: Active (WIP) batches
    active_batches = Batch.objects.filter(status='WIP').count()

    # KPI 4: Total wastage
    total_wastage = (
        BatchClothAssignment.objects.aggregate(total=Sum('wastage_length'))['total'] or 0
    )

    # Section: Stock breakdown by cloth type
    cloth_stock_by_type = (
        ClothRoll.objects
        .values('cloth_type')
        .annotate(total_length=Sum('remaining_length'), roll_count=Count('id'))
        .order_by('-total_length')
    )

    # Section: Recent ledger movements (last 10)
    # select_related covers all FK fields used in templates to prevent N+1
    recent_movements = (
        StockLedger.objects
        .select_related('from_stage', 'to_stage', 'batch', 'created_by', 'content_type')
        .order_by('-date')[:10]
    )

    # Quick stats
    total_cloth_rolls = ClothRoll.objects.count()
    total_stages = Stage.objects.filter(is_active=True).count()

    context = {
        'total_cloth_length': total_cloth_length,
        'total_products': total_products,
        'active_batches': active_batches,
        'total_wastage': total_wastage,
        'cloth_stock_by_type': cloth_stock_by_type,
        'recent_movements': recent_movements,
        'total_cloth_rolls': total_cloth_rolls,
        'total_stages': total_stages,
    }
    return render(request, 'inventory/dashboard.html', context)
