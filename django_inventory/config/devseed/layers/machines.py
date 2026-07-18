"""Layer 5 — machines (writer-map row: machines.machine_service
`create_machine_type`/`create_machine` — carries the MGT-F-1 code-immutability
+ iexact-dup guards; converge by machine code)."""

from django.apps import apps

from machines.services import machine_service

from devseed.layers import DivergenceError


def seed_machines(spec, *, actor):
    MachineType = apps.get_model("production", "MachineType")
    Machine = apps.get_model("machines", "Machine")

    created = skipped = 0
    mtype = MachineType.objects.filter(name=spec["machine_type"]).first()
    if mtype is None:
        mtype = machine_service.create_machine_type(name=spec["machine_type"], user=actor)
        created += 1
    else:
        skipped += 1

    for m in spec["machines"]:
        machine = Machine.objects.filter(code__iexact=m["code"]).first()
        if machine is None:
            machine_service.create_machine(
                code=m["code"], name=m["name"], machine_type=mtype, user=actor,
            )
            created += 1
        else:
            if machine.machine_type_id != mtype.pk:
                raise DivergenceError(
                    f"machine {m['code']}: type '{machine.machine_type}' != scenario '{mtype}'"
                )
            skipped += 1
    return {"created": created, "skipped": skipped}
