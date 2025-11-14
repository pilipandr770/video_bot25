"""
Apply enhanced database migration.
Creates new tables for detailed video generation tracking.
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.config import Config


def apply_migration():
    """Apply the enhanced tables migration."""
    
    print("🔧 Applying enhanced database migration...")
    print(f"📊 Database: {Config.DATABASE_URL}")
    print(f"📁 Schema: {Config.DATABASE_SCHEMA}")
    
    # Create engine
    engine = create_engine(Config.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Read migration file
            migration_path = os.path.join(
                os.path.dirname(__file__),
                'migrations',
                'create_enhanced_tables.sql'
            )
            
            with open(migration_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            print("\n📝 Executing migration SQL...")
            
            # Execute migration
            conn.execute(text(migration_sql))
            conn.commit()
            
            print("✅ Migration applied successfully!")
            
            # Verify tables exist
            print("\n🔍 Verifying tables...")
            
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema 
                AND table_name IN ('video_jobs_enhanced', 'video_segments_enhanced')
                ORDER BY table_name
            """), {"schema": Config.DATABASE_SCHEMA})
            
            tables = [row[0] for row in result]
            
            if len(tables) == 2:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   • {table}")
            else:
                print(f"⚠️  Warning: Expected 2 tables, found {len(tables)}")
            
            print("\n✅ Migration completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    apply_migration()
