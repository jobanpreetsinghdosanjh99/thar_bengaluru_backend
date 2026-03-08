"""
Seed script to populate initial test data
Runs on application startup if data doesn't exist
"""

from sqlalchemy import text
from app.database import SessionLocal
from app.models.models import User, UserRole
from app.security import get_password_hash


def seed_data():
    """Populate database with test data using SQL"""
    db = SessionLocal()
    
    try:
        # Ensure new UC003 columns exist (for existing databases) - UC003 feature
        try:
            db.execute(text("SELECT email_verified FROM users LIMIT 1"))
            print("[Check] UC003 columns already exist in users table")
        except Exception as e:
            # Columns don't exist yet, add them
            db.rollback()  # Rollback failed transaction
            try:
                db.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE"))
                db.execute(text("ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE"))
                db.execute(text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
                db.execute(text("ALTER TABLE users ADD COLUMN last_failed_login_at TIMESTAMP"))
                db.execute(text("ALTER TABLE users ADD COLUMN email_verification_otp VARCHAR(6)"))
                db.execute(text("ALTER TABLE users ADD COLUMN email_verification_otp_expires_at TIMESTAMP"))
                db.execute(text("ALTER TABLE users ADD COLUMN password_reset_otp VARCHAR(6)"))
                db.execute(text("ALTER TABLE users ADD COLUMN password_reset_otp_expires_at TIMESTAMP"))
                db.commit()
                print("[Migration] Added UC003 columns to users table")
            except Exception as migration_error:
                db.rollback()
                print(f"[Migration] Columns may already exist or migration issue: {migration_error}")

        # Ensure UC004D accessory table has required columns for current model
        try:
            db.execute(text("SELECT vendor_id, long_description, images, features, compatibility, brand, rating, reviews_count, is_featured FROM accessories LIMIT 1"))
            print("[Check] UC004D accessory columns already exist")
        except Exception:
            db.rollback()
            try:
                db.execute(text("ALTER TABLE accessories ADD COLUMN IF NOT EXISTS vendor_id INTEGER"))
                db.execute(text("ALTER TABLE accessories ADD COLUMN IF NOT EXISTS long_description TEXT"))
                db.execute(text("ALTER TABLE accessories ADD COLUMN IF NOT EXISTS images VARCHAR(2000)"))
                db.execute(text("ALTER TABLE accessories ADD COLUMN IF NOT EXISTS features VARCHAR(2000)"))
                db.execute(text("ALTER TABLE accessories ADD COLUMN IF NOT EXISTS compatibility VARCHAR(500)"))
                db.execute(text("ALTER TABLE accessories ADD COLUMN IF NOT EXISTS brand VARCHAR(100)"))
                db.execute(text("ALTER TABLE accessories ADD COLUMN IF NOT EXISTS rating FLOAT DEFAULT 0.0"))
                db.execute(text("ALTER TABLE accessories ADD COLUMN IF NOT EXISTS reviews_count INTEGER DEFAULT 0"))
                db.execute(text("ALTER TABLE accessories ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE"))
                db.commit()
                print("[Migration] Added missing UC004D accessory columns")
            except Exception as migration_error:
                db.rollback()
                print(f"[Migration] UC004D accessory column migration issue: {migration_error}")

        # Ensure accessories are linked to at least one vendor for checkout flows
        try:
            existing_vendor = db.execute(text("SELECT id FROM vendors ORDER BY id LIMIT 1")).fetchone()
            if not existing_vendor:
                db.execute(text("""
                    INSERT INTO vendors (name, email, whatsapp_number, payment_gateway, payment_gateway_url, status, created_at, updated_at)
                    VALUES ('Trail Gear Vendor', 'vendor@test.com', '919999999999', 'razorpay', 'https://payments.example.com/pay', 'active', NOW(), NOW())
                """))
                db.commit()
                existing_vendor = db.execute(text("SELECT id FROM vendors ORDER BY id LIMIT 1")).fetchone()
                print("[Seed] Created default UC004D vendor")

            if existing_vendor:
                db.execute(text("UPDATE accessories SET vendor_id = :vendor_id WHERE vendor_id IS NULL"), {"vendor_id": existing_vendor[0]})
                db.commit()
                print("[Seed] Backfilled vendor_id for existing accessories")
        except Exception as vendor_backfill_error:
            db.rollback()
            print(f"[Seed] UC004D vendor backfill issue: {vendor_backfill_error}")
        
        # Check if accessories/merchandise exist
        accessories_count = db.execute(text("SELECT COUNT(*) as count FROM accessories")).fetchone()
        merchandise_count = db.execute(text("SELECT COUNT(*) as count FROM merchandise")).fetchone()
        
        if accessories_count.count > 0 and merchandise_count.count > 0:
            print("Database already has product seed data. Verifying users/admin...")
        
        print("Starting database seeding...")
        
        # UC003: Ensure all test users have verified emails for testing
        try:
            db.execute(text("""
                UPDATE users SET
                    email_verified = true,
                    failed_login_attempts = 0,
                    last_failed_login_at = NULL
                WHERE email IN ('rajesh@test.com', 'priya@test.com', 'arjun@test.com', 'admin@test.com')
            """))
            db.commit()
            print("[UC003] Verified emails and reset login cooldown for all test users")
        except Exception as e:
            db.rollback()
            print(f"[UC003] Could not update existing users: {e}")
        
        # Insert test users (only if they don't exist)
        users_count = db.execute(text("SELECT COUNT(*) as count FROM users")).fetchone()
        if users_count.count == 0:
            # Password: test1234 hashed with bcrypt
            # UC003: Set email_verified=true for test users so they can login
            db.execute(text("""
                INSERT INTO users (name, email, phone, password_hash, role, email_verified, is_banned, created_at, updated_at) VALUES
                ('Rajesh Kumar', 'rajesh@test.com', '9876543210', '$2b$12$.HpI93vKuOnLeZTmXII6dO61IR3eFTmPrU.wPPEzU9TPBRVWOgcaC', 'user', true, false, NOW(), NOW()),
                ('Priya Singh', 'priya@test.com', '9876543211', '$2b$12$.HpI93vKuOnLeZTmXII6dO61IR3eFTmPrU.wPPEzU9TPBRVWOgcaC', 'user', true, false, NOW(), NOW()),
                ('Arjun Patel', 'arjun@test.com', '9876543212', '$2b$12$.HpI93vKuOnLeZTmXII6dO61IR3eFTmPrU.wPPEzU9TPBRVWOgcaC', 'user', true, false, NOW(), NOW())
            """))
            db.commit()
            print(" Created 3 test users (email verified)")
        else:
            print(" Users already exist, skipping user creation")

        # Ensure admin user exists for admin workflows/tests
        admin_user = db.query(User).filter(User.email == 'admin@test.com').first()
        if not admin_user:
            admin_user = User(
                name='Admin User',
                email='admin@test.com',
                phone='9000000000',
                password_hash=get_password_hash('test1234'),
                role=UserRole.ADMIN,
                email_verified=True,  # UC003: Admin can login immediately
                is_banned=False,
            )
            db.add(admin_user)
            db.commit()
            print(" Created admin test user (admin@test.com / test1234)")
        else:
            print(" Admin user already exists, skipping admin creation")
        
        # Insert test feeds (only if they don't exist)
        feeds_count = db.execute(text("SELECT COUNT(*) as count FROM feeds")).fetchone()
        if feeds_count.count == 0:
            db.execute(text("""
                INSERT INTO feeds (author_id, title, content, image_url, created_at) VALUES
                (1, 'Amazing Trail Experience', 'Just finished an amazing trail expedition in the Western Ghats! The terrain was challenging but rewarding.', 'https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=1200', NOW()),
                (1, 'New Suspension Upgrade', 'New suspension upgrade installed! Feel the difference in every bump. Much smoother ride now.', 'https://images.unsplash.com/photo-1493238792000-8113da705763?w=1200', NOW()),
                (1, 'Maintenance Tips for Monsoon', 'Maintenance tips for monsoon season: Check your underbody for rust, ensure all seals are intact, and use synthetic oil. Stay prepared!', NULL, NOW())
            """))
            db.commit()
            print(" Created 3 test feeds")
        else:
            print(" Feeds already exist, skipping feed creation")
        
        # Insert test accessories (only if they don't exist)
        if accessories_count.count == 0:
            db.execute(text("""
                INSERT INTO accessories (name, description, category, price, stock, created_at) VALUES
                ('Front Bumper Guard', 'Heavy-duty front bumper protection', 'Bumpers', 15999, 45, NOW()),
                ('LED Headlight Kit', 'Powerful LED headlights', 'Lighting', 12999, 28, NOW()),
                ('Roof Rack - Aluminum', 'Heavy-duty roof cargo carrier', 'Racks', 16999, 22, NOW()),
                ('Winch - 12000 lbs', 'Heavy-duty electric winch', 'Recovery', 28999, 15, NOW())
            """))
            db.commit()
            print(" Created 4 test accessories")
        else:
            print(" Accessories already exist, skipping accessories creation")
        
        # Insert test merchandise (only if they don't exist)
        if merchandise_count.count == 0:
            db.execute(text("""
                INSERT INTO merchandise (name, description, price, stock, created_at) VALUES
                ('Thar Club Classic Tee', 'Premium cotton t-shirt with club logo', 599, 156, NOW()),
                ('Thar Adventure Hoodie', 'Comfortable hoodie for club members', 1299, 89, NOW()),
                ('Thar Club Cap', 'Adjustable baseball cap', 349, 234, NOW()),
                ('Off-Road Gloves', 'Professional off-road driving gloves', 799, 145, NOW())
            """))
            db.commit()
            print(" Created 4 test merchandise items")
        else:
            print(" Merchandise already exist, skipping merchandise creation")
        
        # UC004: Insert test vehicles for each user
        vehicles_count = db.execute(text("SELECT COUNT(*) as count FROM vehicles")).fetchone()
        if vehicles_count.count == 0:
            try:
                # Get existing user IDs
                users = db.execute(text("SELECT id FROM users ORDER BY id LIMIT 3")).fetchall()
                if len(users) >= 3:
                    user_ids = [u[0] for u in users]
                    db.execute(text(f"""
                        INSERT INTO vehicles (user_id, make, model, year, registration_number, color, mileage, is_primary, created_at) VALUES
                        ({user_ids[0]}, 'Mahindra', 'Thar', '2023', 'KA-03-NM-4040', 'Red', 15000, true, NOW()),
                        ({user_ids[1]}, 'Mahindra', 'Thar', '2022', 'MH-02-AB-5050', 'Blue', 20000, true, NOW()),
                        ({user_ids[2]}, 'Mahindra', 'Bolero', '2021', 'DL-01-CD-6060', 'White', 25000, true, NOW())
                    """))
                    db.commit()
                    print(" Created 3 test vehicles for members")
            except Exception as e:
                db.rollback()
                print(f" Error seeding vehicles: {e}")
        else:
            print(" Vehicles already exist, skipping vehicles creation")
        
        # UC004: Insert test messages between users
        try:
            messages_count = db.execute(text("SELECT COUNT(*) as count FROM messages")).fetchone()
            if messages_count.count == 0:
                # Get first 3 user IDs for creating test messages
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
                    print(" Created 4 test messages")
                else:
                    print(" Insufficient users for message seeding")
            else:
                print(" Messages already exist, skipping messages creation")
        except Exception as e:
            db.rollback()
            print(f" Error seeding messages: {e}")
        
        # UC004B: Insert test events
        try:
            events_count = db.execute(text("SELECT COUNT(*) as count FROM events")).fetchone()
            if events_count.count == 0:
                # Get any user ID to create events (in production, would be admin only)
                first_user = db.execute(text("SELECT id FROM users ORDER BY id LIMIT 1")).fetchone()
                if first_user:
                    creator_id = first_user[0]
                    db.execute(text(f"""
                        INSERT INTO events (
                            name, description, event_date, location, 
                            difficulty_level, required_vehicle_type, max_participants, current_participants,
                            registration_deadline, event_fee, per_person_charge, 
                            safety_requirements, image_url, created_by, status, created_at
                        ) VALUES
                        (
                            'Weekend Trail to Nandi Hills',
                            'Join us for an exciting morning trail to Nandi Hills. Experience breathtaking sunrise views and challenging off-road terrain. Perfect for beginners and experienced riders alike.',
                            NOW() + INTERVAL '15 days',
                            'Nandi Hills, Karnataka',
                            'EASY',
                            '4x4 SUV',
                            20,
                            0,
                            NOW() + INTERVAL '10 days',
                            1500.00,
                            500.00,
                            'Basic safety gear, First aid kit, Valid driving license',
                            'https://example.com/nandi-hills.jpg',
                            {creator_id},
                            'PUBLISHED',
                            NOW()
                        ),
                        (
                            'Coorg Adventure Expedition',
                            'Multi-day expedition through the coffee plantations and mountains of Coorg. Includes camping, bonfire, and authentic Coorgi cuisine. Limited slots available!',
                            NOW() + INTERVAL '30 days',
                            'Coorg, Karnataka',
                            'MODERATE',
                            '4x4 SUV with high ground clearance',
                            15,
                            0,
                            NOW() + INTERVAL '20 days',
                            3500.00,
                            1500.00,
                            'Emergency medical kit, Camping gear, Recovery equipment, CB Radio',
                            'https://example.com/coorg-expedition.jpg',
                            {creator_id},
                            'PUBLISHED',
                            NOW()
                        ),
                        (
                            'Dandeli River Crossing Challenge',
                            'Extreme off-road challenge with river crossings, rocky terrain, and steep climbs. Recommended for experienced drivers only. Professional marshals will be present.',
                            NOW() + INTERVAL '45 days',
                            'Dandeli, Karnataka',
                            'DIFFICULT',
                            'Modified 4x4 with snorkel and winch',
                            10,
                            0,
                            NOW() + INTERVAL '35 days',
                            5000.00,
                            2000.00,
                            'Advanced recovery gear, Winch, Snorkel, CB Radio, Emergency contact, Medical insurance',
                            'https://example.com/dandeli-challenge.jpg',
                            {creator_id},
                            'PUBLISHED',
                            NOW()
                        ),
                        (
                            'Night Drive Experience - Kolar',
                            'Experience the thrill of night driving through forest trails near Kolar. Navigate with headlights and spotlights through challenging terrain.',
                            NOW() + INTERVAL '7 days',
                            'Kolar Gold Fields, Karnataka',
                            'MODERATE',
                            '4x4 SUV',
                            12,
                            0,
                            NOW() + INTERVAL '5 days',
                            2000.00,
                            800.00,
                            'Working spotlights, GPS device, Emergency beacon, First aid',
                            'https://example.com/night-drive.jpg',
                            {creator_id},
                            'PUBLISHED',
                            NOW()
                        ),
                        (
                            'Future Expedition - TBD',
                            'Planning stage expedition. Details will be announced soon. Register your interest!',
                            NOW() + INTERVAL '60 days',
                            'To be decided',
                            'MODERATE',
                            '4x4 SUV',
                            25,
                            0,
                            NOW() + INTERVAL '50 days',
                            0.00,
                            0.00,
                            'TBD',
                            'https://example.com/placeholder.jpg',
                            {creator_id},
                            'DRAFT',
                            NOW()
                        )
                    """))
                    db.commit()
                    print(" Created 5 test events (4 published, 1 draft)")
                else:
                    print(" No users found, skipping events creation")
            else:
                print(" Events already exist, skipping events creation")
        except Exception as e:
            db.rollback()
            print(f" Error seeding events: {e}")
        
        print("\n Database seeding completed successfully!")
        print("\nTest credentials for login:")
        print("  Email: rajesh@test.com")
        print("  Password: test1234")
        print("  Admin Email: admin@test.com")
        print("  Admin Password: test1234")
        
    except Exception as e:
        print(f" Error during seeding: {str(e)}")
        db.rollback()
    finally:
        db.close()
