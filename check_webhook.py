"""Check Telegram webhook status"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')

if not token:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

print(f"🔍 Checking webhook for bot: {token[:10]}...")

# Get webhook info
response = requests.get(f'https://api.telegram.org/bot{token}/getWebhookInfo')
data = response.json()

if data['ok']:
    result = data['result']
    print("\n📊 Webhook Status:")
    print(f"  URL: {result.get('url', 'Not set')}")
    print(f"  Has custom certificate: {result.get('has_custom_certificate', False)}")
    print(f"  Pending update count: {result.get('pending_update_count', 0)}")
    print(f"  Max connections: {result.get('max_connections', 'N/A')}")
    
    if result.get('last_error_date'):
        print(f"\n⚠️ Last error:")
        print(f"  Date: {result.get('last_error_date')}")
        print(f"  Message: {result.get('last_error_message')}")
    
    if not result.get('url'):
        print("\n❌ Webhook is NOT set!")
        print("💡 Bot is not receiving updates via webhook.")
        print("   Use polling mode (test_bot_polling.py) or set webhook URL.")
    else:
        print("\n✅ Webhook is configured!")
else:
    print(f"❌ Error: {data}")
