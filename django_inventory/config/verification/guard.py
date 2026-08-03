"""verification.guard — command polarity (VER-D2, contract §6.3).

INVERSE shape vs the devseed guard: devseed is structurally ABSENT in
production, so its guard only ever refuses. This app is production-PRESENT, so
polarity is per-command: dev-world commands (verify_demo / verify_factory /
verify_feature) REFUSE outside the dev environment; verify_production and
verify_all run EVERYWHERE (environment-aware composition is VER-C logic, not a
guard concern). Pure functions first; one thin gather. No bypass flags exist.
"""

DEV_SETTINGS_MODULE = "config.settings.local"

# Polarity classes (contract §6.3 matrix — each cell negative-tested).
DEV_WORLD_COMMANDS = frozenset({"verify_demo", "verify_factory", "verify_feature"})
EVERYWHERE_COMMANDS = frozenset({"verify_production", "verify_all"})


def check_dev_settings_module(settings_module):
    if settings_module != DEV_SETTINGS_MODULE:
        return (
            f"settings module is '{settings_module}' — dev-world verify commands "
            f"run ONLY under '{DEV_SETTINGS_MODULE}' (seeded worlds are dev-only)"
        )
    return None


def check_dev_marker(debug):
    if not debug:
        return "DEBUG is False — dev-world verify commands need a development environment"
    return None


def polarity_failures(command, settings_module, debug):
    """Collect EVERY failing polarity factor (never short-circuit — the operator
    sees the whole wall). Everywhere-commands never refuse on environment."""
    if command in EVERYWHERE_COMMANDS:
        return []
    if command not in DEV_WORLD_COMMANDS:
        return [f"unknown verify command '{command}' — polarity undeclared"]
    failures = [
        check_dev_settings_module(settings_module),
        check_dev_marker(debug),
    ]
    return [f for f in failures if f]


def gather_and_check(command):
    """Thin impure layer: read real settings, run the pure polarity checks."""
    from django.conf import settings

    return polarity_failures(
        command,
        settings_module=getattr(settings, "SETTINGS_MODULE", ""),
        debug=settings.DEBUG,
    )


def environment():
    """The report-environment classifier (VER-C): 'dev' only under the dev
    settings module WITH the dev marker — anything else reports as 'prod'
    (a battery/test run classifies prod: DEBUG is False there, which is
    exactly why production-mode checks are testable in the battery)."""
    from django.conf import settings

    is_dev = (getattr(settings, "SETTINGS_MODULE", "") == DEV_SETTINGS_MODULE
              and settings.DEBUG)
    return "dev" if is_dev else "prod"
