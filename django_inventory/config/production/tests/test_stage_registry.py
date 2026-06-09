"""M2.1: stage-engine seam — registry + StageHandler contract.

Pure scaffolding for the M2 refactor; nothing in the running app uses it yet.
These tests pin the registry behavior the rest of M2 builds on.
"""
from decimal import Decimal

from django.test import SimpleTestCase

from production.stages import base
from production.stages.base import CompletionResult, StageHandler, WorkerAllocation


class _DummyHandler(StageHandler):
    code = 'dummy_stage'
    name = 'Dummy'
    template_partial = 'x.html'
    pays_workers = True

    def panel_context(self, adda, record):
        return {}

    def start(self, *, user_id, adda, record, data):
        return record

    def complete(self, *, user_id, adda, record, data):
        return CompletionResult(allocations=[WorkerAllocation(worker_id=user_id, quantity=Decimal('1'))])

    def reopen(self, *, user_id, record):
        from production.stages.base import ReopenResult
        return ReopenResult()

    def cost_quantity(self, record):
        return Decimal('0')


class StageRegistryTest(SimpleTestCase):
    def setUp(self):
        self._saved = base.all_handlers()   # snapshot real handlers (none yet in M2.1)
        base.clear()

    def tearDown(self):
        base.clear()
        for h in self._saved.values():
            base.register(h)

    def test_register_and_get_roundtrip(self):
        base.register(_DummyHandler)               # class form (instantiated once)
        self.assertTrue(base.has('dummy_stage'))
        handler = base.get('dummy_stage')
        self.assertIsInstance(handler, _DummyHandler)
        self.assertIn('dummy_stage', base.all_handlers())

    def test_get_unknown_raises(self):
        with self.assertRaises(KeyError):
            base.get('nope')

    def test_duplicate_code_raises(self):
        base.register(_DummyHandler)
        with self.assertRaises(ValueError):
            base.register(_DummyHandler())          # different instance, same code

    def test_blank_code_rejected(self):
        class _NoCode(_DummyHandler):
            code = ''
        with self.assertRaises(ValueError):
            base.register(_NoCode)

    def test_abstract_handler_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            StageHandler()                          # missing abstract methods

    def test_completion_result_carries_primitive_allocations(self):
        handler = _DummyHandler()
        out = handler.complete(user_id=7, adda=None, record=None, data={})
        self.assertEqual(len(out.allocations), 1)
        self.assertEqual(out.allocations[0].worker_id, 7)
        self.assertEqual(out.allocations[0].quantity, Decimal('1'))

    def test_autodiscover_is_safe_with_no_stage_packages(self):
        base.autodiscover()                         # M2.1: no stage dirs yet -> no-op, no crash
