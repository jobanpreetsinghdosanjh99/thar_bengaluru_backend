# Production Server Deployment Runbook

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Database Setup](#database-setup)
4. [Application Deployment](#application-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Running Migrations](#running-migrations)
7. [Process Management](#process-management)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup Strategy](#backup-strategy)
10. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Software Requirements
- **OS**: Ubuntu 22.04 LTS or newer (recommended)
- **Python**: 3.9 or higher
- **PostgreSQL**: 14 or higher
- **Nginx**: Latest stable version
- **Git**: For deployment

### Server Specifications (Minimum)
- **CPU**: 2 vCPU
- **RAM**: 4GB
- **Storage**: 40GB SSD
- **Network**: 1Gbps connection

---

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx git supervisor certbot python3-certbot-nginx

# Create application user (do not use root)
sudo adduser --disabled-password --gecos "" tharapp
sudo usermod -aG sudo tharapp

# Switch to application user
sudo su - tharapp
```

### 2. Setup Application Directory

```bash
# Create application directory
mkdir -p /home/tharapp/thar_bengaluru_backend
cd /home/tharapp/thar_bengaluru_backend

# Clone repository
git clone https://github.com/jobanpreetsinghdosanjh99/thar_bengaluru_backend.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Database Setup

### 1. Create PostgreSQL Database

```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
psql
```

```sql
-- Create production database
CREATE DATABASE thar_bengaluru_prod;

-- Create production user with strong password
CREATE USER thar_prod_user WITH ENCRYPTED PASSWORD 'YOUR_STRONG_PASSWORD_HERE';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE thar_bengaluru_prod TO thar_prod_user;

-- Grant schema privileges
\c thar_bengaluru_prod
GRANT ALL ON SCHEMA public TO thar_prod_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO thar_prod_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO thar_prod_user;

-- Exit psql
\q
```

```bash
# Exit postgres user
exit
```

### 2. Configure PostgreSQL for Remote Access (if needed)

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Change listen_addresses
# listen_addresses = 'localhost'  # Change to '0.0.0.0' for all interfaces or specific IP

# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add connection rules (be specific with IP ranges)
# host    thar_bengaluru_prod    thar_prod_user    10.0.0.0/8    scram-sha-256

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## Environment Configuration

### 1. Create Production .env File

```bash
cd /home/tharapp/thar_bengaluru_backend
nano .env
```

Add the following configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://thar_prod_user:YOUR_STRONG_PASSWORD_HERE@localhost:5432/thar_bengaluru_prod

# JWT Configuration (Generate new secret: openssl rand -hex 32)
SECRET_KEY=YOUR_PRODUCTION_SECRET_KEY_HERE_MINIMUM_32_CHARS
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
DEBUG=False

# CORS Configuration (Use your actual domain)
CORS_ORIGINS=https://app.tharbengaluru.com,https://www.tharbengaluru.com

# Payment Gateway - Razorpay (Use LIVE keys for production)
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=YOUR_RAZORPAY_SECRET_HERE

# Email Service (Use production SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@tharbengaluru.com
SMTP_PASSWORD=YOUR_APP_SPECIFIC_PASSWORD
SMTP_FROM_EMAIL=noreply@tharbengaluru.com
SMTP_FROM_NAME=THAR Bengaluru

# WhatsApp Business API
WHATSAPP_API_URL=https://graph.facebook.com/v17.0
WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN=YOUR_WHATSAPP_TOKEN

# Logging
LOG_LEVEL=INFO
```

### 2. Secure the .env File

```bash
chmod 600 .env
chown tharapp:tharapp .env
```

---

## Running Migrations

### 1. Run Production Database Setup

**IMPORTANT: This does NOT add test data**

```bash
cd /home/tharapp/thar_bengaluru_backend
source venv/bin/activate

# Option 1: Run as Python module
python -c "from app.setup_production import setup_production_database; setup_production_database()"

# Option 2: Run as script
python app/setup_production.py
```

Expected output:
```
======================================================================
PRODUCTION DATABASE SETUP
======================================================================
...
[STEP 1] Setting up table schemas...
✓ [users] UC003 authentication columns added
✓ [accessories] UC004D vendor columns added
✓ [merchandise] UC004E vendor columns added
✓ [club_membership_requests] UC005 lifecycle columns and indexes added
✓ [thar_bengaluru_memberships] UC006 indexes verified
...
✓ PRODUCTION DATABASE SETUP COMPLETE
======================================================================
```

### 2. Create Initial Admin User

**Method 1: Via API (Recommended)**

```bash
# Start the application temporarily
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, create admin user via API
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin User",
    "email": "admin@tharbengaluru.com",
    "phone": "9999999999",
    "password": "StrongAdminPassword123!"
  }'
```

**Method 2: Direct Database Insert**

```bash
sudo su - postgres
psql thar_bengaluru_prod
```

```sql
-- Insert admin user (password: AdminPass123! hashed)
INSERT INTO users (
    name, email, phone, password_hash, role, 
    email_verified, is_banned, created_at, updated_at
) VALUES (
    'Admin User',
    'admin@tharbengaluru.com',
    '9999999999',
    '$2b$12$YOUR_BCRYPT_HASH_HERE',  -- Generate with Python: from app.security import get_password_hash; print(get_password_hash('YourPassword'))
    'admin',
    true,
    false,
    NOW(),
    NOW()
);
```

---

## Application Deployment

### 1. Test Application Locally

```bash
cd /home/tharapp/thar_bengaluru_backend
source venv/bin/activate

# Test run
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Verify health endpoint
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### 2. Setup Supervisor for Process Management

```bash
sudo nano /etc/supervisor/conf.d/thar_backend.conf
```

Add configuration:

```ini
[program:thar_backend]
command=/home/tharapp/thar_bengaluru_backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/home/tharapp/thar_bengaluru_backend
user=tharapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/thar_backend/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/tharapp/thar_bengaluru_backend/venv/bin"
```

Create log directory:

```bash
sudo mkdir -p /var/log/thar_backend
sudo chown tharapp:tharapp /var/log/thar_backend
```

Start the service:

```bash
# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start the application
sudo supervisorctl start thar_backend

# Check status
sudo supervisorctl status thar_backend
```

### 3. Setup Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/thar_backend
```

Add configuration:

```nginx
upstream thar_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.tharbengaluru.com;  # Change to your domain

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Client max body size (for file uploads)
    client_max_body_size 10M;

    location / {
        proxy_pass http://thar_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (don't log)
    location /health {
        proxy_pass http://thar_backend;
        access_log off;
    }
}
```

Enable the site:

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/thar_backend /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 4. Setup SSL with Let's Encrypt

```bash
# Generate SSL certificate
sudo certbot --nginx -d api.tharbengaluru.com

# Auto-renewal is configured by default
# Test renewal
sudo certbot renew --dry-run
```

---

## Process Management

### Common Supervisor Commands

```bash
# Check status
sudo supervisorctl status thar_backend

# Start application
sudo supervisorctl start thar_backend

# Stop application
sudo supervisorctl stop thar_backend

# Restart application
sudo supervisorctl restart thar_backend

# View logs (last 100 lines)
sudo tail -n 100 /var/log/thar_backend/app.log

# Follow logs in real-time
sudo tail -f /var/log/thar_backend/app.log
```

---

## Monitoring & Logging

### 1. Application Logs

```bash
# View application logs
sudo tail -f /var/log/thar_backend/app.log

# Search for errors
sudo grep -i "error" /var/log/thar_backend/app.log

# Search by date
sudo grep "2026-03-08" /var/log/thar_backend/app.log
```

### 2. Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### 3. PostgreSQL Logs

```bash
# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### 4. System Monitoring

```bash
# Check CPU/Memory usage
htop

# Check disk space
df -h

# Check network connections
sudo netstat -tulpn | grep :8000

# Check process
ps aux | grep uvicorn
```

---

## Backup Strategy

### 1. Database Backup Script

Create backup script:

```bash
sudo nano /home/tharapp/backup_database.sh
```

```bash
#!/bin/bash

# Configuration
DB_NAME="thar_bengaluru_prod"
DB_USER="thar_prod_user"
BACKUP_DIR="/home/tharapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/thar_backup_$DATE.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup (compressed)
PGPASSWORD="YOUR_PASSWORD" pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "thar_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

Make executable:

```bash
chmod +x /home/tharapp/backup_database.sh
```

### 2. Setup Automated Backups (Cron)

```bash
crontab -e
```

Add daily backup at 2 AM:

```cron
0 2 * * * /home/tharapp/backup_database.sh >> /var/log/thar_backup.log 2>&1
```

### 3. Restore from Backup

```bash
# Decompress and restore
gunzip < /home/tharapp/backups/thar_backup_YYYYMMDD_HHMMSS.sql.gz | \
  PGPASSWORD="YOUR_PASSWORD" psql -U thar_prod_user -h localhost thar_bengaluru_prod
```

---

## Rollback Procedures

### 1. Application Rollback

```bash
cd /home/tharapp/thar_bengaluru_backend

# List recent commits
git log --oneline -n 10

# Rollback to specific commit
git checkout <commit-hash>

# Restart application
sudo supervisorctl restart thar_backend
```

### 2. Database Rollback

```bash
# Stop application first
sudo supervisorctl stop thar_backend

# Restore from backup
gunzip < /home/tharapp/backups/thar_backup_BEFORE_MIGRATION.sql.gz | \
  PGPASSWORD="YOUR_PASSWORD" psql -U thar_prod_user -h localhost thar_bengaluru_prod

# Restart application
sudo supervisorctl start thar_backend
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Server meets minimum specifications
- [ ] PostgreSQL installed and configured
- [ ] Application user created (non-root)
- [ ] .env file configured with production values
- [ ] SSL certificate obtained
- [ ] Firewall configured (ports 80, 443 open)

### Deployment
- [ ] Code deployed from Git repository
- [ ] Virtual environment created and activated
- [ ] Dependencies installed from requirements.txt
- [ ] Database created with correct user permissions
- [ ] `setup_production.py` executed successfully
- [ ] Admin user created
- [ ] Supervisor configured and running
- [ ] Nginx configured and SSL enabled
- [ ] Health check endpoint responding

### Post-Deployment
- [ ] Application logs show no errors
- [ ] Test user registration and login
- [ ] Test admin endpoints
- [ ] Verify database connections
- [ ] Setup automated backups
- [ ] Configure monitoring/alerts
- [ ] Document admin credentials securely

### Testing in Production
```bash
# Health check
curl https://api.tharbengaluru.com/health

# Test registration
curl -X POST https://api.tharbengaluru.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","phone":"9999999999","password":"Test123!"}'

# Test login
curl -X POST https://api.tharbengaluru.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

---

## Troubleshooting

### Application won't start

```bash
# Check supervisor logs
sudo tail -n 100 /var/log/supervisor/supervisord.log

# Check application logs
sudo tail -n 100 /var/log/thar_backend/app.log

# Check if port is in use
sudo netstat -tulpn | grep :8000

# Check database connectivity
PGPASSWORD="YOUR_PASSWORD" psql -U thar_prod_user -h localhost thar_bengaluru_prod -c "SELECT 1"
```

### SSL certificate issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

### Database connection errors

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -n 100 /var/log/postgresql/postgresql-14-main.log

# Verify user permissions
sudo su - postgres
psql thar_bengaluru_prod
\du  # List users and roles
```

---

## Security Best Practices

1. **Never commit .env files** to Git
2. **Use strong passwords** (minimum 16 characters, mixed case, numbers, symbols)
3. **Rotate secrets regularly** (JWT secret, database passwords)
4. **Keep system packages updated**: `sudo apt update && sudo apt upgrade`
5. **Use firewall**: Configure UFW to allow only necessary ports
6. **Disable root SSH**: Edit `/etc/ssh/sshd_config` and set `PermitRootLogin no`
7. **Enable SSH key authentication** instead of passwords
8. **Monitor logs** for suspicious activity
9. **Backup regularly** and test restore procedures
10. **Use HTTPS everywhere** - never serve over HTTP in production

---

## Support Contacts

- **Technical Lead**: technical@tharbengaluru.com
- **DevOps**: devops@tharbengaluru.com
- **Emergency Hotline**: +91-XXXX-XXXXXX

---

**Document Version**: 1.0  
**Last Updated**: March 8, 2026  
**Next Review**: June 8, 2026
