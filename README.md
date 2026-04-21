# Fab's Beauty Salon — WhatsApp Chatbot

Production-ready WhatsApp chatbot for **Fab's Beauty Salon** using the **Meta WhatsApp Cloud API**, built with Python + FastAPI.

---

## Features

- Receives and validates incoming WhatsApp webhooks from Meta WhatsApp Cloud API
- Parses text messages and extracts sender info, message ID, timestamp
- Rule-based keyword replies for services, hours, booking, and location
- Politely rejects non-text messages (images, voice notes, stickers)
- Duplicate message detection (in-memory, last 100 messages)
- Retry logic (max 2 retries with linear back-off) for outgoing messages
- Conversation logging to Google Sheets
- Health check endpoint for monitoring

---

## Architecture

```
Customer (WhatsApp)
       │
       ▼
 Meta Cloud API  ──▶  POST /webhook  ──▶  message_parser.py
                                  │
                                  ▼
                          webhook.py (routing logic)
                          ┌───────────┴───────────┐
                          ▼                       ▼
                    responder.py            logger.py
                  (send reply via         (log to Google
                   Meta API)                Sheets)
```

---

## Prerequisites

- **Python 3.11+**
- **Ubuntu 22.04 VPS** (tested)
- **Meta WhatsApp Cloud API access** with an approved WhatsApp Business number
- **Google Cloud service account** with Sheets API enabled
- **Domain name** pointed at your VPS IP (for SSL)

---

## Deployment on Ubuntu 22.04 VPS

For a clean production rollout, use the step-by-step runbooks in `deploy/`:

- `deploy/FREE_HOSTING.md`
- `deploy/DEPLOY_UBUNTU.md`
- `deploy/HTTPS_SETUP.md`
- `deploy/TOKEN_AND_SECRETS.md`
- `deploy/WEBHOOK_CUTOVER.md`
- `deploy/GO_LIVE_CHECKLIST.md`

### 1. System Update & Python Installation

```bash
# Update package list and upgrade existing packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and essential tools
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git curl
```

### 2. Clone the Project

```bash
# Clone your repo (or upload files via scp/sftp)
cd /opt
sudo mkdir -p fabs_chatbot
sudo chown $USER:$USER fabs_chatbot
cd fabs_chatbot

# Copy/clone your project files here
# git clone https://github.com/your-repo/fabs_chatbot.git .
```

### 3. Create Virtual Environment & Install Dependencies

```bash
cd /opt/fabs_chatbot

# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit with your real values
nano .env
```

Fill in all variables:
- `WHATSAPP_API_KEY` — long-lived Meta/WhatsApp token
- `WHATSAPP_PHONE_NUMBER_ID` — your WhatsApp phone number ID
- `OPENAI_API_KEY` — from OpenRouter/OpenAI-compatible provider
- `OPENROUTER_MODEL` — model slug (example: `openai/gpt-4o-mini`)
- `GOOGLE_SHEET_ID` — the ID from your Google Sheets URL
- `GOOGLE_CREDENTIALS_JSON` — absolute path to your service account JSON file
- `HANDOFF_PHONE_NUMBER` — staff WhatsApp for escalations
- `WEBHOOK_VERIFY_TOKEN` — a strong random string you choose

### 5. Upload Google Credentials

```bash
# Upload your service account JSON file to the server
# Example using scp from your local machine:
# scp credentials.json user@your-server:/opt/fabs_chatbot/credentials.json

# Make sure the path in .env matches
```

### 6. Test Run

```bash
cd /opt/fabs_chatbot
source venv/bin/activate

# Run directly to test (auto-reloads on code changes in development)
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info --reload

# Test health endpoint
# From another terminal:
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

### 7. Set Up systemd Service (Auto-Restart on Crash/Reboot)

Create the service file:

```bash
sudo nano /etc/systemd/system/fabs-chatbot.service
```

Paste the following:

```ini
[Unit]
Description=Fab's Beauty Salon WhatsApp Chatbot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/fabs_chatbot
Environment="PATH=/opt/fabs_chatbot/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/opt/fabs_chatbot/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2 --log-level info
Restart=always
RestartSec=5
StartLimitBurst=5
StartLimitIntervalSec=60

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/fabs_chatbot

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fabs-chatbot

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
# Fix ownership for www-data
sudo chown -R www-data:www-data /opt/fabs_chatbot

# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable fabs-chatbot

# Start the service
sudo systemctl start fabs-chatbot

# Check status
sudo systemctl status fabs-chatbot

# View logs
sudo journalctl -u fabs-chatbot -f
```

### 8. Set Up Caddy as Reverse Proxy with Automatic SSL

Install Caddy:

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

Configure Caddy:

```bash
sudo nano /etc/caddy/Caddyfile
```

Paste this (replace `your-domain.com` with your actual domain):

```caddyfile
your-domain.com {
    reverse_proxy 127.0.0.1:8000

    # Security headers
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }

    # Access logging
    log {
        output file /var/log/caddy/fabs-chatbot.log {
            roll_size 10mb
            roll_keep 5
        }
    }
}
```

Start Caddy:

```bash
# Create log directory
sudo mkdir -p /var/log/caddy

# Restart Caddy to apply config
sudo systemctl restart caddy

# Verify Caddy is running
sudo systemctl status caddy

# Caddy automatically provisions SSL via Let's Encrypt!
```

### 9. Configure Meta Webhook URL

1. Open your Meta app dashboard for WhatsApp webhook configuration
2. Go to **WhatsApp → Configuration → Webhook**
3. Set the callback URL to:
   ```
   https://your-domain.com/webhook
   ```
4. Set the verify token to the same value as `WEBHOOK_VERIFY_TOKEN` in your `.env`
5. Save, verify, and test the connection

### 10. Verify Everything Works

```bash
# Check the bot is running
curl https://your-domain.com/health

# Check systemd service
sudo systemctl status fabs-chatbot

# Watch live logs
sudo journalctl -u fabs-chatbot -f

# Send a WhatsApp message to your bot number and watch the logs!
```

---

## Useful Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl start fabs-chatbot` | Start the bot |
| `sudo systemctl stop fabs-chatbot` | Stop the bot |
| `sudo systemctl restart fabs-chatbot` | Restart the bot |
| `sudo systemctl status fabs-chatbot` | Check bot status |
| `sudo journalctl -u fabs-chatbot -f` | Follow live logs |
| `sudo journalctl -u fabs-chatbot --since "1 hour ago"` | View recent logs |

---

## Project Structure

```
fabs_chatbot/
├── main.py              ← FastAPI app entry point
├── config.py            ← All environment variables loaded here
├── webhook.py           ← Receives and validates incoming WhatsApp webhooks
├── message_parser.py    ← Extracts sender phone, message text, ID, timestamp
├── responder.py         ← Sends replies back via Meta WhatsApp API
├── logger.py            ← Logs every conversation turn to Google Sheets
├── requirements.txt     ← All dependencies
├── .env.example         ← Template showing all required environment variables
├── .env                 ← Your actual environment variables (DO NOT COMMIT)
└── README.md            ← This file
```

---

## Security Notes

- **Never commit `.env`** — it contains secrets. Add it to `.gitignore`.
- The systemd service runs as `www-data` with strict filesystem protections.
- Caddy handles SSL termination with automatic certificate renewal.
- The webhook verify token prevents unauthorized webhook registrations.

---

## License

Private — Fab's Beauty Salon. All rights reserved.
# WhatsApp-Smart-Chatbot
