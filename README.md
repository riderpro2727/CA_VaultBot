# 🎓 CA Vault Bot

**A production-ready Telegram bot for CA & Commerce study resources, powered by Google Drive, PostgreSQL, and Redis.**

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 🔍 **Smart Search** | Fuzzy, typo-tolerant, synonym-aware search engine |
| 📚 **Google Drive Integration** | Multi-folder, recursive scanning with unlimited drives |
| ⚡ **Real-time Indexing** | Auto-rescan every 10 minutes, detect new/deleted/renamed files |
| 🧠 **AI Ranking** | Results ranked by relevance, popularity, clicks & recency |
| 📁 **14+ File Types** | PDF, PPT, ZIP, MP4, Excel, DOCX, and more |
| ⭐ **Favorites** | Save and manage favorite resources |
| 📜 **Search History** | Track and clear search history |
| 📊 **User Dashboard** | Activity score, stats, and badges |
| 🛡️ **Admin Panel** | Full Telegram-based admin with no web UI needed |
| 🔒 **Security** | Rate limiting, input validation, admin-only commands |
| 📈 **Analytics** | Search trends, top files, active users |
| 🐳 **Docker Ready** | One command to deploy |

---

## 📦 Tech Stack

- **Bot Framework**: python-telegram-bot v20 (async)
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Cache**: Redis (search cache, rate limiting, sessions)
- **Search**: RapidFuzz (fuzzy matching + synonym expansion)
- **Google Drive**: Google Drive API v3 with service account
- **Scheduler**: APScheduler (background indexing)
- **Logging**: Loguru (structured JSON logs)
- **Performance**: uvloop, async connection pooling

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Google Cloud service account with Drive API enabled
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

---

### 1. Clone & Setup

```bash
cd ca_vault_bot
cp .env.example .env
# Edit .env with your credentials
```

---

### 2. Google Drive Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable **Google Drive API**
4. Create a **Service Account**
5. Generate a JSON key and save as `service_account.json`
6. Share your Google Drive folders with the service account email

---

### 3. Environment Configuration

Edit `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789,987654321
DATABASE_URL=postgresql+asyncpg://cavault:password@localhost:5432/cavault_db
REDIS_URL=redis://localhost:6379/0
GOOGLE_SERVICE_ACCOUNT_JSON=./service_account.json
```

---

### 4. Deploy with Docker (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop
docker-compose down
```

---

### 5. Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis
# (or use docker-compose up -d db redis)

# Run the bot
python main.py
```

---

## 🤖 Bot Commands

### User Commands
| Command | Description |
|---------|-------------|
| `/start` | Register and open main menu |
| `/cancel` | Cancel current operation |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/admin` | Open admin dashboard |
| `/adddrive <folder_id> [name]` | Add Google Drive folder |
| `/removedrive <folder_id>` | Remove Drive folder |
| `/listdrives` | List all drive sources |
| `/reindex [drive_id]` | Trigger manual reindex |
| `/stats` | View bot statistics |
| `/broadcast <message>` | Send message to all users |

---

## 📁 Project Structure

```
ca_vault_bot/
├── main.py                 # Entry point
├── config/
│   └── settings.py        # Pydantic settings
├── database/
│   ├── models.py          # SQLAlchemy ORM models
│   ├── engine.py          # Async engine & sessions
│   └── repositories.py   # Data access layer
├── cache/
│   └── redis_client.py   # Redis cache service
├── google_drive/
│   └── client.py         # Drive API client
├── search/
│   └── engine.py         # Multi-strategy search engine
├── indexer/
│   ├── engine.py         # Indexing engine
│   └── scheduler.py      # Background scheduler
├── services/
│   ├── user_service.py   # User business logic
│   ├── drive_service.py  # Drive business logic
│   └── search_service.py # Search business logic
├── bot/
│   ├── application.py    # PTB app builder
│   ├── keyboards.py      # Inline keyboards
│   └── messages.py       # Message templates
├── handlers/
│   ├── start.py          # Registration flow
│   ├── callbacks.py      # Callback dispatcher
│   ├── admin.py          # Admin commands
│   ├── search.py         # Search conversations
│   └── message.py        # Text message handler
├── middlewares/
│   └── rate_limiter.py   # Rate limiting
├── migrations/
│   └── versions/         # Alembic migrations
├── utils/
│   ├── helpers.py        # General utilities
│   ├── file_utils.py     # File type detection
│   └── logger.py        # Logging setup
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🔧 Adding Drive Sources

### Via Bot Command
```
/adddrive 1BxiMVs0XRA5nFMdKvBdBZjgmUUq "CA Final Notes"
/adddrive SHARED_DRIVE_ID "Shared Resources" --shared
```

### Via Admin Panel
1. Send `/admin` to the bot
2. Tap **💾 Drives**
3. Tap **➕ Add Drive**
4. Follow the instructions

---

## 📊 How Search Works

1. **Exact Match** — Direct substring match (score: 100)
2. **Token Match** — All query words found in filename (score: 95)
3. **Partial Match** — Some query words match (score: 50-90)
4. **Fuzzy Match** — RapidFuzz WRatio (typo-tolerant)
5. **Synonym Expansion** — `acc` → searches for `accounting`, `accounts`
6. **Ranking Boost** — Popularity, download count, recency

---

## 🚀 Deployment on Render

1. Create a new **Background Worker** service
2. Set Build Command: `pip install -r requirements.txt`
3. Set Start Command: `python main.py`
4. Add environment variables from `.env.example`
5. Add PostgreSQL and Redis add-ons

---

## 🚀 Deployment on Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Add required environment variables in Railway dashboard.

---

## 📝 License

MIT License — Free for personal and commercial use.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Open a Pull Request

---

*Built with ❤️ for CA students across India*
