"""Quick verification test for bot handlers"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing bot handlers import...")

try:
    from app.bot import handlers
    print("✅ handlers module imported successfully")
    
    # Check all required functions exist
    required_functions = [
        'handle_start',
        'handle_message',
        'handle_voice',
        'handle_callback_query'
    ]
    
    for func_name in required_functions:
        if hasattr(handlers, func_name):
            print(f"✅ {func_name} function exists")
        else:
            print(f"❌ {func_name} function NOT FOUND")
            sys.exit(1)
    
    # Check helper functions
    helper_functions = [
        '_parse_callback_data',
        '_get_approval_type',
        '_handle_approval',
        '_handle_cancellation'
    ]
    
    for func_name in helper_functions:
        if hasattr(handlers, func_name):
            print(f"✅ {func_name} helper function exists")
        else:
            print(f"❌ {func_name} helper function NOT FOUND")
            sys.exit(1)
    
    # Test callback data parsing
    print("\nTesting callback data parsing...")
    
    test_cases = [
        ("approve_script:test-job-123", ("approve_script", "test-job-123")),
        ("cancel_images:another-job-456", ("cancel_images", "another-job-456")),
        ("approve_videos:video-job-789", ("approve_videos", "video-job-789")),
    ]
    
    for callback_data, expected in test_cases:
        try:
            result = handlers._parse_callback_data(callback_data)
            if result == expected:
                print(f"✅ Parsed '{callback_data}' correctly: {result}")
            else:
                print(f"❌ Parse mismatch for '{callback_data}': got {result}, expected {expected}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to parse '{callback_data}': {e}")
            sys.exit(1)
    
    # Test invalid callback data
    print("\nTesting invalid callback data...")
    try:
        handlers._parse_callback_data("invalid_format")
        print("❌ Should have raised ValueError for invalid format")
        sys.exit(1)
    except ValueError:
        print("✅ Correctly raised ValueError for invalid format")
    
    # Test approval type extraction
    print("\nTesting approval type extraction...")
    
    approval_tests = [
        ("approve_script", "script"),
        ("cancel_script", "script"),
        ("approve_images", "images"),
        ("cancel_images", "images"),
        ("approve_videos", "videos"),
        ("cancel_videos", "videos"),
        ("unknown_action", None),
    ]
    
    for action, expected_type in approval_tests:
        result = handlers._get_approval_type(action)
        if result == expected_type:
            print(f"✅ Extracted type '{expected_type}' from '{action}'")
        else:
            print(f"❌ Type mismatch for '{action}': got {result}, expected {expected_type}")
            sys.exit(1)
    
    print("\n✅ All handler tests passed!")
    
except ImportError as e:
    print(f"❌ Failed to import handlers: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
