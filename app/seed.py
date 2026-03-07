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
