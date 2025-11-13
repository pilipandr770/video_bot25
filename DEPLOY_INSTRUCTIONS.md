# Инструкции по развертыванию (без Redis)

## Критическая проблема решена! ✅

**Проблема:** Бот не мог подключиться к Redis на Render.com  
**Решение:** Полностью убрали Redis, теперь используем только PostgreSQL

## Быстрый старт

### 1. Запустить миграцию базы данных на Render.com

Перейдите в ваш PostgreSQL dashboard на Render.com:
https://dashboard.render.com/d/dpg-d0visga4d50c73ekmu4g

Откройте вкладку **"Shell"** и выполните:

```sql
-- Создать схему
CREATE SCHEMA IF NOT EXISTS ai_video_bot;

-- Создать таблицу для approvals
CREATE TABLE IF NOT EXISTS ai_video_bot.approval_statuses (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL,
    approval_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('approved', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    CONSTRAINT unique_job_approval UNIQUE (job_id, approval_type)
);

-- Создать индексы
CREATE INDEX IF NOT EXISTS idx_approval_job_type 
ON ai_video_bot.approval_statuses(job_id, approval_type);

CREATE INDEX IF NOT EXISTS idx_approval_expires 
ON ai_video_bot.approval_statuses(expires_at);

-- Создать таблицы для Celery
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

-- Создать индексы для Celery
CREATE INDEX IF NOT EXISTS idx_celery_task_id 
ON ai_video_bot.celery_taskmeta(task_id);

CREATE INDEX IF NOT EXISTS idx_celery_taskset_id 
ON ai_video_bot.celery_groupmeta(taskset_id);
```

### 2. Закоммитить и запушить изменения

```bash
git add .
git commit -m "Fix: Replace Redis with PostgreSQL for Celery and approvals"
git push origin main
```

### 3. Render.com автоматически:

1. ✅ Пересоберет Docker образ
2. ✅ Перезапустит web и worker сервисы  
3. ✅ Подключит их к PostgreSQL (DATABASE_URL уже настроен в .env)

### 4. Проверить логи

Откройте логи на Render.com:
- Web service: https://dashboard.render.com/web/srv-...
- Worker service: https://dashboard.render.com/web/srv-...

Должны увидеть:
```
Celery app initialized with PostgreSQL broker
ApprovalManager initialized with PostgreSQL
```

**Не должно быть:**
```
Error -2 connecting to red-ctabcdefghij1234567:6379
```

### 5. Протестировать бота

1. Отправьте `/start` боту
2. Отправьте текстовое сообщение с описанием ролика
3. Проверьте, что задача запускается без ошибок Redis

## Что изменилось

### Удалено:
- ❌ Redis сервис
- ❌ Зависимость `redis==5.0.1`
- ❌ REDIS_URL из конфигурации

### Добавлено:
- ✅ PostgreSQL для Celery broker/backend
- ✅ PostgreSQL для approval system
- ✅ Таблицы: `approval_statuses`, `celery_taskmeta`, `celery_groupmeta`
- ✅ Миграции в папке `migrations/`

## Преимущества

1. **Проще** - один сервис вместо двух
2. **Дешевле** - не платим за Redis
3. **Надежнее** - PostgreSQL более стабилен
4. **Работает!** - нет проблем с подключением

## Если что-то не работает

### Проверить подключение к PostgreSQL:

```bash
# Из логов Render.com скопируйте DATABASE_URL
psql "postgresql://user:password@host/database"

# Проверить таблицы
\dt ai_video_bot.*
```

### Проверить Celery:

Из логов worker сервиса должно быть:
```
[INFO] Celery app initialized with PostgreSQL broker
```

### Проверить ApprovalService:

Из логов web сервиса должно быть:
```
[INFO] ApprovalManager initialized with PostgreSQL
```

## Следующие шаги

После успешного развертывания:

1. ✅ Протестировать полный flow генерации видео
2. ✅ Проверить систему утверждений (approve/cancel)
3. ✅ Убедиться, что временные файлы очищаются
4. ✅ Мониторить размер базы данных

## Контакты

Если возникнут проблемы:
1. Проверьте логи на Render.com
2. Проверьте, что миграция выполнена
3. Проверьте переменные окружения (DATABASE_URL, DATABASE_SCHEMA)

Удачи! 🚀
