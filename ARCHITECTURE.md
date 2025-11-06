# 🏗️ Architecture: Simple Static UI + MongoDB

## Overview

**No servers. No complexity. Just works.**

```
Postgres (read-only) → Python script → MongoDB → Static HTML/JS UI
```

---

## How It Works

### 1. **Seed Data (Local, One-Time)**

```bash
# Pull data from Postgres
python load_from_postgres.py

# This creates review_data/pending_reviews.json locally
```

### 2. **Upload to MongoDB (Local Script)**

```bash
# Upload the seeded data to MongoDB
python seed_mongodb.py

# This pushes pending_reviews.json → MongoDB Atlas
```

### 3. **Deploy Static UI (Vercel)**

```bash
# Deploy the static HTML/JS app
vercel deploy

# UI reads from MongoDB, writes reviews back to MongoDB
```

### 4. **To Update Data**

```bash
# Re-run seed scripts locally
python load_from_postgres.py
python seed_mongodb.py

# Redeploy (or it auto-deploys from GitHub)
git push
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     LOCAL (Your Machine)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Postgres (read-only) ──┐                               │
│                          │                               │
│                          ▼                               │
│              load_from_postgres.py                       │
│                          │                               │
│                          ▼                               │
│           review_data/pending_reviews.json               │
│                          │                               │
│                          ▼                               │
│                  seed_mongodb.py ─────────┐             │
│                                            │             │
└────────────────────────────────────────────┼─────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────┐
                              │   MongoDB Atlas (Cloud)   │
                              │                          │
                              │  - pending_reviews coll  │
                              │  - completed_reviews     │
                              └──────────────────────────┘
                                             ▲
                                             │
                              ┌──────────────┴───────────┐
                              │                          │
                         READ │                          │ WRITE
                              │                          │
                              │                          │
                    ┌─────────┴──────────────────────────┴────┐
                    │        VERCEL (Static Deploy)           │
                    ├─────────────────────────────────────────┤
                    │                                         │
                    │  index.html (Static UI)                 │
                    │     │                                   │
                    │     ├─ Fetch pending reviews            │
                    │     ├─ Display for human review         │
                    │     └─ Submit completed reviews         │
                    │                                         │
                    │  api/config.js (1 tiny function)        │
                    │     └─ Returns MongoDB API credentials  │
                    │                                         │
                    └─────────────────────────────────────────┘
```

---

## Files Structure

```
eval-tool/
├── index.html              # Static UI (deploys to Vercel)
├── api/
│   └── config.js           # Serverless function (returns MongoDB config)
├── load_from_postgres.py   # Seed script: Postgres → JSON
├── seed_mongodb.py         # Seed script: JSON → MongoDB
├── vercel.json             # Vercel deployment config
├── requirements.txt        # Python deps (local only)
├── ARCHITECTURE.md         # This file
└── DEPLOY.md              # Deployment guide
```

---

## Setup Guide

### **One-Time Setup**

#### 1. MongoDB Atlas Setup

1. Get connection string from MongoDB Atlas
2. Create database: `llm_reviews`
3. Create collections: `pending_reviews`, `completed_reviews`
4. Set up Data API (easier than driver for static sites)

#### 2. Environment Variables (Vercel)

```bash
# In Vercel dashboard → Settings → Environment Variables
MONGODB_DATA_API_KEY=your_api_key
MONGODB_CLUSTER_URL=https://data.mongodb-api.com/app/your-app-id
```

---

## Daily Workflow

### **To Review AI Outputs:**

1. Open https://your-app.vercel.app
2. Review items
3. Submit feedback
4. All saved to MongoDB automatically

### **To Add New Data:**

```bash
# On your local machine
python load_from_postgres.py    # Pull latest from Postgres
python seed_mongodb.py           # Upload to MongoDB

# That's it! UI will show new data immediately
```

---

## Why This Is Simple

✅ **No servers** - Static HTML/JS  
✅ **One tiny serverless function** - Just returns config (17 lines)  
✅ **No Streamlit** - Just plain HTML/CSS/JS  
✅ **No builds** - Deploy static files only  
✅ **No state management** - MongoDB handles everything  

**Total deployment:** `index.html` + `api/config.js` + environment variables

---

## MongoDB Data API (The Key)

Instead of Python backend, we use **MongoDB Data API**:

```javascript
// In index.html
fetch('https://data.mongodb-api.com/app/your-app/endpoint/data/v1/action/findOne', {
  method: 'POST',
  headers: {
    'api-key': 'YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    dataSource: 'Cluster0',
    database: 'llm_reviews',
    collection: 'pending_reviews'
  })
})
```

**No backend needed!** The static HTML calls MongoDB directly.

---

## Security

- ✅ API keys in Vercel env vars
- ✅ MongoDB IP whitelist (allow from anywhere for Data API)
- ✅ Read-only Postgres connection (already set up)
- ✅ MongoDB user with limited permissions

---

## That's It

Three files:
1. `index.html` - The UI
2. `load_from_postgres.py` - Seed from Postgres
3. `seed_mongodb.py` - Upload to MongoDB

Zero complexity. Zero servers. Just works.

