-- UC004B: Event Registration & Payment Tables
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    event_date TIMESTAMP NOT NULL,
    location VARCHAR(500) NOT NULL,
    difficulty_level VARCHAR(20) DEFAULT ''moderate'',
    required_vehicle_type VARCHAR(100),
    max_participants INTEGER NOT NULL,
    current_participants INTEGER DEFAULT 0,
    registration_deadline TIMESTAMP NOT NULL,
    event_fee FLOAT NOT NULL,
    per_person_charge FLOAT DEFAULT 0.0,
    safety_requirements TEXT,
    status VARCHAR(20) DEFAULT ''draft'',
    image_url VARCHAR(500),
    whatsapp_group_template VARCHAR(500),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS event_registrations (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    registration_status VARCHAR(20) DEFAULT ''pending'',
    num_copassengers INTEGER DEFAULT 0,
    total_amount FLOAT NOT NULL,
    payment_id INTEGER,
    whatsapp_link VARCHAR(500),
    confirmation_sent BOOLEAN DEFAULT FALSE,
    registered_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS copassengers (
    id SERIAL PRIMARY KEY,
    registration_id INTEGER REFERENCES event_registrations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_id INTEGER REFERENCES events(id),
    amount FLOAT NOT NULL,
    currency VARCHAR(3) DEFAULT ''INR'',
    payment_gateway VARCHAR(50) NOT NULL,
    gateway_payment_id VARCHAR(255),
    gateway_order_id VARCHAR(255),
    payment_status VARCHAR(20) DEFAULT ''pending'',
    payment_method VARCHAR(50),
    failure_reason TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add foreign key constraint for payment_id in event_registrations
ALTER TABLE event_registrations 
ADD CONSTRAINT fk_payment 
FOREIGN KEY (payment_id) REFERENCES payments(id);

-- Indexes for performance
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_registrations_event ON event_registrations(event_id);
CREATE INDEX idx_registrations_user ON event_registrations(user_id);
CREATE INDEX idx_payments_status ON payments(payment_status);
