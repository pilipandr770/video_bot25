# Запуск проекта в Docker

## Статус
✅ Проект успешно запущен в Docker контейнерах

## Что было сделано

1. **Обновлен Dockerfile**
   - Добавлена установка FFmpeg из системных пакетов Debian
   - Убрана зависимость от локальных FFmpeg бинарников
   - Добавлен curl для health checks

2. **Обновлен docker-compose.yml**
   - Убрано устаревшее поле `version`
   - Обновлены пути к FFmpeg (используется системный FFmpeg)
   - Убраны volume маппинги для FFmpeg бинарников

3. **Установлены зависимости Python**
   - Все пакеты из requirements.txt установлены локально

## Запущенные сервисы

### Redis (ai-video-bot-redis)
- Порт: 6379
- Статус: ✅ Healthy
- Используется как брокер для Celery и хранилище для rate limiting

### Web Application (ai-video-bot-web)
- Порт: 5000
- Статус: ✅ Healthy
- Flask приложение с Gunicorn
- 2 worker процесса
- Endpoints:
  - `http://localhost:5000/` - главная страница
  - `http://localhost:5000/health` - health check
  - `http://localhost:5000/webhook` - Telegram webhook

### Celery Worker (ai-video-bot-worker)
- Статус: ✅ Running
- Concurrency: 2
- Задачи:
  - `app.tasks.generate_video` - генерация видео
  - `app.tasks.cleanup_old_files` - очистка временных файлов

## Команды для управления

### Запуск контейнеров
```bash
docker-compose up -d
```

### Остановка контейнеров
```bash
docker-compose down
```

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f redis
```

### Проверка статуса
```bash
docker-compose ps
```

### Пересборка контейнеров
```bash
docker-compose build
docker-compose up -d
```

### Перезапуск сервиса
```bash
docker-compose restart web
docker-compose restart worker
```

## Тестирование

### Health Check
```bash
curl http://localhost:5000/health
```

Ожидаемый ответ:
```json
{"service":"ai-video-generator-bot","status":"healthy"}
```

### Проверка Redis
```bash
docker exec ai-video-bot-redis redis-cli ping
```

Ожидаемый ответ: `PONG`

## Переменные окружения

Все переменные загружаются из файла `.env`:
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `TELEGRAM_WEBHOOK_URL` - URL для webhook (для локального теста: http://localhost:5000)
- `OPENAI_API_KEY` - ключ OpenAI API
- `OPENAI_ASSISTANT_ID` - ID OpenAI Assistant
- `RUNWAY_API_KEY` - ключ Runway API
- `REDIS_URL` - URL Redis (в контейнерах: redis://redis:6379/0)
- `LOG_LEVEL` - уровень логирования (DEBUG/INFO/WARNING/ERROR)

## Следующие шаги

1. **Настройка webhook для Telegram**
   - Для локального тестирования нужен публичный URL (ngrok, localtunnel)
   - Или деплой на Render.com/Heroku

2. **Тестирование функционала**
   - Отправка сообщений боту
   - Генерация видео
   - Проверка rate limiting

3. **Мониторинг**
   - Просмотр логов в реальном времени
   - Проверка использования ресурсов

## Troubleshooting

### Контейнер не запускается
```bash
docker-compose logs <service-name>
```

### Проблемы с Redis
```bash
docker-compose restart redis
```

### Пересоздание контейнеров
```bash
docker-compose down -v
docker-compose up -d --build
```

### Очистка Docker
```bash
# Удалить все остановленные контейнеры
docker container prune

# Удалить неиспользуемые образы
docker image prune

# Полная очистка
docker system prune -a
```
