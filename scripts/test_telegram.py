import asyncio
import os
import sys

import httpx

# Інжект кореня проєкту для імпорту backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import get_settings


async def test_telegram_bot() -> None:
    settings = get_settings()

    token = settings.telegram_bot_token.get_secret_value()
    chat_id = settings.telegram_chat_id

    if not token or "placeholder" in token:
        print("[ERROR] TELEGRAM_BOT_TOKEN не налаштовано у .env")
        sys.exit(1)

    if not chat_id or "000000" in chat_id:
        print("[ERROR] TELEGRAM_CHAT_ID не налаштовано у .env")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "✅ [Test] Систему Restaurant Voice Agent успішно підключено до Telegram.",
        "parse_mode": "HTML",
    }

    print(f"Відправка тестового повідомлення у chat_id: {chat_id}...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            print("[OK] Тестове повідомлення успішно доставлено.")
        except httpx.HTTPStatusError as e:
            print(f"[ERROR] Помилка API Telegram: {e.response.status_code} - {e.response.text}")
            sys.exit(1)
        except httpx.RequestError as e:
            print(f"[ERROR] Мережева помилка при підключенні до Telegram: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_telegram_bot())
