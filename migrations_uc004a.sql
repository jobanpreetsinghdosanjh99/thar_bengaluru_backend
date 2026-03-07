-- UC004A: Add Edit Profile fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS emergency_contact VARCHAR(15);
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_photo VARCHAR(500);
