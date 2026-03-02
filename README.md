# THAR Bengaluru Backend API

A Python FastAPI backend for the THAR 4x4 Club Management Flutter App.

## Features

- **User Authentication**: JWT-based login/registration
- **Community Feeds**: Create, view, and comment on community posts
- **Accessories Store**: Browse and manage 4x4 accessories
- **Merchandise**: Club merchandise with size/color variants
- **Membership Management**: Club membership requests and approvals
- **TBLR Membership**: New member applications and tracking
- **Shopping Cart**: Add items to cart for checkout

## Tech Stack

- **Framework**: FastAPI (Python web framework)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens
- **Password Hashing**: bcrypt
- **Deployment**: Render, Railway, or Heroku

## Quick Start

### 1. Setup Environment

```bash
# Clone or create the project
cd thar_bengaluru_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Database

Copy `.env.example` to `.env` and update with your settings:

```bash
cp .env.example .env
```

Edit `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/thar_bengaluru_db
SECRET_KEY=your-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Setup PostgreSQL

```bash
# Windows (using PostgreSQL installer)
createdb -U postgres thar_bengaluru_db

# Mac (using homebrew)
createdb thar_bengaluru_db

# Linux
sudo -u postgres createdb thar_bengaluru_db
```

### 4. Run the Server

```bash
python main.py
```

Server will start at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Community Feeds
- `GET /feeds` - List all feeds
- `GET /feeds/{feed_id}` - Get feed details
- `POST /feeds` - Create new feed
- `POST /feeds/{feed_id}/comments` - Add comment
- `GET /feeds/{feed_id}/comments` - Get comments

### Accessories
- `GET /accessories` - List accessories
- `GET /accessories/{accessory_id}` - Get accessory details
- `POST /accessories` - Create accessory (admin)

### Merchandise
- `GET /merchandise` - List merchandise
- `GET /merchandise/{merch_id}` - Get merchandise details
- `POST /merchandise` - Create merchandise (admin)

### Membership
- `POST /membership-requests` - Submit membership request
- `GET /membership-requests` - List all requests (admin)
- `GET /membership-requests/{request_id}` - Get request details
- `PATCH /membership-requests/{request_id}/approve` - Approve (admin)
- `PATCH /membership-requests/{request_id}/reject` - Reject (admin)

### TBLR Membership
- `POST /tblr-membership` - Submit TBLR application
- `GET /tblr-membership` - List applications (admin)
- `GET /tblr-membership/{app_id}` - Get application details
- `PATCH /tblr-membership/{app_id}/approve` - Approve (admin)
- `PATCH /tblr-membership/{app_id}/reject` - Reject (admin)

### Shopping Cart
- `GET /cart` - Get user's cart
- `POST /cart` - Add item to cart
- `DELETE /cart/{item_id}` - Remove item from cart
- `DELETE /cart` - Clear entire cart

## Deployment

### Option 1: Render (Recommended for free tier)

1. Push code to GitHub
2. Connect Render to your GitHub repo
3. Create PostgreSQL database on Render
4. Deploy with auto-deploys enabled
5. Free tier: ~0.5 GB RAM, shared CPU

**Cost**: Free tier (with 15-day inactivity shutdown), $7+/month for production

### Option 2: Railway

1. Sign up at railway.app
2. Connect GitHub repo
3. Add PostgreSQL plugin
4. Deploy

**Cost**: Pay-as-you-go (~$5/month for moderate usage)

### Option 3: Fly.io

```bash
# Install Fly CLI
# Deploy using flyctl
flyctl deploy
```

**Cost**: Free tier with limits, $5+/month for production

## Environment Variables

Create `.env` file in root:

```
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Database Schema

### Users
- id, name, email, phone, password_hash, role, created_at, updated_at

### Feeds
- id, author_id, title, content, image_url, likes_count, created_at, updated_at

### Feed Comments
- id, feed_id, author_id, content, created_at

### Accessories
- id, name, description, category, price, image_url, stock, created_at, updated_at

### Merchandise
- id, name, description, price, image_url, sizes, colors, stock, created_at, updated_at

### Club Membership Requests
- id, user_id, name, email, phone, vehicle_model, vehicle_number, registration_date, reason, status, created_at, updated_at

### TBLR Membership
- id, user_id, full_name, email, phone, vehicle_model, vehicle_number, experience_level, motivation, status, created_at, updated_at

### Cart Items
- id, user_id, product_type, product_id, quantity, size, color, created_at

## Testing

Use FastAPI's built-in Swagger UI:

1. Go to `http://localhost:8000/docs`
2. Try out API endpoints directly
3. Click "Authorize" to add JWT token

## Common Issues

### "Database connection refused"
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database exists

### "Module not found"
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

### "Port 8000 already in use"
```bash
# Run on different port
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Future Enhancements

- Payment integration (Stripe/PayPal)
- Email notifications
- Image upload to cloud storage
- WebSocket for real-time updates
- Admin dashboard
- Event management
- Ride tracking/GPS

## License

MIT

## Support

For issues or questions, contact the development team.
