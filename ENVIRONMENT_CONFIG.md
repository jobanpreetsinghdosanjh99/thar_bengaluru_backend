# Environment Configuration - Backend

## Quick Start

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit with your credentials**:
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## Environment Variables Reference

### Required Variables

#### Database
```env
DATABASE_URL=postgresql://username:password@host:port/database_name
```

#### JWT Authentication
```env
SECRET_KEY=your-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Server
```env
ENVIRONMENT=development  # development | staging | production
HOST=0.0.0.0
PORT=8000
DEBUG=True  # Set to False in production
```

#### CORS (Security)
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```
⚠️ **Never use `*` in production!**

### Payment Gateways (Required for UC004B)

#### Razorpay
```env
RAZORPAY_KEY_ID=rzp_test_xxxxx  # Use rzp_live_xxxxx for production
RAZORPAY_KEY_SECRET=your_secret_key
```
Get credentials: https://dashboard.razorpay.com/app/keys

#### PhonePe
```env
PHONEPE_MERCHANT_ID=YOUR_MERCHANT_ID
PHONEPE_SALT_KEY=your_salt_key
PHONEPE_SALT_INDEX=1
```
Get credentials: https://business.phonepe.com/

### Email Service (Required for UC003)

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=noreply@tharbengaluru.com
SMTP_FROM_NAME=THAR Bengaluru
```

**Gmail Setup**:
1. Enable 2-Factor Authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the app password in `SMTP_PASSWORD`

**Production Alternatives**:
- SendGrid: https://sendgrid.com/
- AWS SES: https://aws.amazon.com/ses/
- Mailgun: https://www.mailgun.com/

### WhatsApp Business API (Required for UC004B)

```env
WHATSAPP_API_URL=https://graph.facebook.com/v17.0
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
```

**Setup Guide**:
1. Register: https://business.whatsapp.com/
2. Follow: https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
3. Get credentials from Meta Business Suite

### SMS Gateway (Optional)

```env
SMS_GATEWAY_URL=https://api.twilio.com/2010-04-01
SMS_ACCOUNT_SID=your_account_sid
SMS_AUTH_TOKEN=your_auth_token
SMS_FROM_NUMBER=+1234567890
```

**Twilio Setup**: https://www.twilio.com/try-twilio

---

## Environment-Specific Configurations

### Development (.env)
```env
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=postgresql://thar_user:thar_password_123@localhost:5432/thar_bengaluru_db
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:*
RAZORPAY_KEY_ID=rzp_test_mock_key_id
RAZORPAY_KEY_SECRET=mock_key_secret_for_development
```

### Staging (.env.staging)
```env
ENVIRONMENT=staging
DEBUG=False
DATABASE_URL=postgresql://user:pass@staging-db.example.com:5432/thar_staging
CORS_ORIGINS=https://app-staging.tharbengaluru.com
RAZORPAY_KEY_ID=rzp_test_real_staging_key
RAZORPAY_KEY_SECRET=real_staging_secret
```

### Production (.env.production)
```env
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=postgresql://user:strongpass@prod-db.example.com:5432/thar_prod
CORS_ORIGINS=https://app.tharbengaluru.com,https://www.tharbengaluru.com
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=live_secret_key_here
# ... all other production credentials ...
```

---

## Running Different Environments

### Development
```bash
# Default uses .env
python main.py
```

### Staging
```bash
# Load staging environment
cp .env.staging .env
python main.py

# Or export environment variables
export $(cat .env.staging | xargs)
python main.py
```

### Production (Recommended)
```bash
# Using Uvicorn with workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn with Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With systemd service
sudo systemctl start thar-backend
```

---

## Security Best Practices

### 🔒 Secret Key Generation
```bash
# Generate secure SECRET_KEY
openssl rand -hex 32
```

### 🔒 Database Security
- Use strong passwords (min 16 chars, mixed case, numbers, symbols)
- Enable SSL/TLS for database connections
- Restrict database access by IP whitelist
- Regular backups

### 🔒 CORS Configuration
```env
# ❌ NEVER in production
CORS_ORIGINS=*

# ✅ ALWAYS specific domains
CORS_ORIGINS=https://app.tharbengaluru.com,https://admin.tharbengaluru.com
```

### 🔒 Environment Separation
- **NEVER** share credentials between environments
- Use different databases for dev/staging/prod
- Use test payment gateway keys for dev/staging
- Use separate email accounts

### 🔒 Credential Management
Consider using secrets management services:
- AWS Secrets Manager
- Google Cloud Secret Manager
- HashiCorp Vault
- Azure Key Vault

---

## Troubleshooting

### Database Connection Issues
```bash
# Test database connection
psql -h localhost -U thar_user -d thar_bengaluru_db

# Check if PostgreSQL is running
sudo systemctl status postgresql
```

### CORS Errors
1. Check `CORS_ORIGINS` includes your frontend URL
2. Ensure no trailing slashes in URLs
3. Verify protocol (http vs https)
4. Check browser console for exact error

### Payment Gateway Errors
1. Verify you're using correct keys (test vs live)
2. Check if IP is whitelisted in gateway dashboard
3. Verify webhook URLs are configured
4. Check gateway dashboard for error logs

### Email Service Not Working
1. Verify SMTP credentials
2. Check if less secure app access is enabled (Gmail)
3. Verify firewall allows outbound port 587/465
4. Test with `telnet smtp.gmail.com 587`

---

## Accessing Configuration in Code

```python
from app.config import settings

# Use settings anywhere in your code
print(f"Environment: {settings.environment}")
print(f"Database: {settings.database_url}")
print(f"Debug mode: {settings.debug}")

# Environment checks
if settings.is_production():
    # Production-only code
    pass

if settings.is_development():
    # Development-only code
    pass
```

---

## Testing Configuration

```python
# test_config.py
from app.config import settings

def test_configuration():
    """Verify all required configurations are set."""
    assert settings.database_url, "DATABASE_URL not set"
    assert settings.secret_key != "your-secret-key-change-in-production", "Change SECRET_KEY!"
    assert len(settings.secret_key) >= 32, "SECRET_KEY too short"
    
    if settings.is_production():
        assert settings.debug is False, "DEBUG must be False in production"
        assert "*" not in settings.cors_origins, "CORS must not use * in production"
        assert settings.razorpay_key_id.startswith("rzp_live_"), "Use live Razorpay keys in production"

if __name__ == "__main__":
    test_configuration()
    print("✅ Configuration is valid!")
```

Run test:
```bash
python test_config.py
```

---

## Deployment Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Generate new `SECRET_KEY` with `openssl rand -hex 32`
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=False`
- [ ] Configure production database URL with SSL
- [ ] Set specific `CORS_ORIGINS` (no wildcards)
- [ ] Use live payment gateway credentials
- [ ] Configure production email service
- [ ] Set up WhatsApp Business API
- [ ] Test all API endpoints
- [ ] Set up SSL/TLS certificate
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up logging and monitoring
- [ ] Configure automated backups
- [ ] Set up health check endpoints
- [ ] Document deployment process

---

## Additional Resources

- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- PostgreSQL Security: https://www.postgresql.org/docs/current/security.html
- Uvicorn Deployment: https://www.uvicorn.org/deployment/
- Gunicorn Documentation: https://docs.gunicorn.org/

---

**Last Updated**: March 7, 2026
