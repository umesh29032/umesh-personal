> **📦 ARCHIVED 2026-06-12.** Historical record — do not update.
> Superseded by / live truth: scripts/check.sh + CLAUDE.md (test layout moved on).

# Tests, Edge Cases, Risks

## Test layout

```
raw_materials/tests/
├── test_roll_id_sequence.py        # sequential + concurrent allocation (Postgres-only)
├── test_roll_service.py            # bulk create, color breakup, assign, RBAC gates
├── test_master_service.py          # archive vs hard_delete, PROTECT behaviour
└── test_form_field_gating.py       # BulkRollForm shape per role

production/tests/
├── test_adda_service.py            # per-product counter atomicity
├── test_stage_service.py           # complete_layering / complete_cutting / advance
└── test_models.py                  # unique_together on WorkflowStage + AddaStageRecord

tracking/tests/
├── test_barcode_service.py         # generate_for_cutting, one-shot guard, qr_data_uri
└── test_history_service.py         # log_roll / log_adda / log_product write fields
```

Coverage target: ≥80% line coverage on services. Views covered via integration tests on golden path.

## Golden-path integration test

```python
def test_golden_path_end_to_end(db, super_admin_user):
    # 1. seed master data exists (migration)
    cotton = ClothType.objects.get(name='Cotton')
    red    = ClothColor.objects.get(name='Red')
    blue   = ClothColor.objects.get(name='Blue')
    rohini = StorageLocation.objects.get(code='ROHINI')

    # 2. bulk create 5 rolls
    rolls = roll_service.bulk_create_rolls(
        user=super_admin_user, cloth_type=cotton, location=rohini,
        purchased_date=date.today(),
        breakup=[{'color': red, 'qty': 3}, {'color': blue, 'qty': 2}],
    )
    assert len(rolls) == 5
    assert all(r.roll_id.startswith('CR-') for r in rolls)

    # 3. start Adda for T-SHIRT
    tshirt = Product.objects.get(code='T-SHIRT')
    adda = adda_service.create_adda(super_admin_user, tshirt)
    assert adda.code == 'T-SHIRT-001'

    # 4. assign rolls to Adda
    for r in rolls:
        roll_service.assign_roll_to_adda(super_admin_user, r, adda, weight_kg=Decimal('25.0'), width_inch=42)
        assert r.status == ClothRoll.Status.USED

    # 5. complete layering
    stage_service.complete_layering(
        adda, lay_count=10, duration_minutes=45, worker_ids=[super_admin_user.id],
        notes='', user=super_admin_user,
    )
    adda.refresh_from_db()
    assert adda.current_stage.stage_type == WorkflowStage.StageType.CUTTING

    # 6. complete cutting → barcodes generated
    stage_service.complete_cutting(
        adda, pieces_cut=200, worker_ids=[super_admin_user.id], notes='', user=super_admin_user,
    )
    adda.refresh_from_db()
    assert adda.status == Adda.Status.COMPLETED
    assert adda.current_stage is None
    assert adda.barcodes.count() == 200
    assert adda.barcodes.first().value == 'T-SHIRT-001-0001'
    assert adda.barcodes.last().value  == 'T-SHIRT-001-0200'
```

## Edge cases — explicit handling

| # | Case | Behaviour |
|---|------|-----------|
| 1 | Bulk roll create with qty=0 in a breakup row | form-level `qty >= 1` validator |
| 2 | Bulk create with archived color (is_active=False) | form queryset filters `is_active=True`; service rejects archived FK |
| 3 | Assign roll to Adda whose current_stage != Layering | `ValidationError("rolls only assignable during Layering stage")` |
| 4 | Assign roll to Adda whose status is cancelled/completed | `ValidationError`; service guard |
| 5 | Complete cutting with `pieces_cut=0` | form-level `pieces_cut >= 1` |
| 6 | Cutting completed twice (resubmit) | `AddaStageRecord` unique_together blocks second insert |
| 7 | Barcode generation crashes mid-bulk_create | atomic txn rolls back; safe to retry |
| 8 | Accountant tries to edit production data | service raises PermissionDenied; view-level redirects |
| 9 | Archive ClothType that is in use | UI shows Archive only; hard-delete disabled when usage_count > 0 |
| 10 | Concurrent `create_adda` for same product | `SELECT FOR UPDATE` on Product row serializes; no duplicate codes |
| 11 | Scan endpoint without auth | `@login_required` redirects to login |
| 12 | Roll's cloth_type/color archived after roll exists | roll detail still renders; PROTECT keeps FK valid |
| 13 | Roll already assigned, user reassigns to different Adda | service raises `ValidationError("roll already used")`; super-admin uses `unassign_roll` first |
| 14 | Product code contains hyphens (e.g. `1-6`) | URL pattern `<str:code>` handles; barcode parser splits on last `-NNNN` group |
| 15 | LayeringRecord saved with 0 rolls assigned | allowed (snapshot of empty set); UI warns user before submit |

## Risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Roll ID sequence drift after manual DB edit | low | service-only writer; never accept client-supplied roll_id |
| Per-product Adda counter race | medium | `SELECT FOR UPDATE` already in `create_adda`; concurrency test |
| Sticker print misaligned | medium | print template tested in browser print-preview before ship |
| QR payload guessable | low | scan endpoint requires login; no PII in URL |
| Stale history when actor user deleted | low | actor FK `PROTECT`; explicit anonymization migration when needed |
| Future M2M migration for partial roll use breaks existing rolls | medium | service name `assign_roll_to_adda` future-proofed; M2M migration is additive |
| Expense app added later breaks workers M2M | low | M2M `through=` migration is Django-supported on existing M2M |
| `qrcode` lib not installed at deploy | low | pinned in requirements.txt; CI installs from req file |
| Migration order broken if `production` not registered before `tracking` | low | explicit `Migration.dependencies` chain; verified in CI by `makemigrations --check` |

## Non-goals re-confirmed (locked from Understanding Lock)

- Scanning UX beyond opening detail page on QR scan (generation in scope; advanced status updates via scan come later)
- Stages beyond Layering and Cutting (Packing/Delivery deferred)
- Non-cloth raw materials (yarn, thread, packaging)
- Mobile app — relies on phone camera QR + browser
- Vendor payments + expense ledger (placeholder app only)
- Multi-factory permissions
- Analytics dashboards beyond v1 Cloth Inventory + Adda dashboard
