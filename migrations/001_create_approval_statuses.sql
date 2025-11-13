-- Migration: Create approval_statuses table for PostgreSQL
-- This replaces Redis for storing approval states

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS ai_video_bot;

-- Create approval_statuses table
CREATE TABLE IF NOT EXISTS ai_video_bot.approval_statuses (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    approval_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('approved', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    -- Index for fast lookups
    CONSTRAINT unique_job_approval UNIQUE (job_id, approval_type)
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_approval_job_type 
ON ai_video_bot.approval_statuses(job_id, approval_type);

CREATE INDEX IF NOT EXISTS idx_approval_expires 
ON ai_video_bot.approval_statuses(expires_at);

-- Create Celery tables for task queue (if not exists)
CREATE TABLE IF NOT EXISTS ai_video_bot.celery_taskmeta (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(155) UNIQUE NOT NULL,
    status VARCHAR(50),
    result BYTEA,
    date_done TIMESTAMP,
    traceback TEXT,
    name VARCHAR(155),
    args BYTEA,
    kwargs BYTEA,
    worker VARCHAR(155),
    retries INTEGER,
    queue VARCHAR(155)
);

CREATE TABLE IF NOT EXISTS ai_video_bot.celery_groupmeta (
    id SERIAL PRIMARY KEY,
    taskset_id VARCHAR(155) UNIQUE NOT NULL,
    result BYTEA,
    date_done TIMESTAMP
);

-- Create indexes for Celery tables
CREATE INDEX IF NOT EXISTS idx_celery_task_id 
ON ai_video_bot.celery_taskmeta(task_id);

CREATE INDEX IF NOT EXISTS idx_celery_taskset_id 
ON ai_video_bot.celery_groupmeta(taskset_id);

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON SCHEMA ai_video_bot TO your_db_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ai_video_bot TO your_db_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ai_video_bot TO your_db_user;

COMMENT ON TABLE ai_video_bot.approval_statuses IS 'Stores user approval states for video generation stages (replaces Redis)';
COMMENT ON TABLE ai_video_bot.celery_taskmeta IS 'Celery task metadata (replaces Redis as Celery backend)';
COMMENT ON TABLE ai_video_bot.celery_groupmeta IS 'Celery group metadata (replaces Redis as Celery backend)';
