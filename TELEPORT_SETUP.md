# Connecting to Postgres via Teleport

Guide for accessing your OpenGov Postgres database through Teleport.

## 🔐 Two Ways to Connect

### **Option 1: Teleport Database Proxy (Recommended)**

Teleport can forward the database connection to localhost.

#### Step 1: Start Teleport Proxy

```bash
# Login to Teleport
tsh login --proxy=your-teleport-proxy.com

# List available databases
tsh db ls

# Connect to your database (creates local proxy)
tsh db connect opengov-db --db-name=opengov_prod

# OR start proxy without connecting:
tsh proxy db opengov-db --db-name=opengov_prod --port=5432
```

This creates a local proxy at `localhost:5432` (or whatever port you specify)

#### Step 2: Update .env

While the proxy is running, your connection string is:

```bash
# In .env file:
POSTGRES_URL=postgresql://your-username@localhost:5432/opengov_prod
```

**Note**: The password might be automatically handled by Teleport, or you'll need to provide it.

#### Step 3: Run Discovery

```bash
python discover_postgres_data.py
```

---

### **Option 2: Teleport Database Connect (Direct)**

If you have direct access, get the connection details from Teleport:

```bash
# Show connection info
tsh db config opengov-db

# This will output something like:
# Host: localhost
# Port: 12345
# Database: opengov_prod
# User: your-user
```

Then use those details in `.env`:

```bash
POSTGRES_URL=postgresql://your-user:password@localhost:12345/opengov_prod
```

---

## 🚀 Complete Workflow with Teleport

### Terminal 1: Keep Teleport Proxy Running

```bash
# Login
tsh login --proxy=opengov.teleport.com

# Start database proxy (keep this running)
tsh proxy db opengov-prod --db-name=opengov --port=5433
# Using port 5433 to avoid conflicts with local postgres

# Keep this terminal open!
```

### Terminal 2: Run Discovery Tool

```bash
# In your eval-tool directory

# Update .env
echo 'POSTGRES_URL=postgresql://your-username@localhost:5433/opengov' > .env

# Run discovery
python discover_postgres_data.py
```

---

## 🔍 Finding Your Database Name

If you're not sure which database to connect to:

```bash
# List all databases you have access to
tsh db ls

# Output might look like:
# Name              Description              Labels
# opengov-prod      Production database      env=prod
# opengov-staging   Staging database         env=staging
# opengov-analytics Analytics database       env=prod
```

Pick the one you want (probably `opengov-prod` or `opengov-analytics`)

---

## 💡 Common Teleport Commands

```bash
# Login
tsh login --proxy=your-proxy.teleport.com

# List databases
tsh db ls

# Get connection info
tsh db config DATABASE_NAME

# Connect directly (interactive)
tsh db connect DATABASE_NAME

# Start proxy (for tools like this)
tsh proxy db DATABASE_NAME --port=5433

# Check current session
tsh status

# Logout
tsh logout
```

---

## 🛠️ Troubleshooting

### "tsh: command not found"

Install Teleport client:
- Download from: https://goteleport.com/download/
- Or ask your DevOps team for the installer

### "Access denied" or "No databases found"

You might need permissions. Ask your DevOps/Security team:
- "Can I get read access to the Postgres database for data analysis?"
- Mention you need SELECT-only access

### Port already in use (5432)

Use a different port:
```bash
tsh proxy db DATABASE_NAME --port=5433
# Then use localhost:5433 in your connection string
```

### Connection times out

Make sure:
1. Teleport proxy is still running (check Terminal 1)
2. You're not on VPN if Teleport handles that
3. Your Teleport session hasn't expired (`tsh status`)

### Can't find the right database

Ask your team:
- "What's the Teleport database name for our main Postgres?"
- "Which database has our application data?"

---

## 📋 Quick Reference Card

```bash
# 1. Login to Teleport
tsh login --proxy=your-company.teleport.com

# 2. Find your database
tsh db ls

# 3. Start proxy (keep running)
tsh proxy db YOUR_DB_NAME --port=5433

# 4. In another terminal, set connection
echo 'POSTGRES_URL=postgresql://USER@localhost:5433/DATABASE' > .env

# 5. Run discovery
python discover_postgres_data.py
```

---

## 🎯 Example: Complete Setup

```bash
# Terminal 1
$ tsh login --proxy=opengov.teleport.com
# [Login successful]

$ tsh db ls
# Name           Description
# og-prod-db     Production Postgres
# og-analytics   Analytics DB

$ tsh proxy db og-prod-db --port=5433
# Started proxy on localhost:5433
# [Keep this running...]

# Terminal 2 (in eval-tool directory)
$ echo 'POSTGRES_URL=postgresql://mike@localhost:5433/opengov_prod' > .env

$ python discover_postgres_data.py
# ✓ Connected successfully!
# Finding tables...
# [Discovery starts...]
```

---

## 🔒 Security Notes

- **Read-only access is ideal**: Ask for a read-only user
- **Session expires**: Teleport sessions timeout (usually 8-12 hours)
- **No passwords in .env**: Teleport handles authentication
- **VPN**: Some setups require VPN + Teleport

---

## ⚡ If You're Already Connected via Teleport

If you're already in a `tsh db connect` session:

```sql
-- Check what database you're in:
SELECT current_database();

-- List all tables:
\dt

-- Or in SQL:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Sample a table:
SELECT * FROM your_table LIMIT 3;
```

You can manually find the data this way, then create the query for `load_from_postgres.py`!

---

Need help with your specific Teleport setup? Share the output of `tsh db ls` and I'll help you configure it!

