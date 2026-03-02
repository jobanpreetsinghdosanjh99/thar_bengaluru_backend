"""
Seed script to populate initial test data
Runs on application startup if data doesn't exist
"""

from sqlalchemy import text
from app.database import SessionLocal


def seed_data():
    """Populate database with test data using SQL"""
    db = SessionLocal()
    
    try:
        # Check if accessories/merchandise exist
        accessories_count = db.execute(text("SELECT COUNT(*) as count FROM accessories")).fetchone()
        merchandise_count = db.execute(text("SELECT COUNT(*) as count FROM merchandise")).fetchone()
        
        if accessories_count.count > 0 and merchandise_count.count > 0:
            print("Database already seeded with complete data. Skipping...")
            return
        
        print("Starting database seeding...")
        
        # Insert test users (only if they don't exist)
        users_count = db.execute(text("SELECT COUNT(*) as count FROM users")).fetchone()
        if users_count.count == 0:
            # Password: test1234 hashed with bcrypt
            db.execute(text("""
                INSERT INTO users (name, email, phone, password_hash, role, created_at, updated_at) VALUES
                ('Rajesh Kumar', 'rajesh@test.com', '9876543210', '$2b$12$.HpI93vKuOnLeZTmXII6dO61IR3eFTmPrU.wPPEzU9TPBRVWOgcaC', 'user', NOW(), NOW()),
                ('Priya Singh', 'priya@test.com', '9876543211', '$2b$12$.HpI93vKuOnLeZTmXII6dO61IR3eFTmPrU.wPPEzU9TPBRVWOgcaC', 'user', NOW(), NOW()),
                ('Arjun Patel', 'arjun@test.com', '9876543212', '$2b$12$.HpI93vKuOnLeZTmXII6dO61IR3eFTmPrU.wPPEzU9TPBRVWOgcaC', 'user', NOW(), NOW())
            """))
            db.commit()
            print(" Created 3 test users")
        else:
            print(" Users already exist, skipping user creation")
        
        # Insert test feeds (only if they don't exist)
        feeds_count = db.execute(text("SELECT COUNT(*) as count FROM feeds")).fetchone()
        if feeds_count.count == 0:
            db.execute(text("""
                INSERT INTO feeds (author_id, title, content, image_url, created_at) VALUES
                (1, 'Amazing Trail Experience', 'Just finished an amazing trail expedition in the Western Ghats! The terrain was challenging but rewarding.', 'https://via.placeholder.com/400x300?text=Trail+Adventure', NOW()),
                (1, 'New Suspension Upgrade', 'New suspension upgrade installed! Feel the difference in every bump. Much smoother ride now.', 'https://via.placeholder.com/400x300?text=Suspension', NOW()),
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
        
        print("\n Database seeding completed successfully!")
        print("\nTest credentials for login:")
        print("  Email: rajesh@test.com")
        print("  Password: test1234")
        
    except Exception as e:
        print(f" Error during seeding: {str(e)}")
        db.rollback()
    finally:
        db.close()
