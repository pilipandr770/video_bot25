"""Set Telegram webhook to Render URL"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
webhook_url = "https://video-bot25.onrender.com/webhook"

if not token:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

print(f"🔧 Setting webhook to: {webhook_url}")

# Set webhook
response = requests.post(
    f'https://api.telegram.org/bot{token}/setWebhook',
    json={'url': webhook_url}
)

data = response.json()

if data['ok']:
    print("✅ Webhook set successfully!")
    print(f"   URL: {webhook_url}")
    
    # Get webhook info to confirm
    info_response = requests.get(f'https://api.telegram.org/bot{token}/getWebhookInfo')
    info_data = info_response.json()
    
    if info_data['ok']:
        result = info_data['result']
        print("\n📊 Webhook Status:")
        print(f"  URL: {result.get('url')}")
        print(f"  Pending updates: {result.get('pending_update_count', 0)}")
        
        if result.get('last_error_date'):
            print(f"\n⚠️ Last error: {result.get('last_error_message')}")
else:
    print(f"❌ Error: {data}")
