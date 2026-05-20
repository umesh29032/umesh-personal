"""accounts app ke signal handlers.

YEH FILE KYU HAI?
─────────────────
Spec D8 — retro-tag: jab koi user pe `cutting_master` ya `cutting_master_helper`
skill add hoti hai, woh user automatic active Layering stage_records ke workers
M2M mein add ho jaata hai.

Trigger: `m2m_changed` signal on `User.skills` (post_add action).

Kyun service layer mein nahi rakha?
  M2M edits aksar admin UI / shell se hote hain. View layer pe wrapper rakhne ka
  matlab hai admin form bhi business logic call kare. Signal cleaner — har M2M
  edit path automatically retro-tag chalata hai.

Race / ordering:
  m2m_changed `post_add` fires AFTER M2M row inserted. So when we query
  `user.skills`, the newly-added skill is already there. Safe to call
  `sync_layering_workers_for_skill`.
"""
from __future__ import annotations

from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from accounts.models import User


@receiver(m2m_changed, sender=User.skills.through)
def on_user_skill_change(sender, instance, action, reverse, pk_set, **kwargs):
    """Skill add hote hi user ko active Layerings mein retro-tag karo.

    Signal fires for both directions (User.skills.add(skill) vs Skill.users.add(user)).
    `reverse=False` → instance is User. `reverse=True` → instance is Skill, pk_set is users.

    `action`:
      • `post_add` — naya skill attach hua → retro-tag chalao
      • `post_remove` / `post_clear` — handle nahi karte (M2M historical record bana rahta)
      • `pre_*` actions — skip (M2M not yet committed)
    """
    if action != 'post_add' or not pk_set:
        return

    # Lazy import — accounts can be loaded before production app is ready
    try:
        from production.services import sync_layering_workers_for_skill
    except ImportError:
        return

    if reverse:
        # Skill object on which users are being added — iterate users
        for user_pk in pk_set:
            try:
                user_obj = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                continue
            sync_layering_workers_for_skill(user_obj)
    else:
        # Forward direction — instance IS the user; new skills landing in pk_set
        sync_layering_workers_for_skill(instance)
