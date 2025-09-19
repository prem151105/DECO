# DocSense AI Deployment Guide

## Overview
This application consists of:
- **Backend**: FastAPI (Python) with SQLite database
- **Frontend**: React.js with authentication

## Deployment Options

### Option 1: Vercel (Frontend) + Railway/Render (Backend) - Recommended

#### 1. Deploy Backend to Railway
1. Go to [Railway.app](https://railway.app) and create account
2. Create new project from GitHub repo
3. Set environment variables:
   - `GOOGLE_API_KEY` (for Gemini AI)
   - `SECRET_KEY` (random string)
   - `EMAIL_USER` and `EMAIL_PASS` (for notifications)
4. Railway will auto-detect Python and install dependencies
5. Get the backend URL (e.g., `https://your-app.railway.app`)

#### 2. Deploy Frontend to Vercel
1. Go to [Vercel.com](https://vercel.com) and create account
2. Import your GitHub repo
3. Set environment variable:
   - `REACT_APP_API_URL=https://your-backend-url.railway.app`
4. Deploy

### Option 2: Local Development
```bash
# Backend
cd /path/to/project
python setup.py  # Creates admin user
python api.py

# Frontend
cd frontend
npm install
npm start
```

## Environment Variables

### Backend (.env)
```
GOOGLE_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key_here
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_email_password
```

### Frontend
```
REACT_APP_API_URL=https://your-backend.railway.app
```

## Database
- SQLite is used for simplicity
- For production, consider PostgreSQL
- Data persists in Railway/Render deployments

## Features
- ✅ Admin login and document upload
- ✅ User management
- ✅ Document processing with AI
- ✅ Email notifications
- ✅ Search functionality
- ✅ Role-based access

## Security Notes
- JWT tokens expire in 30 minutes
- Passwords are hashed with bcrypt
- CORS configured for frontend domain
- Admin-only endpoints protected

## Troubleshooting
- If CORS errors: Check REACT_APP_API_URL
- If login fails: Check SECRET_KEY consistency
- If emails not sending: Verify EMAIL_USER/EMAIL_PASS