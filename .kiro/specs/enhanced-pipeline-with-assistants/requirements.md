# Requirements Document

## Introduction

Улучшенный пайплайн генерации видео с использованием трёх специализированных OpenAI ассистентов и детальным отслеживанием каждого этапа в базе данных. Система обеспечивает последовательную генерацию контента с утверждением на каждом этапе и полной прозрачностью процесса через постоянные кнопки управления в боте.

## Glossary

- **Script Assistant**: OpenAI ассистент для генерации сценария видео (50 секунд, 10 сегментов)
- **Segment Assistant**: OpenAI ассистент для генерации промптов изображений из текста сегмента
- **Animation Assistant**: OpenAI ассистент для генерации промптов анимации изображений
- **Job Table**: Таблица в PostgreSQL с детальным состоянием каждого этапа генерации
- **Segment Cell**: Ячейка в таблице для хранения данных одного сегмента (текст, промпты, пути к файлам)
- **Persistent Buttons**: Постоянные кнопки управления в Telegram боте (Старт, Статус, Подтвердить, Отклонить)
- **Sequential Generation**: Последовательная генерация контента (один за другим, без параллелизма)

## Requirements

### Requirement 1: Использование трёх специализированных OpenAI ассистентов

**User Story:** Как пользователь, я хочу получать высококачественный контент, сгенерированный специализированными AI ассистентами, чтобы каждый этап (сценарий, изображения, анимация) был оптимизирован под свою задачу.

#### Acceptance Criteria

1. WHEN THE System generates script, THE System SHALL use Script Assistant (OPENAI_SCRIPT_ASSISTANT_ID) to create 50-second scenario with 10 segments
2. WHEN THE System generates image prompts, THE System SHALL use Segment Assistant (OPENAI_SEGMENT_ASSISTANT_ID) to create detailed English prompts for each of 10 segments
3. WHEN THE System generates animation prompts, THE System SHALL use Animation Assistant (OPENAI_ANIMATION_ASSISTANT_ID) to create motion descriptions for each of 10 segments
4. WHEN THE System calls OpenAI Assistant, THE System SHALL wait for completion before proceeding to next step
5. WHEN THE System receives assistant response, THE System SHALL validate response format and content before saving to database

### Requirement 2: Детальная таблица состояния в PostgreSQL

**User Story:** Как разработчик, я хочу иметь детальную таблицу в базе данных, которая хранит состояние каждого этапа генерации, чтобы можно было отслеживать прогресс и восстанавливать процесс после сбоев.

#### Acceptance Criteria

1. THE System SHALL create table `video_jobs_detailed` with columns: job_id, user_id, chat_id, prompt, status, created_at, updated_at
2. THE System SHALL create table `video_segments` with columns: id, job_id, segment_index (0-9), segment_text, image_prompt, animation_prompt, image_path, video_path, status, created_at, updated_at
3. THE System SHALL create table `job_artifacts` with columns: id, job_id, artifact_type (script, audio, final_video), artifact_path, status, created_at
4. WHEN THE System starts new job, THE System SHALL create record in video_jobs_detailed with status 'generating_script'
5. WHEN THE System generates segment data, THE System SHALL create or update record in video_segments table
6. WHEN THE System completes artifact generation, THE System SHALL create record in job_artifacts table
7. WHEN THE User rejects job, THE System SHALL delete all records for job_id from all tables
8. WHEN THE System queries job status, THE System SHALL join video_jobs_detailed, video_segments, and job_artifacts to show complete picture

### Requirement 3: Последовательная генерация контента

**User Story:** Как пользователь, я хочу, чтобы контент генерировался последовательно и предсказуемо, чтобы я мог отслеживать прогресс и понимать, на каком этапе находится генерация.

#### Acceptance Criteria

1. THE System SHALL generate script first and wait for user approval before generating image prompts
2. WHEN THE User approves script, THE System SHALL generate 10 image prompts sequentially using Segment Assistant
3. WHEN THE System completes all image prompts, THE System SHALL save them to database and generate 10 images sequentially using Runway API
4. WHEN THE System completes all images, THE System SHALL send preview (first 5 images) for user approval
5. WHEN THE User approves images, THE System SHALL generate 10 animation prompts sequentially using Animation Assistant
6. WHEN THE System completes all animation prompts, THE System SHALL save them to database and animate 10 videos sequentially using Runway API
7. WHEN THE System completes all videos, THE System SHALL send preview (first 3 videos) for user approval
8. WHEN THE User approves videos, THE System SHALL generate audio and assemble final video
9. THE System SHALL NOT start next stage until previous stage is completed and approved

### Requirement 4: Постоянные кнопки управления в боте

**User Story:** Как пользователь, я хочу иметь постоянные кнопки управления в боте, чтобы я мог в любой момент проверить статус, подтвердить или отклонить текущий этап.

#### Acceptance Criteria

1. THE System SHALL display persistent keyboard with buttons: "🚀 Старт", "📊 Статус", "✅ Подтвердить", "❌ Отклонить"
2. WHEN THE User clicks "🚀 Старт", THE System SHALL show welcome message and instructions
3. WHEN THE User clicks "📊 Статус", THE System SHALL query database and show current job status with progress details
4. WHEN THE User clicks "✅ Подтвердить", THE System SHALL approve current stage and proceed to next stage
5. WHEN THE User clicks "❌ Отклонить", THE System SHALL cancel job, delete all database records, and cleanup all files
6. WHEN THE User has no active job, THE System SHALL show message "Нет активных заданий" for Статус/Подтвердить/Отклонить buttons
7. THE System SHALL show persistent keyboard in all bot messages

### Requirement 5: Расширенный workflow с новыми этапами

**User Story:** Как пользователь, я хочу видеть детальный прогресс генерации на каждом этапе, чтобы понимать, что происходит и сколько времени это займёт.

#### Acceptance Criteria

1. THE System SHALL implement stage "generating_script" with status updates
2. THE System SHALL implement stage "awaiting_script_approval" with script preview
3. THE System SHALL implement stage "generating_image_prompts" with progress counter (1/10, 2/10, etc.)
4. THE System SHALL implement stage "generating_images" with progress counter (1/10, 2/10, etc.)
5. THE System SHALL implement stage "awaiting_images_approval" with image prev