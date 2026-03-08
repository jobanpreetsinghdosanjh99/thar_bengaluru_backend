"""
Production Database Setup Script
Runs schema migrations and indexes ONLY - NO TEST DATA
Safe to run on production databases

Run manually with: python -c "from app.setup_production import setup_production_database; setup_production_database()"
"""

from sqlalchemy import text
from app.database import SessionLocal


def setup_users_table(db):
    """Setup users table with UC003 authentication columns"""
    try:
        db.execute(text("SELECT email_verified FROM users LIMIT 1"))
        print("✓ [users] UC003 authentication columns exist")
        return True
    except Exception:
        db.rollback()
        
    try:
        print("⟳ [users] Adding UC003 authentication columns...")
        
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS last_failed_login_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS email_verification_otp VARCHAR(6),
            ADD COLUMN IF NOT EXISTS email_verification_otp_expires_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS password_reset_otp VARCHAR(6),
            ADD COLUMN IF NOT EXISTS password_reset_otp_expires_at TIMESTAMP
        """))
        
        db.commit()
        print("✓ [users] UC003 authentication columns added")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"✗ [users] Migration failed: {e}")
        return False


def setup_accessories_table(db):
    """Setup accessories table with UC004D vendor integration columns"""
    try:
        db.execute(text("SELECT vendor_id, long_description, images, features, compatibility, brand, rating, reviews_count, is_featured FROM accessories LIMIT 1"))
        print("✓ [accessories] UC004D vendor columns exist")
        return True
    except Exception:
        db.rollback()
    
    try:
        print("⟳ [accessories] Adding UC004D vendor integration columns...")
        
        db.execute(text("""
            ALTER TABLE accessories 
            ADD COLUMN IF NOT EXISTS vendor_id INTEGER,
            ADD COLUMN IF NOT EXISTS long_description TEXT,
            ADD COLUMN IF NOT EXISTS images VARCHAR(2000),
            ADD COLUMN IF NOT EXISTS features VARCHAR(2000),
            ADD COLUMN IF NOT EXISTS compatibility VARCHAR(500),
            ADD COLUMN IF NOT EXISTS brand VARCHAR(100),
            ADD COLUMN IF NOT EXISTS rating FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS reviews_count INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE
        """))
        
        db.commit()
        print("✓ [accessories] UC004D vendor columns added")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"✗ [accessories] Migration failed: {e}")
        return False


def setup_merchandise_table(db):
    """Setup merchandise table with UC004E vendor integration columns"""
    try:
        db.execute(text("SELECT vendor_id, long_description, category, images, features, material, brand, rating, reviews, is_featured, is_on_sale, discounted_price FROM merchandise LIMIT 1"))
        print("✓ [merchandise] UC004E vendor columns exist")
        return True
    except Exception:
        db.rollback()
    
    try:
        print("⟳ [merchandise] Adding UC004E vendor integration columns...")
        
        db.execute(text("""
            ALTER TABLE merchandise 
            ADD COLUMN IF NOT EXISTS vendor_id INTEGER,
            ADD COLUMN IF NOT EXISTS long_description TEXT,
            ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'Apparel',
            ADD COLUMN IF NOT EXISTS images VARCHAR(2000),
            ADD COLUMN IF NOT EXISTS features VARCHAR(2000),
            ADD COLUMN IF NOT EXISTS material VARCHAR(100),
            ADD COLUMN IF NOT EXISTS brand VARCHAR(100),
            ADD COLUMN IF NOT EXISTS rating FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS reviews INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS is_on_sale BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS discounted_price FLOAT
        """))
        
        db.commit()
        print("✓ [merchandise] UC004E vendor columns added")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"✗ [merchandise] Migration failed: {e}")
        return False


def setup_club_membership_table(db):
    """Setup club_membership_requests table with UC005 full lifecycle columns"""
    try:
        db.execute(text("SELECT payment_status, membership_id, whatsapp_group_link, terms_accepted FROM club_membership_requests LIMIT 1"))
        print("✓ [club_membership_requests] UC005 lifecycle columns exist")
        return True
    except Exception:
        db.rollback()
    
    try:
        print("⟳ [club_membership_requests] Adding UC005 membership lifecycle columns...")
        
        db.execute(text("""
            ALTER TABLE club_membership_requests 
            ADD COLUMN IF NOT EXISTS residential_address TEXT,
            ADD COLUMN IF NOT EXISTS emergency_contact VARCHAR(15),
            ADD COLUMN IF NOT EXISTS vehicle_fuel_type VARCHAR(20),
            ADD COLUMN IF NOT EXISTS vehicle_transmission_type VARCHAR(20),
            ADD COLUMN IF NOT EXISTS profile_photo_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS rc_document_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS insurance_document_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS aadhaar_document_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS driving_license_document_url VARCHAR(500),
            ADD COLUMN IF NOT EXISTS vehicle_modifications TEXT,
            ADD COLUMN IF NOT EXISTS additional_info TEXT,
            ADD COLUMN IF NOT EXISTS terms_accepted BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS workshop_trail_completed BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS payment_gateway VARCHAR(50),
            ADD COLUMN IF NOT EXISTS payment_order_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS payment_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS payment_link_enabled BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS approved_by_admin_id INTEGER,
            ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS rejection_reason TEXT,
            ADD COLUMN IF NOT EXISTS membership_id VARCHAR(100),
            ADD COLUMN IF NOT EXISTS whatsapp_group_name VARCHAR(255),
            ADD COLUMN IF NOT EXISTS whatsapp_group_link VARCHAR(500),
            ADD COLUMN IF NOT EXISTS whatsapp_join_available BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS activated_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS audit_log TEXT
        """))
        
        # Create index on membership_id for fast lookups
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_club_membership_requests_membership_id 
            ON club_membership_requests (membership_id)
        """))
        
        db.commit()
        print("✓ [club_membership_requests] UC005 lifecycle columns and indexes added")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"✗ [club_membership_requests] Migration failed: {e}")
        return False


def setup_tb_membership_table(db):
    """Setup thar_bengaluru_memberships table with UC006 indexes"""
    try:
        db.execute(text("SELECT payment_status, membership_id, whatsapp_group_link FROM thar_bengaluru_memberships LIMIT 1"))
        print("✓ [thar_bengaluru_memberships] UC006 table queryable")
        
        # Ensure index exists
        try:
            db.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_tb_memberships_membership_id 
                ON thar_bengaluru_memberships (membership_id)
            """))
            db.commit()
            print("✓ [thar_bengaluru_memberships] UC006 indexes verified")
        except Exception:
            db.rollback()
        
        return True
        
    except Exception:
        db.rollback()
        print("⚠ [thar_bengaluru_memberships] Table not yet created (will be created on first app startup)")
        return True


def backfill_approved_memberships_as_active(db):
    """
    Backfill existing approved memberships to active status
    Safe to run multiple times (idempotent)
    """
    try:
        print("⟳ [backfill] Ensuring approved memberships are marked as active...")
        
        # UC005: Club memberships
        result = db.execute(text("""
            UPDATE club_membership_requests 
            SET 
                payment_status = 'success',
                payment_link_enabled = TRUE
            WHERE 
                status = 'APPROVED' 
                AND (payment_status IS NULL OR payment_status IN ('', 'pending'))
        """))
        club_updated = result.rowcount
        
        # UC006: TB memberships
        result = db.execute(text("""
            UPDATE thar_bengaluru_memberships 
            SET 
                payment_status = 'success',
                payment_link_enabled = TRUE
            WHERE 
                status = 'APPROVED' 
                AND (payment_status IS NULL OR payment_status IN ('', 'pending'))
        """))
        tb_updated = result.rowcount
        
        db.commit()
        
        if club_updated > 0 or tb_updated > 0:
            print(f"✓ [backfill] Updated {club_updated} club + {tb_updated} TB memberships to active")
        else:
            print("✓ [backfill] All approved memberships already active")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"⚠ [backfill] Could not update memberships: {e}")
        return True  # Non-critical, continue


def create_default_vendor_if_needed(db):
    """
    Create a default vendor if none exists
    Required for accessories and merchandise with vendor_id FK
    """
    try:
        existing_vendor = db.execute(text("SELECT id FROM vendors ORDER BY id LIMIT 1")).fetchone()
        
        if existing_vendor:
            print(f"✓ [vendors] Default vendor exists (ID: {existing_vendor[0]})")
            return existing_vendor[0]
        
        print("⟳ [vendors] Creating default vendor...")
        
        db.execute(text("""
            INSERT INTO vendors (
                name, 
                email, 
                whatsapp_number, 
                payment_gateway, 
                payment_gateway_url, 
                status, 
                created_at, 
                updated_at
            ) VALUES (
                'Default Vendor', 
                'vendor@tharbengaluru.com', 
                '919999999999', 
                'razorpay', 
                'https://razorpay.com', 
                'active', 
                NOW(), 
                NOW()
            )
        """))
        
        db.commit()
        
        vendor = db.execute(text("SELECT id FROM vendors ORDER BY id LIMIT 1")).fetchone()
        print(f"✓ [vendors] Default vendor created (ID: {vendor[0]})")
        return vendor[0]
        
    except Exception as e:
        db.rollback()
        print(f"✗ [vendors] Failed to create default vendor: {e}")
        return None


def backfill_vendor_ids(db, vendor_id):
    """
    Backfill vendor_id for existing accessories and merchandise
    """
    try:
        # Accessories
        result = db.execute(text("""
            UPDATE accessories 
            SET vendor_id = :vendor_id 
            WHERE vendor_id IS NULL
        """), {"vendor_id": vendor_id})
        acc_updated = result.rowcount
        
        # Merchandise
        result = db.execute(text("""
            UPDATE merchandise 
            SET vendor_id = :vendor_id 
            WHERE vendor_id IS NULL
        """), {"vendor_id": vendor_id})
        merch_updated = result.rowcount
        
        db.commit()
        
        if acc_updated > 0 or merch_updated > 0:
            print(f"✓ [backfill] Assigned vendor to {acc_updated} accessories + {merch_updated} merchandise")
        else:
            print("✓ [backfill] All products already have vendor assignment")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"⚠ [backfill] Could not assign vendor: {e}")
        return True  # Non-critical


def setup_production_database():
    """
    Main production database setup function
    Safe to run on empty or existing databases
    Does NOT insert any test data
    """
    print("=" * 70)
    print("PRODUCTION DATABASE SETUP")
    print("=" * 70)
    print("This script will:")
    print("  1. Add missing columns for UC003, UC004D, UC004E, UC005, UC006")
    print("  2. Create necessary indexes")
    print("  3. Backfill existing data for consistency")
    print("  4. Create default vendor if needed")
    print("\nNOTE: NO TEST DATA will be inserted")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Step 1: Setup all tables
        print("\n[STEP 1] Setting up table schemas...")
        setup_users_table(db)
        setup_accessories_table(db)
        setup_merchandise_table(db)
        setup_club_membership_table(db)
        setup_tb_membership_table(db)
        
        # Step 2: Create default vendor
        print("\n[STEP 2] Verifying vendor setup...")
        vendor_id = create_default_vendor_if_needed(db)
        
        # Step 3: Backfill data
        if vendor_id:
            print("\n[STEP 3] Backfilling vendor assignments...")
            backfill_vendor_ids(db, vendor_id)
        
        print("\n[STEP 4] Backfilling membership statuses...")
        backfill_approved_memberships_as_active(db)
        
        print("\n" + "=" * 70)
        print("✓ PRODUCTION DATABASE SETUP COMPLETE")
        print("=" * 70)
        print("Database is ready for production use.")
        print("Next steps:")
        print("  1. Create admin user via /auth/register endpoint")
        print("  2. Manually promote user to admin role in database")
        print("  3. Start adding real events, accessories, merchandise")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ SETUP FAILED: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    setup_production_database()
