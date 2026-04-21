# Token and Secrets Setup

## 1) Use a long-lived Meta token

Temporary access tokens expire quickly and cause reply failures (`401`, code `190`, subcode `463`).

For production:
- Create a **System User** in Meta Business Manager.
- Generate a long-lived token with WhatsApp permissions.
- Replace `WHATSAPP_API_KEY` in `.env`.

After changing `.env`:

```bash
sudo systemctl restart fabs-chatbot
```

## 2) Keep `.env` consistent

Required keys:
- `WHATSAPP_API_KEY`
- `WHATSAPP_PHONE_NUMBER_ID`
- `OPENAI_API_KEY`
- `GOOGLE_SHEET_ID`
- `GOOGLE_CREDENTIALS_JSON`
- `HANDOFF_PHONE_NUMBER`
- `WEBHOOK_VERIFY_TOKEN`

## 3) Verify secrets quickly

Run these checks:

```bash
sudo systemctl status fabs-chatbot
sudo journalctl -u fabs-chatbot -n 100 --no-pager
```

Look for:
- no startup fatal errors
- successful `/webhook` POST handling
- successful outbound WhatsApp API responses (`200`/`201`)

## 4) Security rules

- Never commit `.env` or service-account JSON.
- Store credentials in a private path (e.g. `/opt/fabs_chatbot/credentials.json`).
- Rotate Meta/OpenRouter keys if leaked.
