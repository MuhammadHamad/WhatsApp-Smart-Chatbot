# Go-Live Checklist

## Service reliability

- [ ] `fabs-chatbot` service is enabled on boot.
- [ ] Server reboots successfully and service auto-starts.
- [ ] Health endpoint works: `curl https://your-domain.com/health`.

## Monitoring basics

- [ ] `journalctl` shows clean startup (no fatal errors).
- [ ] No repeated `401` token-expiry errors.
- [ ] No repeated `5xx` errors from outbound APIs.
- [ ] Caddy logs are rotating in `/var/log/caddy/fabs-chatbot.log`.

## Webhook and messaging

- [ ] Webhook URL set to `https://your-domain.com/webhook`.
- [ ] Verify token matches exactly.
- [ ] Inbound messages are received and processed.
- [ ] Outbound replies return `200`/`201` in logs.

## Sandbox vs production limits

- [ ] If using test/sandbox mode, required recipient numbers are allow-listed.
- [ ] Handoff number is allow-listed or production-approved.
- [ ] Team understands test-mode restrictions before external pilot.

## Secrets and access

- [ ] `.env` exists only on server and is never committed.
- [ ] Meta token is long-lived (System User), not temporary.
- [ ] Google credentials path exists and is readable by service user.

## Rollback plan

- [ ] Previous working `.env` backup is available.
- [ ] Restart command known: `sudo systemctl restart fabs-chatbot`.
- [ ] Logs command known: `sudo journalctl -u fabs-chatbot -f`.
