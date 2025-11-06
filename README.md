# LLM Evaluation Tool

Simple tool for evaluating and reviewing LLM outputs from OpenGov's AI features.

---

## 📖 Read This First

**[→ ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system overview and setup guide

**That's the only doc you need.** Everything else is reference material.

---

## Quick Start

### 1. Seed Data from Postgres

```bash
python load_from_postgres.py
```

### 2. Upload to MongoDB

```bash
python seed_mongodb.py
```

### 3. Deploy

```bash
vercel deploy
```

Done! See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

---

## Reference Docs

- **[POSTGRES_SETUP.md](POSTGRES_SETUP.md)** - Postgres connection via Teleport
- **[TELEPORT_SETUP.md](TELEPORT_SETUP.md)** - Teleport proxy setup
- **[QUICKSTART.md](QUICKSTART.md)** - Original automated testing docs (legacy)

---

## Architecture

**Simple. No servers. No complexity.**

```
Postgres → Python Script → MongoDB → Static HTML UI
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete details.
