from django.apps import AppConfig


class LearningConfig(AppConfig):
    """The course reader — a WINDOW over docs/*_course/*.md.

    Zero models by design (same posture as `bod` and `verification`): the
    markdown files are the single source of truth, this app only renders them.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learning'
    verbose_name = 'Learning (courses)'
