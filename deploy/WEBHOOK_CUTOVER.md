# Webhook Cutover and Testing

## 1) Set webhook URL in Meta/360dialog

Set:
- Webhook URL: `https://your-domain.com/webhook`
- Verify token: same value as `WEBHOOK_VERIFY_TOKEN` in `.env`

## 2) Confirm app health

```bash
curl https://your-domain.com/health
```

Expected:

```json
{"status":"ok"}
```

## 3) End-to-end inbound/outbound test

1. Send a WhatsApp message to your bot number.
2. Watch logs:

```bash
sudo journalctl -u fabs-chatbot -f
```

Look for:
- `POST /webhook` received
- `Rule-based reply` or `AI reply`
- outbound WhatsApp API call returns `200`/`201`

## 4) Common failures and fixes

- `401 Unauthorized` from Graph API:
  - token expired, rotate `WHATSAPP_API_KEY`.
- `Recipient phone number not in allowed list`:
  - add recipient in test allow-list or move to production mode.
- No incoming webhooks:
  - check DNS, HTTPS certificate, firewall, and webhook URL path.
