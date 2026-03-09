"""
Development/Testing Database Seed Script
Includes schema migrations AND test data
DO NOT RUN ON PRODUCTION - Use setup_production.py instead

This script runs automatically on development startup
"""

from sqlalchemy import text
from app.database import SessionLocal
from app.models.models import User, UserRole
from app.security import get_password_hash


def run_schema_migrations(db):
    """Run all schema migrations - delegates to setup_production.py logic"""
    from app.setup_production import (
        setup_users_table,
        setup_accessories_table,
        setup_merchandise_table,
        setup_club_membership_table,
        setup_tb_membership_table,
        backfill_approved_memberships_as_active
    )
    
    print("\n[DEVELOPMENT] Running schema migrations...")
    setup_users_table(db)
    setup_accessories_table(db)
    setup_merchandise_table(db)
    setup_club_membership_table(db)
    setup_tb_membership_table(db)
    backfill_approved_memberships_as_active(db)


def seed_vendors(db):
    """Seed test vendor data"""
    try:
        existing_vendor = db.execute(text("SELECT id FROM vendors ORDER BY id LIMIT 1")).fetchone()
        if not existing_vendor:
            db.execute(text("""
                INSERT INTO vendors (
                    name, email, whatsapp_number, payment_gateway, 
                    payment_gateway_url, status, created_at, updated_at
                ) VALUES (
                    'Trail Gear Vendor', 'vendor@test.com', '919999999999', 
                    'razorpay', 'https://payments.example.com/pay', 
                    'active', NOW(), NOW()
                )
            """))
            db.commit()
            print("✓ [vendors] Created test vendor")
            return db.execute(text("SELECT id FROM vendors ORDER BY id LIMIT 1")).fetchone()[0]
        else:
            print("✓ [vendors] Test vendor already exists")
            return existing_vendor[0]
    except Exception as e:
        db.rollback()
        print(f"✗ [vendors] Failed: {e}")
        return None


def seed_users(db):
    """Seed test users with verified emails (UC003)"""
    try:
        users_count = db.query(User).count()
        if users_count == 0:
            # Password: test1234 hashed with bcrypt
            test_users = [
                User(
                    name='Rajesh Kumar',
                    email='rajesh@test.com',
                    phone='9876543210',
                    password_hash='$2b$12$.HpI93vKuOnLeZTmXII6dO61IR3eFTmPrU.wPPEzU9TPBRVWOgcaC',
                    role=UserRole.USER,
                    email_verified=True,
                    is_banned=False,
                ),
                User(
                    name='Priya Singh',
                    email='priya@test.com',
                    phone='9876543211',
                    password_hash='$2b$12$.HpI93vKuOnLeZTmXII6dO61IR3eFTmPrU.wPPEzU9TPBRVWOgcaC',
                    role=UserRole.USER,
                    email_verified=True,
                    is_banned=False,
                ),
                User(
                    name='Arjun Patel',
                    email='arjun@test.com',
                    phone='9876543212',
                    password_hash='$2b$12$.HpI93vKuOnLeZTmXII6dO61IR3eFTmPrU.wPPEzU9TPBRVWOgcaC',
                    role=UserRole.USER,
                    email_verified=True,
                    is_banned=False,
                ),
            ]
            for user in test_users:
                db.add(user)
            db.commit()
            print("✓ [users] Created 3 test users (email verified)")
        else:
            print("✓ [users] Test users already exist")
        
        # Ensure admin user exists
        admin_user = db.query(User).filter(User.email == 'admin@test.com').first()
        if not admin_user:
            admin_user = User(
                name='Admin User',
                email='admin@test.com',
                phone='9000000000',
                password_hash=get_password_hash('test1234'),
                role=UserRole.ADMIN,
                email_verified=True,
                is_banned=False,
            )
            db.add(admin_user)
            db.commit()
            print("✓ [users] Created admin user (admin@test.com / test1234)")
        else:
            print("✓ [users] Admin user already exists")
            
        return True
        
    except Exception as e:
        db.rollback()
        print(f"✗ [users] Failed: {e}")
        return False


def seed_feeds(db):
    """Seed test feed posts"""
    try:
        from app.models.models import Feed
        
        feeds_count = db.query(Feed).count()
        if feeds_count == 0:
            # Get first user to use as author
            first_user = db.query(User).first()
            if not first_user:
                print("⚠ [feeds] No users found, skipping feed seeding")
                return False
            
            test_feeds = [
                Feed(
                    author_id=first_user.id,
                    title='Amazing Trail Experience',
                    content='Just finished an amazing trail expedition in the Western Ghats! The terrain was challenging but rewarding.',
                    image_url='https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=1200'
                ),
                Feed(
                    author_id=first_user.id,
                    title='New Suspension Upgrade',
                    content='New suspension upgrade installed! Feel the difference in every bump. Much smoother ride now.',
                    image_url='https://images.unsplash.com/photo-1493238792000-8113da705763?w=1200'
                ),
                Feed(
                    author_id=first_user.id,
                    title='Maintenance Tips for Monsoon',
                    content='Maintenance tips for monsoon season: Check your underbody for rust, ensure all seals are intact, and use synthetic oil. Stay prepared!',
                    image_url=None
                ),
            ]
            for feed in test_feeds:
                db.add(feed)
            db.commit()
            print("✓ [feeds] Created 3 test feeds")
        else:
            print("✓ [feeds] Test feeds already exist")
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ [feeds] Failed: {e}")
        return False


def seed_accessories(db, vendor_id):
    """Seed test accessories with vendor"""
    try:
        accessories_count = db.execute(text("SELECT COUNT(*) as count FROM accessories")).fetchone()
        if accessories_count.count == 0:
            db.execute(text(f"""
                INSERT INTO accessories (
                    vendor_id, name, description, category, price, stock, created_at
                ) VALUES
                ({vendor_id}, 'Front Bumper Guard', 'Heavy-duty front bumper protection', 'Bumpers', 15999, 45, NOW()),
                ({vendor_id}, 'LED Headlight Kit', 'Powerful LED headlights', 'Lighting', 12999, 28, NOW()),
                ({vendor_id}, 'Roof Rack - Aluminum', 'Heavy-duty roof cargo carrier', 'Racks', 16999, 22, NOW()),
                ({vendor_id}, 'Winch - 12000 lbs', 'Heavy-duty electric winch', 'Recovery', 28999, 15, NOW())
            """))
            db.commit()
            print("✓ [accessories] Created 4 test accessories")
        else:
            print("✓ [accessories] Test accessories already exist")
        
        # Backfill vendor_id for any accessories without it
        db.execute(text("UPDATE accessories SET vendor_id = :vendor_id WHERE vendor_id IS NULL"), {"vendor_id": vendor_id})
        db.commit()
        
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ [accessories] Failed: {e}")
        return False


def seed_merchandise(db, vendor_id):
    """Seed test merchandise with UC004E fields"""
    try:
        merchandise_count = db.execute(text("SELECT COUNT(*) as count FROM merchandise")).fetchone()
        if merchandise_count.count == 0:
            db.execute(text(f"""
                INSERT INTO merchandise 
                (vendor_id, name, description, long_description, category, price, stock, 
                 image_url, images, sizes, colors, features, material, brand, 
                 rating, reviews, is_featured, is_on_sale, created_at, updated_at) 
                VALUES
                ({vendor_id}, 'Thar Club Classic Tee', 
                 'Premium cotton t-shirt with club logo', 
                 'High-quality cotton t-shirt featuring the official Thar Bengaluru club emblem. Perfect for casual outings and club events.', 
                 'Apparel', 599, 156, 
                 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=1200', 
                 '[\"https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=1200\",\"https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=1200\"]',
                 '[[\"id\":\"s\",\"size\":\"S\",\"label\":\"Small\"],[\"id\":\"m\",\"size\":\"M\",\"label\":\"Medium\"],[\"id\":\"l\",\"size\":\"L\",\"label\":\"Large\"],[\"id\":\"xl\",\"size\":\"XL\",\"label\":\"Extra Large\"]]',
                 '[[\"id\":\"black\",\"name\":\"Black\",\"hex\":\"#000000\"],[\"id\":\"white\",\"name\":\"White\",\"hex\":\"#FFFFFF\"],[\"id\":\"olive\",\"name\":\"Olive\",\"hex\":\"#556B2F\"]]',
                 '[\"100% premium cotton\",\"Screen-printed club logo\",\"Breathable fabric\",\"Pre-shrunk\"]',
                 '100% Cotton', 'Thar Club', 4.5, 120, true, false, NOW(), NOW()),
                
                ({vendor_id}, 'Thar Adventure Hoodie', 
                 'Comfortable hoodie for club members', 
                 'Warm and cozy hoodie with embroidered Thar logo. Perfect for trail adventures and cool evenings.', 
                 'Hoodies', 1299, 89, 
                 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=1200',
                 '[\"https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=1200\",\"https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=1200\"]',
                 '[[\"id\":\"s\",\"size\":\"S\",\"label\":\"Small\"],[\"id\":\"m\",\"size\":\"M\",\"label\":\"Medium\"],[\"id\":\"l\",\"size\":\"L\",\"label\":\"Large\"],[\"id\":\"xl\",\"size\":\"XL\",\"label\":\"Extra Large\"]]',
                 '[[\"id\":\"charcoal\",\"name\":\"Charcoal\",\"hex\":\"#36454F\"],[\"id\":\"navy\",\"name\":\"Navy\",\"hex\":\"#000080\"],[\"id\":\"maroon\",\"name\":\"Maroon\",\"hex\":\"#800000\"]]',
                 '[\"Fleece-lined interior\",\"Embroidered logo\",\"Kangaroo pocket\",\"Adjustable drawstring hood\"]',
                 'Cotton Blend', 'Thar Club', 4.7, 95, true, false, NOW(), NOW()),
                
                ({vendor_id}, 'Thar Club Cap', 
                 'Adjustable baseball cap', 
                 'Classic adjustable cap with woven Thar logo patch. Protects from sun during off-road adventures.', 
                 'Caps', 349, 234, 
                 'https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=1200',
                 '[\"https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=1200\"]',
                 NULL,
                 '[[\"id\":\"black\",\"name\":\"Black\",\"hex\":\"#000000\"],[\"id\":\"tan\",\"name\":\"Tan\",\"hex\":\"#D2B48C\"],[\"id\":\"camo\",\"name\":\"Camo\",\"hex\":\"#78866B\"]]',
                 '[\"Adjustable strap\",\"Woven logo patch\",\"UV protection\",\"Breathable mesh back\"]',
                 'Cotton Canvas', 'Thar Club', 4.3, 230, false, false, NOW(), NOW()),
                
                ({vendor_id}, 'Off-Road Gloves', 
                 'Professional off-road driving gloves', 
                 'Durable gloves designed for extreme trail conditions. Enhanced grip and palm protection for confident driving.', 
                 'Accessories', 799, 145, 
                 'https://images.unsplash.com/photo-1581345678689-0af13c93bb89?w=1200',
                 '[\"https://images.unsplash.com/photo-1581345678689-0af13c93bb89?w=1200\"]',
                 '[[\"id\":\"m\",\"size\":\"M\",\"label\":\"Medium\"],[\"id\":\"l\",\"size\":\"L\",\"label\":\"Large\"],[\"id\":\"xl\",\"size\":\"XL\",\"label\":\"Extra Large\"]]',
                 '[[\"id\":\"black\",\"name\":\"Black\",\"hex\":\"#000000\"]]',
                 '[\"Reinforced palm\",\"Breathable mesh\",\"Touchscreen compatible\",\"Padded knuckles\"]',
                 'Synthetic Leather', 'TrailGear Pro', 4.6, 87, true, false, NOW(), NOW()),
                
                ({vendor_id}, 'Thar Club Sticker Pack', 
                 'Vinyl sticker collection', 
                 'Set of 5 waterproof vinyl stickers featuring various Thar Club designs. Perfect for personalizing vehicles and gear.', 
                 'Stickers', 149, 500, 
                 'https://images.unsplash.com/photo-1572375992501-4b0892d50c69?w=1200',
                 '[\"https://images.unsplash.com/photo-1572375992501-4b0892d50c69?w=1200\"]',
                 NULL, NULL,
                 '[\"5 unique designs\",\"Waterproof vinyl\",\"UV resistant\",\"Easy peel backing\"]',
                 'Vinyl', 'Thar Club', 4.8, 312, false, true, NOW(), NOW())
            """))
            db.commit()
            print("✓ [merchandise] Created 5 test merchandise items")
        else:
            print("✓ [merchandise] Test merchandise already exist")
        
        # Backfill vendor_id for any merchandise without it
        db.execute(text("UPDATE merchandise SET vendor_id = :vendor_id WHERE vendor_id IS NULL"), {"vendor_id": vendor_id})
        db.commit()
        
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ [merchandise] Failed: {e}")
        return False


def seed_vehicles(db):
    """Seed test vehicles for members (UC004)"""
    try:
        vehicles_count = db.execute(text("SELECT COUNT(*) as count FROM vehicles")).fetchone()
        if vehicles_count.count == 0:
            users = db.execute(text("SELECT id FROM users ORDER BY id LIMIT 3")).fetchall()
            if len(users) >= 3:
                user_ids = [u[0] for u in users]
                db.execute(text(f"""
                    INSERT INTO vehicles (
                        user_id, make, model, year, registration_number, 
                        color, mileage, is_primary, created_at
                    ) VALUES
                    ({user_ids[0]}, 'Mahindra', 'Thar', '2023', 'KA-03-NM-4040', 'Red', 15000, true, NOW()),
                    ({user_ids[1]}, 'Mahindra', 'Thar', '2022', 'MH-02-AB-5050', 'Blue', 20000, true, NOW()),
                    ({user_ids[2]}, 'Mahindra', 'Bolero', '2021', 'DL-01-CD-6060', 'White', 25000, true, NOW())
                """))
                db.commit()
                print("✓ [vehicles] Created 3 test vehicles")
            else:
                print("⚠ [vehicles] Insufficient users for seeding")
        else:
            print("✓ [vehicles] Test vehicles already exist")
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ [vehicles] Failed: {e}")
        return False


def seed_messages(db):
    """Seed test messages between users (UC004)"""
    try:
        messages_count = db.execute(text("SELECT COUNT(*) as count FROM messages")).fetchone()
        if messages_count.count == 0:
            users = db.execute(text("SELECT id FROM users ORDER BY id LIMIT 3")).fetchall()
            if len(users) >= 3:
                user_ids = [u[0] for u in users]
                db.execute(text(f"""
                    INSERT INTO messages (sender_id, receiver_id, content, is_read, created_at) VALUES
                    ({user_ids[0]}, {user_ids[1]}, 'Hey! How are you doing? Wanna go for a trail this weekend?', true, NOW() - INTERVAL '2 days'),
                    ({user_ids[1]}, {user_ids[0]}, 'Hi! I am good. Yes, sounds fun! When are you available?', true, NOW() - INTERVAL '1 days'),
                    ({user_ids[0]}, {user_ids[1]}, 'How about Saturday morning? We can start from Bangalore', false, NOW() - INTERVAL '1 hours'),
                    ({user_ids[0]}, {user_ids[2]}, 'Interested in joining us for the upcoming expedition?', false, NOW())
                """))
                db.commit()
                print("✓ [messages] Created 4 test messages")
            else:
                print("⚠ [messages] Insufficient users for seeding")
        else:
            print("✓ [messages] Test messages already exist")
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ [messages] Failed: {e}")
        return False


def seed_events(db):
    """Seed test events with varied difficulty levels (UC004B)"""
    try:
        events_count = db.execute(text("SELECT COUNT(*) as count FROM events")).fetchone()
        if events_count.count == 0:
            first_user = db.execute(text("SELECT id FROM users ORDER BY id LIMIT 1")).fetchone()
            if first_user:
                creator_id = first_user[0]
                db.execute(text(f"""
                    INSERT INTO events (
                        name, description, event_date, location, 
                        difficulty_level, required_vehicle_type, max_participants, current_participants,
                        registration_deadline, event_fee, per_person_charge, 
                        safety_requirements, image_url, created_by, status, created_at, updated_at
                    ) VALUES
                    (
                        'Weekend Trail to Nandi Hills',
                        'Join us for an exciting morning trail to Nandi Hills. Experience breathtaking sunrise views and challenging off-road terrain. Perfect for beginners and experienced riders alike.',
                        NOW() + INTERVAL '15 days',
                        'Nandi Hills, Karnataka',
                        'EASY',
                        '4x4 SUV',
                        20, 0,
                        NOW() + INTERVAL '10 days',
                        1500.00, 500.00,
                        'Basic safety gear, First aid kit, Valid driving license',
                        'https://example.com/nandi-hills.jpg',
                        {creator_id},
                        'PUBLISHED',
                        NOW(), NOW()
                    ),
                    (
                        'Coorg Adventure Expedition',
                        'Multi-day expedition through the coffee plantations and mountains of Coorg. Includes camping, bonfire, and authentic Coorgi cuisine. Limited slots available!',
                        NOW() + INTERVAL '30 days',
                        'Coorg, Karnataka',
                        'MODERATE',
                        '4x4 SUV with high ground clearance',
                        15, 0,
                        NOW() + INTERVAL '20 days',
                        3500.00, 1500.00,
                        'Emergency medical kit, Camping gear, Recovery equipment, CB Radio',
                        'https://example.com/coorg-expedition.jpg',
                        {creator_id},
                        'PUBLISHED',
                        NOW(), NOW()
                    ),
                    (
                        'Dandeli River Crossing Challenge',
                        'Extreme off-road challenge with river crossings, rocky terrain, and steep climbs. Recommended for experienced drivers only. Professional marshals will be present.',
                        NOW() + INTERVAL '45 days',
                        'Dandeli, Karnataka',
                        'DIFFICULT',
                        'Modified 4x4 with snorkel and winch',
                        10, 0,
                        NOW() + INTERVAL '35 days',
                        5000.00, 2000.00,
                        'Advanced recovery gear, Winch, Snorkel, CB Radio, Emergency contact, Medical insurance',
                        'https://example.com/dandeli-challenge.jpg',
                        {creator_id},
                        'PUBLISHED',
                        NOW(), NOW()
                    ),
                    (
                        'Night Drive Experience - Kolar',
                        'Experience the thrill of night driving through forest trails near Kolar. Navigate with headlights and spotlights through challenging terrain.',
                        NOW() + INTERVAL '7 days',
                        'Kolar Gold Fields, Karnataka',
                        'MODERATE',
                        '4x4 SUV',
                        12, 0,
                        NOW() + INTERVAL '5 days',
                        2000.00, 800.00,
                        'Working spotlights, GPS device, Emergency beacon, First aid',
                        'https://example.com/night-drive.jpg',
                        {creator_id},
                        'PUBLISHED',
                        NOW(), NOW()
                    ),
                    (
                        'Future Expedition - TBD',
                        'Planning stage expedition. Details will be announced soon. Register your interest!',
                        NOW() + INTERVAL '60 days',
                        'To be decided',
                        'MODERATE',
                        '4x4 SUV',
                        25, 0,
                        NOW() + INTERVAL '50 days',
                        0.00, 0.00,
                        'TBD',
                        'https://example.com/placeholder.jpg',
                        {creator_id},
                        'DRAFT',
                        NOW(), NOW()
                    )
                """))
                db.commit()
                print("✓ [events] Created 5 test events (4 published, 1 draft)")
            else:
                print("⚠ [events] No users found for event creator")
        else:
            print("✓ [events] Test events already exist")
        return True
    except Exception as e:
        db.rollback()
        print(f"✗ [events] Failed: {e}")
        return False


def seed_data():
    """
    Main seed function for development/testing ONLY
    Runs schema migrations + inserts test data
    """
    print("=" * 70)
    print("DEVELOPMENT DATABASE SEED")
    print("=" * 70)
    print("WARNING: This includes TEST DATA - for development only!")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Step 1: Run schema migrations
        run_schema_migrations(db)
        
        # Step 2: Check if we already have data
        accessories_count = db.execute(text("SELECT COUNT(*) as count FROM accessories")).fetchone()
        merchandise_count = db.execute(text("SELECT COUNT(*) as count FROM merchandise")).fetchone()
        
        if accessories_count.count > 0 and merchandise_count.count > 0:
            print("\n✓ Database already has product seed data")
        
        print("\n[DEVELOPMENT] Seeding test data...")
        
        # Step 3: Seed all test data
        vendor_id = seed_vendors(db)
        seed_users(db)
        seed_feeds(db)
        
        if vendor_id:
            seed_accessories(db, vendor_id)
            seed_merchandise(db, vendor_id)
        
        seed_vehicles(db)
        seed_messages(db)
        seed_events(db)
        
        print("\n" + "=" * 70)
        print("✓ DEVELOPMENT DATABASE SEED COMPLETE")
        print("=" * 70)
        print("\nTest credentials:")
        print("  User: rajesh@test.com / test1234")
        print("  Admin: admin@test.com / test1234")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ SEED FAILED: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
