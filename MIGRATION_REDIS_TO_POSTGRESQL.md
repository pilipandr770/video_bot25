# Миграция с Redis на PostgreSQL

## Обзор изменений

Мы полностью убрали зависимость от Redis и теперь используем **только PostgreSQL** для:

1. **Celery broker и backend** - очередь задач
2. **Approval system** - хранение статусов утверждений

### Преимущества

✅ **Упрощение инфраструктуры** - один сервис вместо двух  
✅ **Снижение затрат** - не нужно платить за Redis на Render.com  
✅ **Надежность** - PostgreSQL более надежен для хранения критичных данных  
✅ **Консистентность** - все данные в одной базе  

## Что изменилось

### 1. Удалены зависимости

**requirements.txt:**
- ❌ Удалено: `redis==5.0.1`
- ✅ Добавлено: `celery[sqlalchemy]==5.3.4`

### 2. Обновлена конфигурация Celery

**app/tasks/__init__.py:**
```python
# Было (Redis):
celery_app = Celery(
    'ai_video_generator',
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL,
)

# Стало (PostgreSQL):
celery_app = Celery(
    'ai_video_generator',
    broker=f'sqla+{Config.DATABASE_URL}',
    backend=f'db+{Config.DATABASE_URL}',
)
```

### 3. Переписан ApprovalService

**app/services/approval_service.py:**
- Теперь использует SQLAlchemy вместо Redis
- Создана модель `ApprovalStatus` для хранения в PostgreSQL
- Автоматическая очистка истекших записей

### 4. Обновлен render.yaml

- ❌ Удален сервис `ai-video-redis`
- ✅ Добавлен сервис `ai-video-postgres`
- Обновлены environment variables (DATABASE_URL вместо REDIS_URL)

### 5. Обновлен .env

```env
# Было:
REDIS_URL=redis://localhost:6379/0

# Стало:
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_SCHEMA=ai_video_bot
```

## Инструкции по развертыванию

### Шаг 1: Обновить зависимости

```bash
pip install -r requirements.txt
```

### Шаг 2: Запустить миграцию базы данных

#### Локально:

```bash
psql -U your_username -d your_database -f migrations/001_create_approval_statuses.sql
```

#### На Render.com:

1. Перейдите в Dashboard PostgreSQL на Render.com
2. Откройте вкладку "Shell"
3. Скопируйте и выполните SQL из `migrations/001_create_approval_statuses.sql`

Или через psql:

```bash
# Используйте External Database URL из Render.com
psql "postgresql://user:password@host/database" -f migrations/001_create_approval_statuses.sql
```

### Шаг 3: Обновить переменные окружения

#### Локально (.env):

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_video_bot
DATABASE_SCHEMA=ai_video_bot
```

#### На Render.com:

1. Перейдите в настройки каждого сервиса (web и worker)
2. Удалите переменную `REDIS_URL`
3. Добавьте переменные:
   - `DATABASE_URL` - выберите "From Database" → `ai-video-postgres`
   - `DATABASE_SCHEMA` - значение: `ai_video_bot`

### Шаг 4: Развернуть обновления

```bash
git add .
git commit -m "Migrate from Redis to PostgreSQL"
git push origin main
```

Render.com автоматически:
1. Создаст PostgreSQL сервис
2. Пересоберет и перезапустит web и worker сервисы
3. Подключит их к новой базе данных

### Шаг 5: Проверить работу

1. Откройте логи web сервиса на Render.com
2. Убедитесь, что нет ошибок подключения к базе данных
3. Отправьте тестовое сообщение боту
4. Проверьте, что задача создается и выполняется

## Проверка миграции

### Проверить таблицы в PostgreSQL:

```sql
-- Подключиться к базе
\c ai_video_bot

-- Проверить схему
\dn

-- Проверить таблицы
\dt ai_video_bot.*

-- Должны быть:
-- ai_video_bot.approval_statuses
-- ai_video_bot.celery_taskmeta
-- ai_video_bot.celery_groupmeta
```

### Проверить Celery:

```bash
# Локально
celery -A app.tasks inspect active

# Должно показать активные задачи без ошибок подключения
```

### Проверить ApprovalService:

```python
from app.services.approval_service import ApprovalManager

# Создать тестовое утверждение
manager = ApprovalManager()
manager.approve("test-job-123", "script")

# Проверить статус
status = manager.is_approved("test-job-123", "script")
print(f"Status: {status}")  # Должно быть True
```

## Откат (если нужно)

Если что-то пошло не так, можно откатиться:

1. Восстановить старую версию кода:
```bash
git revert HEAD
git push origin main
```

2. Вернуть Redis сервис в render.yaml
3. Восстановить REDIS_URL в environment variables

## Troubleshooting

### Ошибка: "relation does not exist"

**Проблема:** Таблицы не созданы в базе данных

**Решение:**
```bash
psql "your_database_url" -f migrations/001_create_approval_statuses.sql
```

### Ошибка: "permission denied for schema"

**Проблема:** У пользователя нет прав на схему

**Решение:**
```sql
GRANT ALL PRIVILEGES ON SCHEMA ai_video_bot TO your_db_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ai_video_bot TO your_db_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ai_video_bot TO your_db_user;
```

### Celery не подключается к PostgreSQL

**Проблема:** Неправильный формат DATABASE_URL

**Решение:** Убедитесь, что URL начинается с `postgresql://` (не `postgres://`)

```python
# Если нужно, добавьте в Config:
DATABASE_URL = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://", 1)
```

### Approval не работает

**Проблема:** Таблица approval_statuses не создана

**Решение:**
1. Проверьте, что миграция выполнена
2. Проверьте, что схема `ai_video_bot` существует
3. Проверьте логи ApprovalManager

## Мониторинг

### Проверить размер таблиц:

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'ai_video_bot'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Очистить старые записи:

```sql
-- Удалить истекшие approvals
DELETE FROM ai_video_bot.approval_statuses 
WHERE expires_at < NOW();

-- Удалить старые Celery задачи (старше 24 часов)
DELETE FROM ai_video_bot.celery_taskmeta 
WHERE date_done < NOW() - INTERVAL '24 hours';
```

## Заключение

После миграции:
- ✅ Redis больше не нужен
- ✅ Все работает на PostgreSQL
- ✅ Инфраструктура упрощена
- ✅ Затраты снижены

Если возникнут вопросы, проверьте логи на Render.com или обратитесь к документации PostgreSQL и Celery.
