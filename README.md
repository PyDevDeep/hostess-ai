### ⚡ Core Tech Stack
* **AI & Voice:** OpenAI Realtime API (`gpt-4o-mini-audio-preview`)
* **Backend:** Python 3.13 + FastAPI (Async) + Uvicorn
* **Database & State:** Airtable + SQLite (`aiosqlite`)
* **Automation:** n8n (Self-hosted)
* **Frontend:** React (Vite) + WebSockets
* **Infrastructure:** Docker Compose / Structlog / Sentry


# n8n Orchestration Layer

This directory contains the automation workflows for the Restaurant Voice Booking Agent.

## Setup Instructions

1. **Start n8n**
   Ensure the n8n container is running via Docker Compose:
   `docker compose up -d n8n`

2. **Access the Dashboard**
   Navigate to `http://localhost/n8n/` (or via your VPS domain).
   Default login (from docker-compose.yml):
   - User: `admin`
   - Password: `admin`

3. **Configure Credentials**
   Go to **Credentials** in the left sidebar and add the following:
   
   - **Airtable API**: Create an Airtable Personal Access Token (PAT) with `data.records:read` and `data.records:write` scopes.
   - **Telegram API**: 
     - Open Telegram, talk to `@BotFather`, and create a new bot to get the `TELEGRAM_BOT_TOKEN`.
     - Add the bot to your admin group.
     - Send a message to the group and hit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find the `TELEGRAM_CHAT_ID`.

4. **Import Workflows**
   Go to **Workflows** -> **Import from File** and upload the following JSON files sequentially:
   - `check_availability.json`
   - `confirm_booking.json`
   - `release_on_hold.json`
   - `post_call_analytics.json`

5. **Activate**
   Set the toggle in the top right corner of each workflow to **Active**.