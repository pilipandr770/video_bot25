# Исправление проблемы с Redis на Render.com

## Проблема

Веб-сервис пытается подключиться к `localhost:6379` вместо Redis сервиса на Render. Ошибка:
```
ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

## Причина

Environment variable `REDIS_URL` не настроен правильно в веб-сервисе на Render.

## Решение

### Шаг 1: Проверить Redis сервис

1. Откройте https://dashboard.render.com
2. Найдите сервис **ai-video-redis**
3. Убедитесь, что статус: **Available** (зеленый)
4. Скопируйте **Internal Redis URL** (должен выглядеть как `redis://red-xxxxx:6379`)

### Шаг 2: Обновить Environment Variables для Web Service

1. Откройте **ai-video-bot-web** сервис
2. Перейдите в **Environment**
3. Найдите переменную `REDIS_URL`
4. Убедитесь, что она настроена как **"From Service"**:
   - Type: `redis`
   - Name: `ai-video-redis`
   - Property: `connectionString`

**ИЛИ** вручную установите значение Internal Redis URL:
```
redis://red-xxxxx:6379
```

### Шаг 3: Обновить Environment Variables для Worker Service

1. Откройте **ai-video-bot-worker** сервис
2. Перейдите в **Environment**
3. Найдите переменную `REDIS_URL`
4. Настройте так же, как для веб-сервиса

### Шаг 4: Перезапустить сервисы

После обновления environment variables:

1. Render автоматически перезапустит сервисы
2. Подождите, пока оба сервиса (web и worker) станут "Live"
3. Проверьте логи на наличие ошибок подключения к Redis

### Шаг 5: Проверить подключение

Отправьте тестовое сообщение боту и проверьте логи:

**Веб-сервис должен показать:**
```
Text message received: user_id=..., chat_id=..., prompt_length=...
Video generation task started: job_id=...
```

**Worker сервис должен показать:**
```
Task video_generation_task started
Connecting to Redis...
```

## Альтернативное решение: Обновить render.yaml

Если проблема сохраняется, убедитесь, что в `render.yaml` правильно настроена связь с Redis:

```yaml
services:
  - type: web
    name: ai-video-bot-web
    envVars:
      - key: REDIS_URL
        fromService:
          type: redis
          name: ai-video-redis
          property: connectionString
```

## Проверка через логи

### Правильные логи (Redis подключен):

```
2025-11-13T15:42:00.140388Z [info] incoming_request
Text message received: user_id=7444992311
Video generation task started: job_id=4650b79d-4a45-47de-9ae1-f4ecb73d9da2
```

### Неправильные логи (Redis не подключен):

```
Connection to Redis lost: Retry (0/20) now.
ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
Failed to start video generation task
```

## Дополнительная диагностика

Если проблема сохраняется, проверьте:

1. **Redis сервис запущен:**
   - Статус должен быть "Available"
   - Не должно быть ошибок в логах

2. **Network connectivity:**
   - Все сервисы должны быть в одном регионе (frankfurt)
   - Internal URLs должны быть доступны между сервисами

3. **Environment variables:**
   - Выполните команду в Shell веб-сервиса:
     ```bash
     echo $REDIS_URL
     ```
   - Должен показать Internal Redis URL, а не localhost

## Быстрое исправление через Render Dashboard

1. Dashboard → ai-video-bot-web → Environment
2. Удалите существующую переменную `REDIS_URL`
3. Добавьте новую:
   - Key: `REDIS_URL`
   - Sync from: `ai-video-redis` (Redis service)
   - Property: `connectionString`
4. Сохраните изменения
5. Дождитесь автоматического перезапуска

## Проверка после исправления

1. Откройте Telegram бота
2. Отправьте `/start`
3. Отправьте тестовое сообщение: "Создай рекламу для смартфона"
4. Проверьте логи веб-сервиса - не должно быть ошибок Redis
5. Проверьте логи worker - должна начаться обработка задачи

---

**Важно:** После исправления `REDIS_URL` все должно заработать. Это критическая переменная для работы Celery и асинхронной обработки задач.
