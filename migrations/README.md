# Database Migrations

This directory contains SQL migration scripts for the AI Video Generator Bot database.

## Overview

The application uses **PostgreSQL** for:
1. **Celery broker and backend** - Task queue management (replaces Redis)
2. **Approval system** - Storing user approval states for video generation stages (replaces Redis)

## Running Migrations

### Local Development

```bash
# Connect to your local PostgreSQL database
psql -U your_username -d your_database -f migrations/001_create_approval_statuses.sql
```

### Render.com Production

1. Go to your PostgreSQL database dashboard on Render.com
2. Click "Connect" and copy the External Database URL
3. Run migration using psql:

```bash
psql "postgresql://user:password@host/database" -f migrations/001_create_approval_statuses.sql
```

Or use the Render.com web console:
1. Go to your database dashboard
2. Click on "Shell" tab
3. Copy and paste the SQL from `001_create_approval_statuses.sql`
4. Execute

## Migration Files

### 001_create_approval_statuses.sql
Creates the following tables:
- `ai_video_bot.approval_statuses` - Stores approval states (approved/cancelled) for each job stage
- `ai_video_bot.celery_taskmeta` - Celery task metadata
- `ai_video_bot.celery_groupmeta` - Celery group metadata

## Schema

The application uses the `ai_video_bot` schema to organize all tables.

### approval_statuses Table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| job_id | VARCHAR(100) | Unique job identifier |
| approval_type | VARCHAR(50) | Type: 'script', 'images', or 'videos' |
| status | VARCHAR(20) | Status: 'approved' or 'cancelled' |
| created_at | TIMESTAMP | When the approval was created |
| expires_at | TIMESTAMP | When the approval expires (TTL) |

### Indexes

- `unique_job_approval` - Ensures one approval per job+type combination
- `idx_approval_job_type` - Fast lookups by job_id and approval_type
- `idx_approval_expires` - Efficient cleanup of expired approvals

## Automatic Cleanup

Expired approval records are automatically cleaned up by the `ApprovalManager._cleanup_expired()` method, which runs during approval operations.

## Environment Variables

Make sure your `.env` file has the correct DATABASE_URL:

```env
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_SCHEMA=ai_video_bot
```

## Troubleshooting

### Permission Errors

If you get permission errors, grant privileges:

```sql
GRANT ALL PRIVILEGES ON SCHEMA ai_video_bot TO your_db_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ai_video_bot TO your_db_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ai_video_bot TO your_db_user;
```

### Schema Not Found

If the schema doesn't exist:

```sql
CREATE SCHEMA IF NOT EXISTS ai_video_bot;
```

### Celery Connection Issues

If Celery can't connect to PostgreSQL, check:
1. DATABASE_URL is correct in environment variables
2. PostgreSQL is accessible from your application
3. Tables were created successfully
4. User has proper permissions
