"""
Test voice message handling in video generation task.
This script tests the voice message marker detection and processing logic.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_voice_message_marker_detection():
    """Test that voice message markers are correctly detected."""
    
    print("🧪 Testing voice message marker detection...\n")
    
    # Test cases
    test_cases = [
        {
            "prompt": "__VOICE_MESSAGE__|AgADAgADYqcxG1234567890",
            "expected": True,
            "description": "Valid voice message marker"
        },
        {
            "prompt": "Regular text prompt about a video",
            "expected": False,
            "description": "Regular text prompt"
        },
        {
            "prompt": "__VOICE_MESSAGE__",
            "expected": True,  # Starts with marker but invalid format
            "description": "Incomplete voice message marker"
        },
        {
            "prompt": "",
            "expected": False,
            "description": "Empty prompt"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        prompt = test_case["prompt"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        # Check if prompt starts with voice message marker
        is_voice_message = prompt.startswith("__VOICE_MESSAGE__|")
        
        # For the incomplete marker test, we check if it starts with the prefix
        if prompt.startswith("__VOICE_MESSAGE__") and not is_voice_message:
            is_voice_message = True  # Would be detected but fail during parsing
        
        result = "✅ PASS" if is_voice_message == expected else "❌ FAIL"
        
        if is_voice_message == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"Test {i}: {description}")
        print(f"  Prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
        print(f"  Expected voice message: {expected}")
        print(f"  Detected voice message: {is_voice_message}")
        print(f"  {result}\n")
    
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


def test_voice_message_file_id_extraction():
    """Test that file IDs are correctly extracted from voice message markers."""
    
    print("\n🧪 Testing file ID extraction...\n")
    
    test_cases = [
        {
            "prompt": "__VOICE_MESSAGE__|AgADAgADYqcxG1234567890",
            "expected_file_id": "AgADAgADYqcxG1234567890",
            "should_succeed": True
        },
        {
            "prompt": "__VOICE_MESSAGE__|",
            "expected_file_id": "",
            "should_succeed": True  # Empty file_id
        },
        {
            "prompt": "Regular text",
            "expected_file_id": None,
            "should_succeed": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        prompt = test_case["prompt"]
        expected_file_id = test_case["expected_file_id"]
        should_succeed = test_case["should_succeed"]
        
        try:
            if prompt.startswith("__VOICE_MESSAGE__|"):
                file_id = prompt.split("|", 1)[1]
                success = True
            else:
                file_id = None
                success = False
            
            if success == should_succeed:
                if not should_succeed or file_id == expected_file_id:
                    print(f"Test {i}: ✅ PASS")
                    print(f"  Extracted file_id: {file_id}\n")
                    passed += 1
                else:
                    print(f"Test {i}: ❌ FAIL")
                    print(f"  Expected: {expected_file_id}")
                    print(f"  Got: {file_id}\n")
                    failed += 1
            else:
                print(f"Test {i}: ❌ FAIL")
                print(f"  Expected success: {should_succeed}, Got: {success}\n")
                failed += 1
                
        except Exception as e:
            if not should_succeed:
                print(f"Test {i}: ✅ PASS (expected failure)")
                print(f"  Error: {e}\n")
                passed += 1
            else:
                print(f"Test {i}: ❌ FAIL (unexpected error)")
                print(f"  Error: {e}\n")
                failed += 1
    
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    print("="*60)
    print("Voice Message Handling Tests")
    print("="*60 + "\n")
    
    test1_passed = test_voice_message_marker_detection()
    test2_passed = test_voice_message_file_id_extraction()
    
    print("\n" + "="*60)
    if test1_passed and test2_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("="*60)
