# 🗄️ Дизайн базы данных для AI Video Generator

## Концепция

4-минутное видео = 48 сегментов по 5 секунд

### Структура видео:
1. **Вступление** (0-11): 12 сегментов × 5 сек = 60 сек (1 минута) - введение в тему
2. **Основная часть** (12-35): 24 сегмента × 5 сек = 120 сек (2 минуты) - основной контент
3. **Заключение** (36-47): 12 сегментов × 5 сек = 60 сек (1 минута) - выводы и призыв к действию

## Таблицы базы данных

### 1. `video_jobs` - Основная таблица заданий
```sql
CREATE TABLE video_jobs (
    id TEXT PRIMARY KEY,              -- UUID задания
    user_id INTEGER NOT NULL,         -- Telegram user ID
    chat_id INTEGER NOT NULL,         -- Telegram chat ID
    prompt TEXT NOT NULL,             -- Исходный промпт пользователя
    status TEXT NOT NULL,             -- pending, script_generated, approved, generating, completed, failed
    script TEXT,                      -- Полный сценарий от OpenAI
    script_intro TEXT,                -- Сценарий вступления
    script_main TEXT,                 -- Сценарий основной части
    script_outro TEXT,                -- Сценарий заключения
    audio_intro_path TEXT,            -- Путь к аудио вступления
    audio_main_path TEXT,             -- Путь к аудио основной части
    audio_outro_path TEXT,            -- Путь к аудио заключения
    final_video_path TEXT,            -- Путь к финальному видео
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 2. `video_segments` - Сегменты видео
```sql
CREATE TABLE video_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,             -- Ссылка на video_jobs.id
    segment_index INTEGER NOT NULL,   -- 0-47 (порядковый номер)
    section TEXT NOT NULL,            -- intro (0-11), main (12-35), outro (36-47)
    text_prompt TEXT,                 -- Текст для этого сегмента
    image_prompt TEXT,                -- Промпт для генерации изображения
    image_path TEXT,                  -- Путь к сгенерированному изображению
    image_status TEXT,                -- pending, generating, completed, failed
    video_path TEXT,                  -- Путь к анимированному видео
    video_status TEXT,                -- pending, generating, completed, failed
    duration REAL DEFAULT 5.0,        -- Длительность сегмента (5 секунд)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES video_jobs(id) ON DELETE CASCADE,
    UNIQUE(job_id, segment_index)
);
```

### 3. `approvals` - Утверждения пользователя
```sql
CREATE TABLE approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    approval_type TEXT NOT NULL,      -- script, images, videos
    status TEXT NOT NULL,             -- pending, approved, rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES video_jobs(id) ON DELETE CASCADE
);
```

## Workflow (Рабочий процесс)

### Этап 1: Генерация сценария
```python
1. Пользователь отправляет промпт
2. Создается запись в video_jobs (status='pending')
3. OpenAI Assistant генерирует полный сценарий
4. Сценарий делится на 3 части:
   - script_intro (1 минута)
   - script_main (2 минуты)
   - script_outro (1 минута)
5. Обновляется video_jobs (status='script_generated')
6. Отправляется пользователю на утверждение
7. Создается запись в approvals (type='script', status='pending')
```

### Этап 2: Деление на сегменты
```python
После утверждения сценария:
1. Обновляется approvals (status='approved')
2. Обновляется video_jobs (status='approved')
3. Создается 48 записей в video_segments:
   - 0-11: section='intro', text из script_intro (12 сегментов)
   - 12-35: section='main', text из script_main (24 сегмента)
   - 36-47: section='outro', text из script_outro (12 сегментов)
4. Для каждого сегмента генерируется image_prompt
```

### Этап 3: Генерация изображений
```python
Для каждого сегмента (0-47):
1. Обновляется video_segments (image_status='generating')
2. Runway API генерирует изображение по image_prompt
3. Сохраняется в image_path
4. Обновляется video_segments (image_status='completed')

Прогресс: "Генерация изображений: 24/48 (50%)"
```

### Этап 4: Утверждение изображений
```python
1. Отправляются первые 5 изображений на превью
2. Создается запись в approvals (type='images', status='pending')
3. Ожидание утверждения пользователя
4. После утверждения: approvals (status='approved')
```

### Этап 5: Анимация видео
```python
Для каждого сегмента (0-47):
1. Обновляется video_segments (video_status='generating')
2. Runway API анимирует изображение
3. Сохраняется в video_path
4. Обновляется video_segments (video_status='completed')

Прогресс: "Анимация видео: 24/48 (50%)"
```

### Этап 6: Утверждение видео
```python
1. Отправляются первые 3 видео на превью
2. Создается запись в approvals (type='videos', status='pending')
3. Ожидание утверждения пользователя
4. После утверждения: approvals (status='approved')
```

### Этап 7: Генерация аудио
```python
1. OpenAI TTS генерирует 3 аудио файла:
   - audio_intro_path (из script_intro)
   - audio_main_path (из script_main)
   - audio_outro_path (из script_outro)
2. Обновляется video_jobs с путями к аудио
```

### Этап 8: Сборка финального видео
```python
1. FFmpeg объединяет все 48 видео сегментов
2. FFmpeg добавляет переходы между секциями (fade между intro/main/outro)
3. FFmpeg объединяет 3 аудио файла
4. FFmpeg накладывает аудио на видео
5. Сохраняется в final_video_path
6. Обновляется video_jobs (status='completed')
7. Отправляется пользователю
```

## Преимущества этого подхода

✅ **Четкая структура** - каждый сегмент имеет свое место
✅ **Отслеживание прогресса** - видно, какие сегменты готовы
✅ **Возобновление** - можно продолжить с любого этапа при сбое
✅ **Параллелизм** - можно генерировать несколько сегментов одновременно
✅ **Утверждения** - пользователь контролирует процесс
✅ **История** - все данные сохраняются для анализа

## Пример запросов

### Получить прогресс задания
```python
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN image_status='completed' THEN 1 ELSE 0 END) as images_done,
    SUM(CASE WHEN video_status='completed' THEN 1 ELSE 0 END) as videos_done
FROM video_segments
WHERE job_id = ?
```

### Получить следующий сегмент для обработки
```python
SELECT * FROM video_segments
WHERE job_id = ? AND image_status = 'pending'
ORDER BY segment_index
LIMIT 1
```

### Получить все готовые видео для сборки
```python
SELECT video_path FROM video_segments
WHERE job_id = ? AND video_status = 'completed'
ORDER BY segment_index
```

## Следующие шаги

1. Создать SQLite базу данных
2. Реализовать модели данных (SQLAlchemy или простой SQL)
3. Обновить Celery tasks для работы с БД
4. Добавить функции прогресса и возобновления
5. Протестировать весь workflow
