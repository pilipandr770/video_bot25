"""
Test video generation locally without Telegram webhook.
This script directly calls the Celery task to test the video generation pipeline.
"""
import os
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env
from app.tasks.video_generation import generate_video_task

def test_video_generation():
    """Test video generation with a simple prompt."""
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Test parameters
    user_id = 123456789  # Fake user ID for testing
    chat_id = 123456789  # Fake chat ID for testing
    prompt = "Создай короткое видео про кота, который играет с мячиком"
    
    print("🎬 Starting video generation test...")
    print(f"📝 Job ID: {job_id}")
    print(f"💬 Prompt: {prompt}")
    print("\n⚠️  Note: This will use real API calls (OpenAI, Runway)")
    print("⚠️  Notifications won't be sent (no real Telegram chat)")
    print("\n" + "="*60 + "\n")
    
    try:
        # Call the task directly (not via Celery)
        result = generate_video_task(
            job_id=job_id,
            user_id=user_id,
            chat_id=chat_id,
            prompt=prompt
        )
        
        print("\n" + "="*60)
        print("✅ Video generation completed!")
        print(f"📊 Result: {result}")
        
        if result.get('status') == 'completed':
            print(f"\n🎥 Final video: {result.get('final_video_path')}")
            print(f"⏱️  Total time: {result.get('metrics', {}).get('total_duration_minutes', 'N/A')} minutes")
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Check if API keys are set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set in .env")
        exit(1)
    
    if not os.getenv('RUNWAY_API_KEY'):
        print("❌ RUNWAY_API_KEY not set in .env")
        exit(1)
    
    print("✅ API keys found")
    print("✅ FFmpeg path:", os.getenv('FFMPEG_PATH'))
    print()
    
    # Ask for confirmation
    response = input("⚠️  This will make real API calls. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Test cancelled")
        exit(0)
    
    test_video_generation()
