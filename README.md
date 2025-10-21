# Community Management System - MyGate Style

A comprehensive community management application with visitor management, role-based access control, AI-powered chat interface, and real-time notifications.

## 🏗️ Architecture (90 seconds)

### Tech Stack

- **Backend**: FastAPI + Python
- **Database**: Supabase (PostgreSQL)
- **AI**: OpenAI GPT-4o-mini with function calling
- **Frontend**: React + Vite + TailwindCSS
- **Notifications**: Firebase Cloud Messaging (FCM)
- **Auth**: JWT-based authentication with Supabase

### Architecture Flow

```
Client (React) 
    ↓ [HTTP + JWT Token]
FastAPI Backend (Python)
    ↓ [SQL Queries]
Supabase (PostgreSQL + Auth)
    ↓ [Tool Calls]
OpenAI GPT-4o-mini
    ↓ [Push Notifications]
Firebase Cloud Messaging
```

### Key Components

1. **Authentication**: JWT tokens with role-based claims
2. **Visitor Management**: State machine (pending → approved → checked_in → checked_out)
3. **AI Copilot**: Natural language commands executed via OpenAI function calling
4. **Audit Log**: Immutable event log for all actions
5. **Notifications**: FCM push notifications for status changes

---

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- Supabase account
- OpenAI API key
- Firebase project (for FCM - optional for basic functionality)

---

## 🚀 Setup Instructions

### Step 1: Clone and Setup Project Structure

```bash
# Create project directory
mkdir community-app
cd community-app

# Create subdirectories
mkdir backend frontend postman
```

### Step 2: Supabase Setup

1. Go to [https://supabase.com](https://supabase.com) and create a new project
2. Go to **Settings** → **API** and note:
   - Project URL
   - `anon` public key
   - `service_role` secret key
3. Go to **SQL Editor** and run the database schema (provided in setup guide)
4. Enable **Email Auth** in Authentication settings

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

**Edit `.env` file:**

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here
SUPABASE_JWT_SECRET=your_jwt_secret_from_supabase

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Firebase (optional for basic testing)
FCM_PROJECT_ID=your-firebase-project-id
FCM_PRIVATE_KEY=your-firebase-private-key
FCM_CLIENT_EMAIL=your-firebase-client-email

# App Settings
SECRET_KEY=your-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Generate SECRET_KEY:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Seed Database

```bash
# Make sure you're in the backend directory with venv activated
python seed.py
```

This will create:

- 1 Resident user (<resident@example.com>)
- 1 Guard user (<guard@example.com>)
- 1 Admin user (<admin@example.com>)
- 1 Household (A-101)
- 2 Test visitors (1 pending, 1 approved)
- Sample audit events

### Step 5: Run Backend Server

```bash
# In backend directory with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

Check health endpoint: `http://localhost:8000/health`

### Step 6: Frontend Setup

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Create .env file (optional)
echo "VITE_API_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Step 7: Import Postman Collection

1. Open Postman
2. Click **Import**
3. Select `postman/Community_App.postman_collection.json`
4. Set collection variable `base_url` to `http://localhost:8000`
5. Test the health check endpoint first

---

## 🔐 RBAC Policy (Who Can Do What)

### Resident

- ✅ Create visitors for their household
- ✅ Approve/deny visitors for their household
- ✅ View visitors for their household
- ✅ Use AI copilot for visitor management
- ❌ Cannot check in/out visitors
- ❌ Cannot view other households' visitors

### Guard

- ✅ View all visitors
- ✅ Check in approved visitors
- ✅ Check out checked-in visitors
- ✅ Use AI copilot for check-in/out
- ❌ Cannot create visitors
- ❌ Cannot approve/deny visitors

### Admin/Committee

- ✅ Full access to all features
- ✅ View all visitors across households
- ✅ Approve/deny any visitor
- ✅ Check in/out visitors
- ✅ View complete audit log
- ✅ Manage all operations via AI copilot

---

## 🤖 AI Tools (OpenAI Function Calling)

### Available Tools

1. **approve_visitor**
   - Parameters: `visitor_name` (string)
   - Access: Residents (own household), Admins (all)
   - Validates: User permission, visitor status (must be pending)

2. **deny_visitor**
   - Parameters: `visitor_name` (string), `reason` (string, optional)
   - Access: Residents (own household), Admins (all)
   - Validates: User permission, visitor status (must be pending)

3. **checkin_visitor**
   - Parameters: `visitor_name` (string)
   - Access: Guards, Admins
   - Validates: User role, visitor status (must be approved)

4. **checkout_visitor**
   - Parameters: `visitor_name` (string)
   - Access: Guards, Admins
   - Validates: User role, visitor status (must be checked_in)

5. **list_visitors**
   - Parameters: `status` (string: "pending", "approved", "denied", "checked_in", "checked_out", "all")
   - Access: All authenticated users
   - Returns: Filtered list based on user role and household

### Example AI Commands

```
"approve Ramesh"
"deny John Doe because he's not authorized"
"check in Suresh Reddy"
"check out Mr Verma"
"show me all pending visitors"
"list approved visitors"
```

---

## 📊 Database Schema

### Tables

**users**

- id (UUID, PK)
- email (TEXT, UNIQUE)
- phone (TEXT)
- display_name (TEXT)
- household_id (UUID, FK)
- roles (TEXT[])
- created_at, updated_at (TIMESTAMPTZ)

**households**

- id (UUID, PK)
- flat_no (TEXT)
- name (TEXT)
- members (UUID[])
- created_at, updated_at (TIMESTAMPTZ)

**visitors**

- id (UUID, PK)
- name (TEXT)
- phone (TEXT)
- purpose (TEXT)
- host_household_id (UUID, FK)
- status (ENUM: pending, approved, denied, checked_in, checked_out)
- approved_by (UUID, FK)
- approved_at, checked_in_at, checked_out_at (TIMESTAMPTZ)
- scheduled_time (TIMESTAMPTZ)
- created_at, updated_at (TIMESTAMPTZ)

**events** (Audit Log - Immutable)

- id (UUID, PK)
- type (TEXT)
- actor_user_id (UUID, FK)
- subject_id (UUID)
- payload (JSONB)
- timestamp (TIMESTAMPTZ)

**device_tokens**

- id (UUID, PK)
- user_id (UUID, FK)
- token (TEXT, UNIQUE)
- created_at (TIMESTAMPTZ)

---

## 🧪 Testing Guide

### Using Postman

1. **Login as Resident**
   - Use "Login - Resident" request
   - Token automatically saved to collection variable

2. **Create a Visitor**
   - Use "Create Visitor" request
   - Visitor ID automatically saved

3. **Approve Visitor (as Resident)**
   - Use "Approve Visitor" request

4. **Login as Guard**
   - Use "Login - Guard" request

5. **Check In Visitor (as Guard)**
   - Use "Check In Visitor" request

6. **Check Out Visitor (as Guard)**
   - Use "Check Out Visitor" request

7. **Test AI Copilot**
   - Use "Chat - Approve Ramesh" request
   - Try custom messages

8. **View Audit Log**
   - Use "Audit Events" request

### Test Credentials

```
Resident:
  Email: resident@example.com
  Password: password123
  Household: A-101

Guard:
  Email: guard@example.com
  Password: password123

Admin:
  Email: admin@example.com
  Password: password123
```

### Manual Testing Flow

1. **Login to Frontend** (`http://localhost:3000`)
   - Use quick login buttons or enter credentials

2. **As Resident:**
   - Create a new visitor
   - View pending visitors
   - Use AI Copilot: "approve [visitor name]"

3. **Logout and Login as Guard:**
   - View all visitors
   - Check in approved visitors
   - Use AI Copilot: "check in [visitor name]"

4. **Check Audit Log:**
   - View all recorded events
   - Verify immutability (no edit/delete)

---

## 🔔 Notifications

### FCM Implementation

The system includes FCM notification hooks at key points:

- Visitor created → Notify guards
- Visitor approved → Notify guards
- Visitor denied → Notify guards
- Visitor checked in → Notify household members
- Visitor checked out → Notify household members

### Topics

- `guards` - All guard users
- `household_{id}` - Specific household members

**Note:** For local development, notifications are logged to console. To enable actual FCM:

1. Create Firebase project
2. Generate service account key
3. Add credentials to `.env`
4. Implement `send_notification()` in `app/utils/fcm.py`

---

## 📁 Project Structure

```
community-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Configuration management
│   │   ├── database.py          # Supabase client
│   │   ├── models.py            # Enums and data models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── auth.py              # JWT authentication
│   │   ├── dependencies.py      # Route dependencies
│   │   ├── routers/
│   │   │   ├── auth.py          # Auth endpoints
│   │   │   ├── visitors.py      # Visitor management
│   │   │   ├── chat.py          # AI copilot
│   │   │   └── notifications.py # Device tokens
│   │   └── utils/
│   │       ├── openai_tools.py  # OpenAI integration
│   │       └── fcm.py           # FCM notifications
│   ├── requirements.txt
│   ├── .env
│   └── seed.py                  # Database seeding script
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VisitorsList.jsx
│   │   │   ├── CreateVisitor.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   └── AuditLog.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── auth.js
│   │   │   ├── visitors.js
│   │   │   ├── chat.js
│   │   │   └── events.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── postman/
    └── Community_App.postman_collection.json
```

---

## 💰 Basic Cost Estimation

### OpenAI API (GPT-4o-mini)

- Input: ~$0.15 per 1M tokens
- Output: ~$0.60 per 1M tokens
- Average chat interaction: ~500 tokens
- **Estimated cost**: $0.0004 per chat interaction
- Monthly (1000 chats): ~$0.40

### Supabase

- Free tier: 500MB database, 50GB bandwidth
- For small community (<100 households): Free tier sufficient
- Paid plans start at $25/month

### Firebase (FCM)

- Completely free for any volume

### Total Estimated Monthly Cost

- Small deployment: **Free - $5/month**
- Medium deployment (500 households): **$25-50/month**

---

## 🔒 Security Checklist

✅ **Implemented:**

- JWT-based authentication
- Role-based access control (RBAC)
- Supabase Row Level Security (RLS) policies
- Server-side validation for all actions
- Immutable audit log
- Token expiration
- CORS configuration
- Environment variables for secrets

⚠️ **Recommended for Production:**

- Multi-factor authentication (MFA) for admin accounts
- Rate limiting on API endpoints
- Input sanitization and validation
- HTTPS/TLS encryption
- Password hashing (currently simplified for demo)
- Database backups
- Error logging and monitoring
- API key rotation policy

---

## 🎯 Features Implemented

### Core Features (MVP)

- ✅ Authentication with JWT
- ✅ Role-based access control (Resident, Guard, Admin)
- ✅ Visitor creation and management
- ✅ Visitor approval/denial workflow
- ✅ Check-in/check-out functionality
- ✅ AI Copilot with OpenAI function calling
- ✅ Real-time notifications (FCM ready)
- ✅ Immutable audit log
- ✅ Responsive web interface

### State Machine

```
pending → approved → checked_in → checked_out
       ↘ denied
```

---

## 🐛 Troubleshooting

### Backend Issues

**Port already in use:**

```bash
# Change port in uvicorn command
uvicorn app.main:app --reload --port 8001
```

**Supabase connection error:**

- Verify SUPABASE_URL and SUPABASE_KEY in `.env`
- Check internet connection
- Verify Supabase project is active

**OpenAI API error:**

- Verify OPENAI_API_KEY is correct
- Check API quota/billing

### Frontend Issues

**Cannot connect to backend:**

- Verify backend is running on port 8000
- Check VITE_API_URL in frontend `.env`
- Clear browser cache

**Login fails:**

- Verify seed.py was run successfully
- Check browser console for errors
- Verify token is being stored in localStorage

### Database Issues

**Tables not created:**

- Run SQL schema in Supabase SQL Editor
- Check for error messages in Supabase dashboard

**Seed data not appearing:**

- Check seed.py output for errors
- Verify Supabase connection
- Run seed.py again if needed

---

## 📝 API Endpoints

### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Visitors

- `GET /visitors/` - List visitors
- `POST /visitors/` - Create visitor
- `GET /visitors/{id}` - Get visitor details
- `POST /visitors/approve` - Approve visitor
- `POST /visitors/deny` - Deny visitor
- `POST /visitors/checkin` - Check in visitor
- `POST /visitors/checkout` - Check out visitor

### Chat

- `POST /chat/` - Send message to AI copilot

### Notifications

- `POST /notifications/register-token` - Register FCM token
- `DELETE /notifications/unregister-token/{token}` - Unregister token

### Audit

- `GET /events` - Get audit log events

### Health

- `GET /health` - Health check endpoint

---

## 📄 License

This project is for educational/demonstration purposes.

---

## 📹 Video


https://github.com/user-attachments/assets/b87dad50-8485-4fd1-996f-ac687f2cee31


**Built with FastAPI, React, Supabase, and OpenAI** 🚀
