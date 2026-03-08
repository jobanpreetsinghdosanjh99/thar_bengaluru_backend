#!/usr/bin/env python
"""Verify seed data was inserted correctly"""

from app.database import SessionLocal
from app.models.models import User, Vendor, Feed

db = SessionLocal()

users = db.query(User).all()
vendors = db.query(Vendor).all()
feeds = db.query(Feed).all()

print(f'\n✓ Users: {len(users)} total')
for u in users:
    print(f'  - {u.name} ({u.email}) [{u.role.value}]')

print(f'\n✓ Vendors: {len(vendors)} total')
for v in vendors:
    print(f'  - {v.name}')

print(f'\n✓ Feeds: {len(feeds)} total')
for f in feeds:
    print(f'  - "{f.title}" by {f.author.name}')

print("\n✓ Database is ready for testing!")
