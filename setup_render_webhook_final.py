#!/usr/bin/env python3
"""
Script to set up Telegram webhook for Render.com deployment.
Run this after your Render services are deployed and running.
"""
import requests
import sys

# Configuration
BOT_TOKEN = "8370296832:AAETV_lHGioGKllkVraWZE2JUOKoFF0gZas"
RENDER_WEB_URL = "https://your-app-name.onrender.com"  # Replace with your actual Render web service URL

# Telegram API endpoints
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
SET_WEBHOOK_URL = f"{TELEGRAM_API_BASE}/setWebhook"
GET_WEBHOOK_INFO_URL = f"{TELEGRAM_API_BASE}/getWebhookInfo"
DELETE_WEBHOOK_URL = f"{TELEGRAM_API_BASE}/deleteWebhook"


def delete_webhook():
    """Delete existing webhook."""
    print("🗑️  Deleting existing webhook...")
    response = requests.post(DELETE_WEBHOOK_URL)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            print("✅ Existing webhook deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete webhook: {result.get('description')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False


def set_webhook(webhook_url):
    """Set new webhook URL."""
    print(f"🔧 Setting webhook to: {webhook_url}")
    
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True  # Clear any pending updates
    }
    
    response = requests.post(SET_WEBHOOK_URL, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            print("✅ Webhook set successfully!")
            return True
        else:
            print(f"❌ Failed to set webhook: {result.get('description')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False


def get_webhook_info():
    """Get current webhook information."""
    print("\n📊 Fetching webhook info...")
    response = requests.get(GET_WEBHOOK_INFO_URL)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("ok"):
            info = result.get("result", {})
            print("\n" + "="*60)
            print("WEBHOOK INFORMATION")
            print("="*60)
            print(f"URL: {info.get('url', 'Not set')}")
            print(f"Has custom certificate: {info.get('has_custom_certificate', False)}")
            print(f"Pending update count: {info.get('pending_update_count', 0)}")
            print(f"Max connections: {info.get('max_connections', 'N/A')}")
            print(f"Allowed updates: {info.get('allowed_updates', [])}")
            
            if info.get('last_error_date'):
                print(f"\n⚠️  Last error date: {info.get('last_error_date')}")
                print(f"Last error message: {info.get('last_error_message', 'N/A')}")
            else:
                print("\n✅ No errors reported")
            
            print("="*60 + "\n")
            return True
        else:
            print(f"❌ Failed to get webhook info: {result.get('description')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False


def test_health_check(base_url):
    """Test the health check endpoint."""
    health_url = f"{base_url}/health"
    print(f"🏥 Testing health check: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check error: {e}")
        return False


def main():
    """Main function to set up webhook."""
    print("\n" + "="*60)
    print("TELEGRAM WEBHOOK SETUP FOR RENDER.COM")
    print("="*60 + "\n")
    
    # Check if user updated the URL
    if "your-app-name" in RENDER_WEB_URL:
        print("❌ ERROR: Please update RENDER_WEB_URL in this script with your actual Render web service URL")
        print("\nYou can find your URL in the Render dashboard:")
        print("1. Go to https://dashboard.render.com")
        print("2. Click on your web service (ai-video-bot-web)")
        print("3. Copy the URL (e.g., https://ai-video-bot-web-xxxx.onrender.com)")
        print("4. Update RENDER_WEB_URL in this script")
        sys.exit(1)
    
    # Test health check first
    if not test_health_check(RENDER_WEB_URL):
        print("\n⚠️  Warning: Health check failed. Make sure your Render service is running.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(1)
    
    # Delete existing webhook
    delete_webhook()
    
    # Set new webhook
    webhook_url = f"{RENDER_WEB_URL}/webhook"
    if set_webhook(webhook_url):
        # Get and display webhook info
        get_webhook_info()
        
        print("\n✅ Webhook setup complete!")
        print("\n📝 Next steps:")
        print("1. Open Telegram and find your bot")
        print("2. Send /start command")
        print("3. Send a test message")
        print("4. Monitor logs in Render dashboard")
        print("\n" + "="*60 + "\n")
    else:
        print("\n❌ Webhook setup failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
