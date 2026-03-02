# Deployment to Render.com (Free Tier)

## Prerequisites
- GitHub account
- Render.com account
- PostgreSQL database (Render provides free tier)

## Step 1: Prepare Code for Deployment

### Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: thar-bengaluru-api
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: thar-bengaluru-db
          property: connectionString

  - type: pserv
    name: thar-bengaluru-db
    plan: free
    ipAllowList: []
    postgresMajorVersion: 15
```

### Create `.render-buildignore` (optional):

```
.git
__pycache__
*.pyc
.env
.env.local
venv/
```

## Step 2: Push to GitHub

```bash
git init
git add .
git commit -m "Initial FastAPI backend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/thar_bengaluru_backend.git
git push -u origin main
```

## Step 3: Deploy on Render

1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Select your GitHub repository
5. Click "Connect"
6. In the deployment settings:
   - **Name**: `thar-bengaluru-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`

7. Click "Create Web Service"

### Add PostgreSQL Database

1. In Render dashboard, click "New +" → "PostgreSQL"
2. Name: `thar-bengaluru-db`
3. Plan: `Free`
4. Create
5. Copy the **Internal Database URL** from the PostgreSQL service
6. Go back to your web service and add environment variable:
   - Key: `DATABASE_URL`
   - Value: Paste the database URL

## Step 4: Verify Deployment

After a few minutes, your API should be live:

- API URL: `https://thar-bengaluru-api.onrender.com`
- Docs: `https://thar-bengaluru-api.onrender.com/docs`
- Health: `https://thar-bengaluru-api.onrender.com/health`

## Backend URL for Flutter App

Update your Flutter app's API base URL:

```dart
const String baseUrl = "https://thar-bengaluru-api.onrender.com";
```

## Important Notes

### Free Tier Limitations
- Apps spin down after 15 minutes of inactivity
- First request after spindown takes ~30 seconds
- Limited to 750 compute hours/month
- PostgreSQL has 90-day inactivity auto-delete

### To Prevent Spindown
- Upgrade to paid plan ($7/month)
- Or keep traffic consistent with a pinging service

### Environment Variables

Render automatically creates `DATABASE_URL` from PostgreSQL service, but you still need to set:

```
SECRET_KEY=generate-a-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Redeploy

After pushing changes to GitHub:
```bash
git add .
git commit -m "Your changes"
git push origin main
```

Render will auto-redeploy if you enabled "Auto-Deploy on push".

## Check Logs

In Render dashboard:
1. Click your web service
2. Go to "Logs" tab
3. See real-time deployment and runtime logs

## Database Management

Render provides pgAdmin interface:
1. Go to your PostgreSQL database in Render
2. Click "External Database URL" and use any PostgreSQL client
3. Or use `psql` command line:

```bash
psql postgresql://user:password@host:5432/dbname
```

## Troubleshooting

### Build fails
- Check Python version compatibility
- Ensure `requirements.txt` is in root
- Verify all dependencies are listed

### Database connection error
- Verify DATABASE_URL is set
- Check PostgreSQL is initialized
- Restart the web service

### Slow first request
- This is normal on free tier (app spindown)
- Consider upgrade to prevent spindowns

## Next Steps

1. Test API endpoints from Flutter app
2. Monitor performance in Render dashboard
3. Set up error tracking (Sentry)
4. Plan upgrade path as usage grows
