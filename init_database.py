"""
Initialize database schema and tables.

This script:
1. Tests database connection
2. Creates schema if it doesn't exist
3. Creates all tables
4. Verifies setup
"""

import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.models.database import init_database, get_db_session, VideoJob, VideoSegment, Approval
from app.config import Config

def main():
    """Initialize database and verify setup."""
    
    print("🔧 Initializing AI Video Bot Database")
    print("=" * 60)
    
    # Check configuration
    if not Config.DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not configured in .env")
        sys.exit(1)
    
    print(f"📊 Database URL: {Config.DATABASE_URL[:50]}...")
    print(f"📁 Schema: {Config.DATABASE_SCHEMA}")
    print()
    
    try:
        # Initialize database
        print("🔌 Connecting to database...")
        engine = init_database()
        print("✅ Connected successfully!")
        print()
        
        # Test session
        print("🧪 Testing database session...")
        db = get_db_session()
        
        # Check tables
        print("📋 Checking tables...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        tables = inspector.get_table_names(schema=Config.DATABASE_SCHEMA)
        
        if tables:
            print(f"✅ Found {len(tables)} tables in schema '{Config.DATABASE_SCHEMA}':")
            for table in tables:
                print(f"   - {table}")
        else:
            print(f"⚠️  No tables found in schema '{Config.DATABASE_SCHEMA}'")
            print("   Tables will be created automatically on first use.")
        
        print()
        
        # Test query
        print("🔍 Testing query...")
        job_count = db.query(VideoJob).count()
        segment_count = db.query(VideoSegment).count()
        approval_count = db.query(Approval).count()
        
        print(f"✅ Query successful!")
        print(f"   - Video Jobs: {job_count}")
        print(f"   - Video Segments: {segment_count}")
        print(f"   - Approvals: {approval_count}")
        print()
        
        db.close()
        
        print("=" * 60)
        print("✅ Database initialization completed successfully!")
        print()
        print("📊 Database is ready for use:")
        print(f"   - Schema: {Config.DATABASE_SCHEMA}")
        print(f"   - Tables: video_jobs, video_segments, approvals")
        print(f"   - Segments per video: {Config.NUM_SEGMENTS}")
        print(f"   - Segment duration: {Config.SEGMENT_DURATION}s")
        print(f"   - Total video duration: {Config.TARGET_VIDEO_DURATION}s (4 minutes)")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR: Database initialization failed!")
        print(f"   Error: {str(e)}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Check DATABASE_URL in .env file")
        print("   2. Verify database credentials")
        print("   3. Ensure database server is accessible")
        print("   4. Check if schema name is valid")
        sys.exit(1)


if __name__ == "__main__":
    main()
