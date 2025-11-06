# 🚀 Vercel Deployment Guide

## Overview

The eval tool automatically switches storage backends:
- **Local Dev**: JSON files (fast, no setup)
- **Production (Vercel)**: MongoDB (persistent storage)

---

## 📋 Prerequisites

1. **MongoDB Atlas Account** (you already have this ✅)
2. **Vercel Account** (free tier works)
3. **GitHub Repository** (already set up ✅)

---

## 🔧 Step 1: MongoDB Atlas Setup

### Get Your Connection String

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. Copy the connection string (looks like):
   ```
   mongodb+srv://username:password@cluster.mongodb.net/
   ```
5. Replace `<password>` with your actual password
6. Add the database name at the end:
   ```
   mongodb+srv://username:password@cluster.mongodb.net/llm_reviews
   ```

### Create Database & Collection (Optional)

MongoDB will auto-create these, but if you want to do it manually:
1. Click **"Browse Collections"**
2. Click **"Create Database"**
3. Database name: `llm_reviews`
4. Collection name: `reviews`

---

## 🚀 Step 2: Deploy to Vercel

### Option A: Deploy from GitHub (Recommended)

1. Go to [vercel.com](https://vercel.com)
2. Click **"New Project"**
3. Import your GitHub repository: `moti-og/eval-tool`
4. Configure:
   - **Framework Preset**: Streamlit (or Other)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run human_review_app.py --server.port $PORT`

### Option B: Deploy from CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd "C:\Users\msokrin\OneDrive - OpenGov, Inc\Useful files\eval-tool"
vercel
```

---

## 🔐 Step 3: Set Environment Variables

In Vercel Dashboard:

1. Go to your project → **Settings** → **Environment Variables**
2. Add these variables:

| Variable Name | Value | Example |
|---------------|-------|---------|
| `MONGODB_URI` | Your MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/llm_reviews` |
| `MONGODB_DB_NAME` | Database name (optional) | `llm_reviews` |
| `MONGODB_COLLECTION` | Collection name (optional) | `reviews` |
| `POSTGRES_URL` | Your Postgres connection (if loading data) | `postgresql://user:pass@host/db` |

3. Click **"Save"**
4. Redeploy your app (or it will auto-redeploy)

---

## ✅ Step 4: Verify Deployment

1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Check the logs for: `📦 Using MongoDB storage (production mode)`
3. Submit a test review
4. Check MongoDB Atlas → Browse Collections → `reviews` collection
5. You should see your review data!

---

## 🔄 Step 5: Load Existing Data (Optional)

If you want to load your existing PostgreSQL AI interactions into production:

### Option A: Run locally, then sync to MongoDB

```bash
# 1. Load from Postgres to JSON locally
python load_from_postgres.py

# 2. Export to MongoDB-compatible format
python -c "
import json
from pathlib import Path

# Load pending reviews
reviews = json.loads(Path('review_data/pending_reviews.json').read_text())
print(f'Loaded {len(reviews)} reviews ready for evaluation')
"

# 3. In production, reviews will auto-save to MongoDB when submitted
```

### Option B: Direct MongoDB import (advanced)

```bash
# Export from Postgres to JSONL
python load_from_postgres.py

# Import to MongoDB (requires mongoimport)
mongoimport --uri "mongodb+srv://..." --collection reviews --file pending_reviews.json --jsonArray
```

---

## 📊 Production Features

Once deployed, your reviews are:
- ✅ **Persistent** (survive deployments/restarts)
- ✅ **Queryable** (use MongoDB Compass or queries)
- ✅ **Backed up** (MongoDB Atlas auto-backups)
- ✅ **Scalable** (handles any review volume)

---

## 🐛 Troubleshooting

### Issue: "MONGODB_URI not set in production environment"

**Fix**: Add `MONGODB_URI` environment variable in Vercel dashboard

### Issue: "Cannot connect to MongoDB"

**Check**:
1. MongoDB Atlas → Network Access → Allow access from anywhere (`0.0.0.0/0`)
2. Connection string includes password
3. Database user has read/write permissions

### Issue: App shows JSON storage in production

**Check**: 
1. `MONGODB_URI` is set in Vercel environment variables
2. Redeploy after adding env vars
3. Check Vercel logs for connection errors

### Issue: Reviews not persisting

**Check**:
1. MongoDB Atlas → Browse Collections → Verify data is there
2. Check Vercel function logs for errors
3. Verify `MONGODB_DB_NAME` and `MONGODB_COLLECTION` match your setup

---

## 🔗 Useful Links

- **MongoDB Atlas**: https://cloud.mongodb.com
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Your Repository**: https://github.com/moti-og/eval-tool
- **MongoDB Compass** (GUI): https://www.mongodb.com/products/compass

---

## 🎯 Quick Checklist

- [ ] MongoDB Atlas cluster created
- [ ] Connection string copied
- [ ] Vercel project created from GitHub
- [ ] `MONGODB_URI` set in Vercel env vars
- [ ] App deployed and accessible
- [ ] Test review submitted successfully
- [ ] Review visible in MongoDB Atlas
- [ ] Local dev still works with JSON

---

**Need help?** Check the Vercel logs or MongoDB Atlas monitoring for specific errors.

