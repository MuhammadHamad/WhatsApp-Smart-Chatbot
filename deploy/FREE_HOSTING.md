# Free Hosting Options (Testing Phase)

This chatbot needs an always-on public HTTPS endpoint for incoming WhatsApp webhooks.  
For free testing, pick one of these:

## 1) Oracle Cloud Always Free (Recommended)

Why:
- Always-on VM (no sleep) for webhooks.
- Good for `systemd` + reverse proxy setup.
- Easiest path to production-like deployment.

What to create:
- 1x Ubuntu VM (Ampere A1 or Micro shape).
- 1 static public IP.
- Open inbound ports `22`, `80`, `443`.

High-level steps:
1. Create an Oracle Cloud account and tenancy.
2. Create a VCN/subnet with internet gateway.
3. Launch Ubuntu VM and save SSH private key.
4. Add security list rules for `80/443`.
5. SSH into VM and continue with `DEPLOY_UBUNTU.md`.

## 2) Fly.io / Render / Railway (Fallback)

Use only if Oracle is unavailable.

Important:
- Some free tiers sleep or limit always-on behavior.
- Sleeping breaks webhook reliability.
- If a free tier sleeps, move to a low-cost VPS quickly.

## 3) Local + ngrok (Not Production)

Only for short demos.
- Works while your machine is on.
- URL changes and tunnels can drop.
- Not suitable for customer testing.

## Recommendation

For your current goal ("free first, sell later"), use Oracle Always Free and keep the same architecture you'll use in paid scale:

- FastAPI app as `systemd` service
- Caddy reverse proxy with HTTPS
- Stable webhook URL
