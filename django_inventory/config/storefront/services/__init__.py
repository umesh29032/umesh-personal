"""storefront service layer.

Holds the ONE genuinely side-effecting write in this app — the Pillow image
crop/resize pipeline (image_service). (The old ListingService was a dead
single-row CRUD pass-through and was removed — Django's CBVs handle those.)
"""
from . import image_service

__all__ = ['image_service']
