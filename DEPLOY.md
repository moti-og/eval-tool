# 🚀 Deployment Guide

## Prerequisites

1. ✅ MongoDB Atlas account with Data API enabled
2. ✅ Vercel account
3. ✅ Data seeded (ran `load_from_postgres.py` and `seed_mongodb.py`)

---

## Step 1: Enable MongoDB Data API

### In MongoDB Atlas:

1. Go to your cluster → **Data API** (left sidebar)
2. Click **"Enable Data API"**
3. Click **"Create API Key"**
   - Name: `vercel-eval-tool`
   - Permissions: Read and Write
   - Click **"Generate API Key"**
4. **Copy and save** the API Key (you'll only see it once!)
5. Copy the **Data API Endpoint URL** (looks like):
   ```
   https://data.mongodb-api.com/app/data-xxxxx/endpoint/data/v1
   ```

---

## Step 2: Deploy to Vercel

### Option A: Via Vercel Dashboard (Easiest)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import `moti-og/eval-tool` from GitHub
3. Click **"Deploy"** (it will fail initially - that's OK!)
4. After deployment, go to **Settings** → **Environment Variables**
5. Add these two variables:
   ```
   MONGODB_DATA_API_URL=https://data.mongodb-api.com/app/data-xxxxx/endpoint/data/v1
   MONGODB_API_KEY=your-api-key-here
   ```
6. Go to **Deployments** → Click "..." → **"Redeploy"**

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd "C:\Users\msokrin\OneDrive - OpenGov, Inc\Useful files\eval-tool"
vercel

# Add environment variables
vercel env add MONGODB_DATA_API_URL
# Paste your Data API URL

vercel env add MONGODB_API_KEY
# Paste your API key

# Redeploy with env vars
vercel --prod
```

---

## Step 3: Configure the App

After deployment, Vercel needs to inject the environment variables into your static HTML.

### Create `api/config.js` (Vercel Function):

The index.html will fetch config from `/api/config` which returns the env vars.

Actually, **simpler approach**: Use Vercel's build step to replace placeholders.

### Update `vercel.json`:

```json
{
  "build": {
    "env": {
      "MONGODB_DATA_API_URL": "@mongodb-data-api-url",
      "MONGODB_API_KEY": "@mongodb-api-key"
    }
  }
}
```

Wait, even simpler...

---

## ⚡ SIMPLEST APPROACH

Just use one tiny serverless function to serve config:

**`api/config.js`:**
```javascript
module.exports = (req, res) => {
  res.json({
    apiUrl: process.env.MONGODB_DATA_API_URL,
    apiKey: process.env.MONGODB_API_KEY,
    dataSource: 'Cluster0',
    database: 'llm_reviews',
    pendingCollection: 'pending_reviews',
    completedCollection: 'completed_reviews'
  });
};
```

Then index.html fetches from `/api/config` on load!

---

## Step 4: Verify

1. Visit your Vercel URL: `https://eval-tool-xyz.vercel.app`
2. You should see: "Loading reviews..."
3. Reviews should load from MongoDB
4. Submit a test review
5. Check MongoDB Atlas → Browse Collections → `completed_reviews`
6. Should see your review! 🎉

---

## Troubleshooting

### "Error loading reviews"

- Check MongoDB Data API is enabled
- Verify API key has Read/Write permissions
- Check network access allows Data API (0.0.0.0/0)

### "No pending reviews"

- Run `seed_mongodb.py` locally to upload reviews
- Check MongoDB Atlas → Browse Collections → `pending_reviews`

### Config not loading

- Check Vercel environment variables are set
- Redeploy after adding env vars
- Check browser console for errors

---

## Daily Workflow

### To Add New Reviews:

```bash
# On local machine
python load_from_postgres.py   # Pull from Postgres
python seed_mongodb.py          # Upload to MongoDB
```

That's it! New reviews appear immediately in the UI.

### To Review:

Just open: `https://your-app.vercel.app`

---

## Security Notes

✅ API keys stored in Vercel env vars (not in code)  
✅ MongoDB API key with limited permissions  
✅ Data API whitelist (optional, can restrict to Vercel IPs)  
✅ No sensitive data in git repository  

---

**That's it! Static HTML + MongoDB = Zero complexity deployments**

