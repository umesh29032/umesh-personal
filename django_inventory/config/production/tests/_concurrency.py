"""Threaded-transaction helper for concurrency tests — M0.3 infra, used by M1.

M1 (WF-4) adds row-level locking to stage completion/advance. Proving
"two concurrent completers → exactly one wins, no double-advance / double-freeze"
needs REAL parallel DB transactions. Tests using this MUST subclass
TransactionTestCase (threads commit to a shared DB; a plain TestCase wraps each
test in one transaction, which would deadlock or hide the race).

    from production.tests._concurrency import run_in_parallel
    results = run_in_parallel([lambda: advance(...), lambda: advance(...)])
    survivors = [r for r, exc in results if exc is None]
    self.assertEqual(len(survivors), 1)   # one wins; the other raises/no-ops

Underscore-prefixed so Django's test discovery (test*.py) never collects it.
"""
import threading

from django.db import connections


def run_in_parallel(fns, *, timeout=10):
    """Run each callable in its own thread, released simultaneously via a barrier
    so they genuinely contend for the same rows. Returns [(result, exception), ...]
    in input order. Each thread closes its own DB connections on exit.
    """
    n = len(fns)
    barrier = threading.Barrier(n)
    results = [(None, None)] * n

    def make_runner(index, fn):
        def runner():
            try:
                barrier.wait(timeout=timeout)
                results[index] = (fn(), None)
            except Exception as exc:
                results[index] = (None, exc)
            finally:
                connections.close_all()
        return runner

    threads = [threading.Thread(target=make_runner(i, fn)) for i, fn in enumerate(fns)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=timeout + 5)
    return results
