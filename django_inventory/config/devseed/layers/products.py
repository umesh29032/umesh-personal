"""Layer 4 — products + flows (writer-map rows: production.product_service
`create_product` + production.flow_service `add_stage_to_product_flow` — the
certified management write paths; actor = the scenario's manager cast user,
TRUE actor stamps per contract §4)."""

from django.apps import apps

from production.services import flow_service, product_service

from devseed.layers import DivergenceError


def seed_product_and_flow(spec, flow_codes, *, actor, flow_actor=None, stage_costs=()):
    flow_actor = flow_actor or actor
    Product = apps.get_model("production", "Product")
    Stage = apps.get_model("production", "Stage")
    WorkflowStage = apps.get_model("production", "WorkflowStage")

    created = skipped = 0
    product = Product.objects.filter(code=spec["code"]).first()
    if product is None:
        # Service path: permission gate + code normalisation run exactly as in prod.
        product = product_service.create_product(actor, code=spec["code"], name=spec["name"])
        created += 1
    else:
        if product.name != spec["name"]:
            raise DivergenceError(f"product {spec['code']}: name '{product.name}' != scenario '{spec['name']}'")
        skipped += 1

    flow_created = flow_skipped = 0
    for code in flow_codes:
        stage = Stage.objects.get(code=code)
        if WorkflowStage.objects.filter(product=product, stage=stage).exists():
            flow_skipped += 1
            continue
        flow_service.add_stage_to_product_flow(user=flow_actor, product=product, stage=stage)
        flow_created += 1

    # Order reconciliation (baseline migration seeds layering+cutting; recipes
    # insert stages between them) — bubble each stage into the scenario order
    # via the certified move service (never a direct `order` write).
    desired = ["layering"] + list(flow_codes)
    def _codes():
        return list(WorkflowStage.objects.filter(product=product)
                    .order_by("order").values_list("stage__code", flat=True))
    guardrail = 200
    while _codes() != desired and guardrail:
        guardrail -= 1
        current = _codes()
        for pos, code in enumerate(desired):
            if current[pos] != code:
                ws = WorkflowStage.objects.get(product=product, stage__code=code)
                flow_service.move_stage_in_product_flow(
                    user=flow_actor, workflow_stage=ws, direction="up")
                break
    if _codes() != desired:
        from devseed.layers import DivergenceError
        raise DivergenceError(f"flow order unreconcilable: {_codes()} != {desired}")

    # Optional binding cost config (R1 rate + R2 payability) via the certified
    # writer — the money-side flow truth the settlement resolver will read.
    from decimal import Decimal
    for cost in stage_costs:
        ws = WorkflowStage.objects.get(product=product, stage__code=cost["stage"])
        if (ws.cost_method == cost["method"]
                and ws.cost_rate is not None
                and Decimal(ws.cost_rate) == Decimal(cost["rate"])):
            flow_skipped += 1
            continue
        flow_service.set_stage_cost(
            user=flow_actor, workflow_stage=ws,
            cost_method=cost["method"], cost_rate=cost["rate"],
            credits_workers=cost.get("credits", False),
        )
        flow_created += 1

    return {
        "created": created + flow_created,
        "skipped": skipped + flow_skipped,
        "product": product,
    }
