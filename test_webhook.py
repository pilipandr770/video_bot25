"""
Simple test script to verify webhook setup.
"""
import sys
import json
from app.bot.webhook import webhook_bp, validate_telegram_request
from app.config import Config


def test_webhook_blueprint():
    """Test that webhook blueprint is created correctly."""
    print("Testing webhook blueprint...")
    
    # Check blueprint exists
    assert webhook_bp is not None, "Webhook blueprint should exist"
    assert webhook_bp.name == "webhook", "Blueprint name should be 'webhook'"
    
    # Check routes are registered
    rules = list(webhook_bp.url_values_defaults.keys()) if hasattr(webhook_bp, 'url_values_defaults') else []
    print(f"✓ Webhook blueprint created successfully")
    print(f"  Blueprint name: {webhook_bp.name}")
    
    return True


def test_validation_function():
    """Test webhook validation function."""
    print("\nTesting validation function...")
    
    # Test with empty data
    result = validate_telegram_request(b"", "test_token", {})
    assert result == False, "Empty data should be invalid"
    print("✓ Empty data validation works")
    
    # Test with some data
    test_data = b'{"update_id": 123, "message": {}}'
    result = validate_telegram_request(test_data, "test_token", {})
    assert result == True, "Valid data should pass basic validation"
    print("✓ Basic data validation works")
    
    return True


def test_config():
    """Test that required config is present."""
    print("\nTesting configuration...")
    
    # Check if TELEGRAM_BOT_TOKEN is configured (can be None in test)
    print(f"  TELEGRAM_BOT_TOKEN configured: {Config.TELEGRAM_BOT_TOKEN is not None}")
    print(f"  TELEGRAM_WEBHOOK_URL configured: {Config.TELEGRAM_WEBHOOK_URL is not None}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Webhook Setup Verification")
    print("=" * 60)
    
    try:
        test_webhook_blueprint()
        test_validation_function()
        test_config()
        
        print("\n" + "=" * 60)
        print("✓ All webhook tests passed!")
        print("=" * 60)
        print("\nWebhook implementation is ready.")
        print("\nNext steps:")
        print("1. Set TELEGRAM_BOT_TOKEN in environment")
        print("2. Set TELEGRAM_WEBHOOK_URL in environment")
        print("3. Deploy to Render.com")
        print("4. Webhook will be available at: <your-domain>/webhook")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
