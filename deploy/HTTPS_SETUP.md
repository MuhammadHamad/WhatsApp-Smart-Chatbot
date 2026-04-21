# HTTPS Setup with Caddy

## 1) Install Caddy

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

## 2) Configure DNS

Create an `A` record for your domain/subdomain:
- `bot.yourdomain.com` -> your VM public IP

Wait for DNS propagation before SSL issuance.

## 3) Configure Caddyfile

```bash
sudo cp /opt/fabs_chatbot/deploy/Caddyfile /etc/caddy/Caddyfile
sudo nano /etc/caddy/Caddyfile
```

Replace `your-domain.com` with your real domain/subdomain.

## 4) Start and verify

```bash
sudo mkdir -p /var/log/caddy
sudo systemctl restart caddy
sudo systemctl status caddy
```

Test:

```bash
curl -I https://your-domain.com/health
```

You should receive `HTTP/2 200` (or similar success status).

## Notes

- Caddy auto-manages SSL certificates (Let's Encrypt).
- Keep app bound to `127.0.0.1:8000`; expose only through Caddy.
