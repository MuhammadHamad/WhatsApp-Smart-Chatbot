import asyncio
import httpx
from config import WHATSAPP_API_KEY, WHATSAPP_API_URL, WHATSAPP_PHONE_NUMBER_ID, OPENAI_API_KEY

async def test_all():
    print("--- Chatbot Diagnosis ---")

    # 1. Test WhatsApp Key
    print(f"\n1. Testing WhatsApp Connection (ID: {WHATSAPP_PHONE_NUMBER_ID})...")
    print(f"   Key starts with: {WHATSAPP_API_KEY[:20]}...")
    headers = {"Authorization": f"Bearer {WHATSAPP_API_KEY}", "Content-Type": "application/json"}
    try:
        url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/whatsapp_business_profile"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                print("[OK] WhatsApp Key is VALID!")
            else:
                print(f"[FAIL] WhatsApp Key FAILED (Error {resp.status_code})")
                print(f"   Details: {resp.text[:300]}")
    except Exception as e:
        print(f"[FAIL] WhatsApp Request Error: {e}")

    # 2. Test OpenRouter Key
    print(f"\n2. Testing OpenRouter Connection...")
    print(f"   Key starts with: {OPENAI_API_KEY[:20]}...")
    oa_headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://fabs-salon.com",
        "X-Title": "Fabs Salon Chatbot"
    }
    oa_payload = {
        "model": "google/gemini-2.0-flash-001:free",
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "max_tokens": 10
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=oa_headers, json=oa_payload)
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "no content")
                print(f"[OK] OpenRouter Key is VALID! AI said: {reply}")
            else:
                print(f"[FAIL] OpenRouter Key FAILED (Error {resp.status_code})")
                print(f"   Details: {resp.text[:300]}")
    except Exception as e:
        print(f"[FAIL] OpenRouter Request Error: {e}")

    print("\n--- Diagnosis Complete ---")

if __name__ == "__main__":
    asyncio.run(test_all())
