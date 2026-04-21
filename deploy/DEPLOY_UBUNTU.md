# Ubuntu Deployment (Always-On Service)

This guide deploys the chatbot as a background service on Ubuntu.

## 1) Install system packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip git curl
```

## 2) Clone project

```bash
sudo mkdir -p /opt/fabs_chatbot
sudo chown "$USER":"$USER" /opt/fabs_chatbot
cd /opt/fabs_chatbot

# Option A: clone from git
# git clone <your-repository-url> .

# Option B: upload project files via SCP/SFTP
```

## 3) Create virtual environment

```bash
cd /opt/fabs_chatbot
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Configure environment

```bash
cd /opt/fabs_chatbot
cp .env.example .env
nano .env
```

Fill all required variables with production/test values.

## 5) Install systemd service

```bash
sudo cp deploy/fabs-chatbot.service /etc/systemd/system/fabs-chatbot.service
sudo systemctl daemon-reload
sudo systemctl enable fabs-chatbot
sudo systemctl start fabs-chatbot
```

## 6) Verify service

```bash
sudo systemctl status fabs-chatbot
sudo journalctl -u fabs-chatbot -f
curl http://127.0.0.1:8000/health
```

Expected health response:

```json
{"status":"ok"}
```

## Common fixes

- If service cannot import modules:
  - check `WorkingDirectory` in service file.
- If `.env` changes do not apply:
  - run `sudo systemctl restart fabs-chatbot`.
- If startup fails:
  - check logs with `journalctl` and verify credentials path.
