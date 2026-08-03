"""Audit-close 2026-07-11 (FOUNDATION_V1_AUDIT §5.2): the template-
comment leak class gets a PERMANENT guard. Django `{# #}` comments are
single-line ONLY — a multi-line `{# ... #}` inside a `{% block %}`
renders its tail as visible page text (bit this project 3×: M4 five
leaks, M5 two more). Outside/above the first block it is discarded by
template inheritance (harmless — the documented file-header idiom).
Guard: refuse any multi-line `{#` opened AFTER the first `{% block %}`
in every patterns_ai template. Multi-line commentary inside blocks
belongs in `{% comment %}…{% endcomment %}`."""
from pathlib import Path

from django.test import SimpleTestCase

TEMPLATES = Path(__file__).resolve().parents[1] / 'templates'


class TemplateCommentLeakGuardTests(SimpleTestCase):
    def test_no_multiline_hash_comments_inside_blocks(self):
        offenders = []
        for tpl in sorted(TEMPLATES.rglob('*.html')):
            text = tpl.read_text(errors='ignore')
            first_block = text.find('{% block')
            pos = 0
            while True:
                start = text.find('{#', pos)
                if start == -1:
                    break
                end = text.find('#}', start)
                if end == -1:                     # unclosed = worst leak
                    offenders.append(f'{tpl.name}: unclosed {{# at '
                                     f'offset {start}')
                    break
                if ('\n' in text[start:end]
                        and first_block != -1 and start > first_block):
                    line = text.count('\n', 0, start) + 1
                    offenders.append(f'{tpl.name}:{line}: multi-line '
                                     '{# #} inside a block — leaks as '
                                     'page text; use {% comment %}')
                pos = end + 2
        self.assertEqual(offenders, [],
                         'template comment leaks found:\n'
                         + '\n'.join(offenders))
