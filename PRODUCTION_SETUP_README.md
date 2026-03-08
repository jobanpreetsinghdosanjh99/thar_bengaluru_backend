# Production Database Setup - Quick Reference

## Overview

This repository contains two database initialization scripts:

### 1. `setup_production.py` - **FOR PRODUCTION USE**
- ✅ Runs schema migrations ONLY
- ✅ Creates necessary tables, columns, and indexes
- ✅ **NO TEST DATA** - safe for production
- ✅ Idempotent - safe to run multiple times

### 2. `seed.py` - **FOR DEVELOPMENT/TESTING ONLY**
- ⚠️ Runs schema migrations
- ⚠️ **INCLUDES TEST DATA** (users, events, products)
- ⚠️ Should **NEVER** be used in production
- ⚠️ Automatically runs on dev server startup

---

## Production Setup (setup_production.py)

### What It Does

1. **Users Table (UC003)**: Adds authentication columns
   - email_verified
   - is_banned
   - failed_login_attempts
   - OTP fields for password reset and email verification

2. **Accessories Table (UC004D)**: Adds vendor integration columns
   - vendor_id
   - long_description, images, features
   - brand, rating, reviews_count
   - compatibility, is_featured

3. **Merchandise Table (UC004E)**: Adds vendor integration columns
   - vendor_id
   - long_description, category, images
   - material, brand, rating, reviews
   - is_featured, is_on_sale, discounted_price

4. **Club Membership Requests (UC005)**: Adds full lifecycle columns
   - Personal info: residential_address, emergency_contact
   - Vehicle info: fuel_type, transmission_type
   - Document URLs: profile_photo, RC, insurance, aadhaar,DL
   - Payment: payment_status, payment_gateway, payment_order_id
   - Admin review: approved_by_admin_id, reviewed_at, rejection_reason
   - Activation: membership_id, whatsapp_group_link, activated_at
   - Creates index on membership_id

5. **TB Memberships (UC006)**: Verifies table and indexes
   - Creates index on membership_id

6. **Vendors**: Creates default vendor if none exists

7. **Backfills**: Ensures existing approved memberships are marked as active

---

## How to Run on Production Server

### Option 1: Python Module (Recommended)

```bash
# Navigate to backend directory
cd /path/to/thar_bengaluru_backend

# Activate virtual environment
source venv/bin/activate

# Run setup
python -c "from app.setup_production import setup_production_database; setup_production_database()"
```

### Option 2: Direct Script Execution

```bash
cd /path/to/thar_bengaluru_backend
source venv/bin/activate
python app/setup_production.py
```

### Expected Output

```
======================================================================
PRODUCTION DATABASE SETUP
======================================================================
This script will:
  1. Add missing columns for UC003, UC004D, UC004E, UC005, UC006
  2. Create necessary indexes
  3. Backfill existing data for consistency
  4. Create default vendor if needed

NOTE: NO TEST DATA will be inserted
======================================================================

[STEP 1] Setting up table schemas...
✓ [users] UC003 authentication columns exist
✓ [accessories] UC004D vendor columns exist
✓ [merchandise] UC004E vendor columns exist
✓ [club_membership_requests] UC005 lifecycle columns and indexes added
✓ [thar_bengaluru_memberships] UC006 indexes verified

[STEP 2] Verifying vendor setup...
✓ [vendors] Default vendor created (ID: 1)

[STEP 3] Backfilling vendor assignments...
✓ [backfill] All products already have vendor assignment

[STEP 4] Backfilling membership statuses...
✓ [backfill] All approved memberships already active

======================================================================
✓ PRODUCTION DATABASE SETUP COMPLETE
======================================================================
Database is ready for production use.
Next steps:
  1. Create admin user via /auth/register endpoint
  2. Manually promote user to admin role in database
  3. Start adding real events, accessories, merchandise
======================================================================
```

---

## Safety Features

### Idempotent Operations
- ✅ Safe to run multiple times
- ✅ Checks if columns already exist before adding
- ✅ Uses `IF NOT EXISTS` for indexes
- ✅ Skips operations that are already complete

### Zero Test Data
- ✅ No test users created
- ✅ No test events created
- ✅ No test products created
- ✅ Only creates a single default vendor (required for FK constraints)

### Non-Destructive
- ✅ Only adds columns, never drops
- ✅ Never deletes existing data
- ✅ Backfills are safe (only updates NULL values)

---

## After Running Setup

### 1. Create Admin User

**Via API:**
```bash
curl -X POST https://your-api.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin User",
    "email": "admin@yourdomain.com",
    "phone": "9999999999",
    "password": "YourStrongPassword123!"
  }'
```

**Promote to Admin (Database):**
```sql
-- Connect to database
psql thar_bengaluru_prod

-- Update user role
UPDATE users 
SET role = 'admin', email_verified = true
WHERE email = 'admin@yourdomain.com';
```

### 2. Verify Setup

```bash
# Check health endpoint
curl https://your-api.com/health

# Test login with admin user
curl -X POST https://your-api.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "YourStrongPassword123!"
  }'
```

---

## Troubleshooting

### Error: "Table does not exist"

If you get table does not exist errors, ensure SQLAlchemy models are loaded first:

```bash
# Create all tables from models
python -c "from app.database import engine; from app.models import models; models.Base.metadata.create_all(engine)"

# Then run setup
python app/setup_production.py
```

### Error: "Column already exists"

This is normal and safe. The script will skip existing columns:

```
✓ [users] UC003 authentication columns exist
```

### Error: "Cannot connect to database"

Check your .env file:

```bash
# Verify DATABASE_URL
cat .env | grep DATABASE_URL

# Test connection
PGPASSWORD="your_password" psql -U your_user -h localhost your_database -c "SELECT 1"
```

---

## Development vs Production

| Feature | `seed.py` (Dev) | `setup_production.py` (Prod) |
|---------|----------------|------------------------------|
| Schema migrations | ✅ Yes | ✅ Yes |
| Indexes | ✅ Yes | ✅ Yes |
| Backfills | ✅ Yes | ✅ Yes |
| Test users | ⚠️ YES (rajesh@test.com, admin@test.com) | ✅ NO |
| Test events | ⚠️ YES (5 events) | ✅ NO |
| Test products | ⚠️ YES (9 items) | ✅ NO |
| Test messages | ⚠️ YES (4 messages) | ✅ NO |
| Default vendor | ✅ YES (required) | ✅ YES (required) |
| Safe for production | ❌ NO | ✅ YES |

---

## Code Organization

### Table-Specific Methods

Each table has its own setup method:

- `setup_users_table(db)` - UC003 authentication
- `setup_accessories_table(db)` - UC004D vendor integration
- `setup_merchandise_table(db)` - UC004E vendor integration
- `setup_club_membership_table(db)` - UC005 membership lifecycle
- `setup_tb_membership_table(db)` - UC006 indexes

### Utility Methods

- `create_default_vendor_if_needed(db)` - Creates vendor for FK constraints
- `backfill_vendor_ids(db, vendor_id)` - Assigns vendor to products
- `backfill_approved_memberships_as_active(db)` - Activates approved members

### Main Entry Point

```python
setup_production_database()  # Orchestrates all setup steps
```

---

## Rollback

If you need to rollback changes, restore from database backup:

```bash
# Restore from backup
gunzip < /path/to/backup_YYYYMMDD.sql.gz | \
  psql -U your_user -h localhost your_database
```

**IMPORTANT**: Always create a database backup before running migrations!

```bash
pg_dump -U your_user -h localhost your_database | gzip > backup_before_setup_$(date +%Y%m%d).sql.gz
```

---

## Contact & Support

For issues or questions:
- Create an issue on GitHub
- Email: devops@tharbengaluru.com

---

**Last Updated**: March 8, 2026
