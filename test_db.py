"""
Simple script to test database connection and schema.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.models.database import init_database, get_db_session, VideoJob, VideoSegment, Approval
from app.config import Config

def test_database():
    """Test database connection and table creation."""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    print()
    
    # Print configuration
    print(f"📊 Database URL: {Config.DATABASE_URL[:50]}...")
    print(f"📁 Schema: {Config.DATABASE_SCHEMA}")
    print()
    
    # Initialize database
    print("🔌 Initializing database...")
    try:
        init_database()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False
    
    print()
    
    # Test session creation
    print("🔌 Creating database session...")
    try:
        db = get_db_session()
        print("✅ Session created successfully!")
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        return False
    
    print()
    
    # Test creating a VideoJob
    print("📝 Testing VideoJob creation...")
    try:
        test_job = VideoJob(
            id="test-job-123",
            user_id=12345,
            chat_id=12345,
            prompt="Test prompt",
            status="pending"
        )
        db.add(test_job)
        db.commit()
        print("✅ VideoJob created successfully!")
        
        # Query it back
        queried_job = db.query(VideoJob).filter_by(id="test-job-123").first()
        if queried_job:
            print(f"✅ VideoJob queried successfully: {queried_job.id}")
        else:
            print("❌ Failed to query VideoJob")
        
        # Clean up
        db.delete(test_job)
        db.commit()
        print("✅ Test VideoJob deleted")
        
    except Exception as e:
        print(f"❌ Failed to create VideoJob: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    print()
    print("=" * 60)
    print("✅ All database tests passed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_database()
    exit(0 if success else 1)
