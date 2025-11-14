-- Migration: Create enhanced video job tables with detailed tracking
-- Date: 2025-11-14

-- Create enhanced video jobs table
CREATE TABLE IF NOT EXISTS ai_video_bot.video_jobs_enhanced (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    prompt TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    
    -- Script stage
    script_text TEXT,
    script_approved INTEGER DEFAULT 0,  -- 0=pending, 1=approved, -1=rejected
    script_generated_at TIMESTAMP,
    
    -- Audio stage
    audio_path VARCHAR(500),
    audio_duration FLOAT,
    audio_generated_at TIMESTAMP,
    
    -- Final video
    final_video_path VARCHAR(500),
    final_video_size_mb FLOAT,
    final_video_duration FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Indexes
    CONSTRAINT idx_enhanced_user_id CREATE INDEX ON (user_id),
    CONSTRAINT idx_enhanced_chat_id CREATE INDEX ON (chat_id),
    CONSTRAINT idx_enhanced_status CREATE INDEX ON (status)
);

-- Create enhanced video segments table
CREATE TABLE IF NOT EXISTS ai_video_bot.video_segments_enhanced (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES ai_video_bot.video_jobs_enhanced(id) ON DELETE CASCADE,
    segment_index INTEGER NOT NULL,
    
    -- Script segment
    text TEXT NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    
    -- Image prompt generation (via Segment Assistant)
    image_prompt TEXT,
    image_prompt_generated_at TIMESTAMP,
    
    -- Image generation (via Runway)
    image_path VARCHAR(500),
    image_runway_task_id VARCHAR(100),
    image_generated_at TIMESTAMP,
    
    -- Animation prompt generation (via Animation Assistant)
    animation_prompt TEXT,
    animation_prompt_generated_at TIMESTAMP,
    
    -- Video generation (via Runway)
    video_path VARCHAR(500),
    video_runway_task_id VARCHAR(100),
    video_duration FLOAT,
    video_generated_at TIMESTAMP,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT idx_enhanced_segment_job_id CREATE INDEX ON (job_id),
    CONSTRAINT idx_enhanced_segment_index CREATE INDEX ON (segment_index),
    CONSTRAINT idx_enhanced_segment_status CREATE INDEX ON (status)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_user_id ON ai_video_bot.video_jobs_enhanced(user_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_chat_id ON ai_video_bot.video_jobs_enhanced(chat_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_jobs_status ON ai_video_bot.video_jobs_enhanced(status);
CREATE INDEX IF NOT EXISTS idx_enhanced_segments_job_id ON ai_video_bot.video_segments_enhanced(job_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_segments_index ON ai_video_bot.video_segments_enhanced(segment_index);
CREATE INDEX IF NOT EXISTS idx_enhanced_segments_status ON ai_video_bot.video_segments_enhanced(status);

-- Add comments
COMMENT ON TABLE ai_video_bot.video_jobs_enhanced IS 'Enhanced video generation jobs with detailed step tracking';
COMMENT ON TABLE ai_video_bot.video_segments_enhanced IS 'Individual video segments with all generation stages';
COMMENT ON COLUMN ai_video_bot.video_jobs_enhanced.script_approved IS '0=pending, 1=approved, -1=rejected';
COMMENT ON COLUMN ai_video_bot.video_segments_enhanced.status IS 'pending, image_prompt_ready, image_ready, animation_prompt_ready, video_ready';
