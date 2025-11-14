# 🔧 Настройка переменных окружения на Render

## Обязательные переменные для обоих сервисов

### Web Service (ai-video-bot-web)

1. Откройте https://dashboard.render.com
2. Выберите сервис `ai-video-bot-web`
3. Перейдите в раздел **Environment**
4. Добавьте/обновите следующие переменные:

```
TELEGRAM_BOT_TOKEN=<your_bot_token_from_botfather>
TELEGRAM_WEBHOOK_URL=https://video-bot25.onrender.com/webhook
OPENAI_API_KEY=<your_openai_api_key>
OPENAI_SCRIPT_ASSISTANT_ID=<your_script_assistant_id>
OPENAI_SEGMENT_ASSISTANT_ID=<your_segment_assistant_id>
OPENAI_ANIMATION_ASSISTANT_ID=<your_animation_assistant_id>
RUNWAY_API_KEY=<your_runway_api_key>
```

**Примечание:** Остальные переменные уже настроены в `render.yaml`

---

### Worker Service (ai-video-bot-worker)

1. Откройте https://dashboard.render.com
2. Выберите сервис `ai-video-bot-worker`
3. Перейдите в раздел **Environment**
4. Добавьте/обновите следующие переменные:

```
TELEGRAM_BOT_TOKEN=<your_bot_token_from_botfather>
OPENAI_API_KEY=<your_openai_api_key>
OPENAI_SCRIPT_ASSISTANT_ID=<your_script_assistant_id>
OPENAI_SEGMENT_ASSISTANT_ID=<your_segment_assistant_id>
OPENAI_ANIMATION_ASSISTANT_ID=<your_animation_assistant_id>
RUNWAY_API_KEY=<your_runway_api_key>
```

---

## ⚠️ Важно: Создание OpenAI Assistants

Сейчас у вас есть только **Script Assistant**. Нужно создать еще два:

### 1. Segment Assistant

1. Откройте https://platform.openai.com/playground
2. Создайте нового Assistant
3. Скопируйте инструкции из `.kiro/specs/ai-video-generator-bot/segment-assistant-instructions.md`
4. Сохраните и скопируйте ID (начинается с `asst_`)
5. Обновите `OPENAI_SEGMENT_ASSISTANT_ID` на Render

### 2. Animation Assistant

1. Откройте https://platform.openai.com/playground
2. Создайте нового Assistant
3. Скопируйте инструкции из `.kiro/specs/ai-video-generator-bot/animation-assistant-instructions.md`
4. Сохраните и скопируйте ID (начинается с `asst_`)
5. Обновите `OPENAI_ANIMATION_ASSISTANT_ID` на Render

---

## 🚀 После настройки переменных

1. **Сохраните изменения** в Environment
2. **Render автоматически перезапустит** оба сервиса
3. **Подождите 2-3 минуты** пока сервисы запустятся
4. **Проверьте логи** обоих сервисов на наличие ошибок

---

## ✅ Проверка что Worker запущен

### Проверка через Dashboard:

1. Откройте https://dashboard.render.com
2. Найдите сервис `ai-video-bot-worker`
3. Статус должен быть **Live** (зеленый)
4. В логах должно быть:

```
[INFO/MainProcess] Connected to sqla+postgresql://...
[INFO/MainProcess] mingle: searching for neighbors
[INFO/MainProcess] mingle: all alone
[INFO/MainProcess] celery@... ready.
```

### Проверка через бота:

1. Отправьте текст боту (например, "Реклама кофе")
2. Бот должен ответить: "✅ Ваш запрос принят!"
3. Через 10-30 секунд должно прийти: "📝 Генерирую сценарий..."
4. Затем сценарий с кнопками одобрения

---

## 🐛 Troubleshooting

### Worker не запускается

**Проверьте логи worker'а:**
```
Error: No module named 'app'
```

**Решение:** Убедитесь, что Dockerfile правильно копирует папку `app/`

---

### "Failed to create job in database"

**Проверьте:**
- `DATABASE_URL` одинаковый для web и worker
- `DATABASE_SCHEMA=ai_video_bot` установлен

**Решение:** Проверьте переменные окружения в обоих сервисах

---

### "OpenAI Assistant ID is required"

**Проверьте:**
- `OPENAI_SCRIPT_ASSISTANT_ID` установлен
- ID начинается с `asst_`

**Решение:** Создайте Assistant в OpenAI Playground и скопируйте ID

---

## 📊 Мониторинг

### Логи Web Service:
```
video_generation_started job_id=...
video_job_created_in_db job_id=...
```

### Логи Worker Service:
```
[INFO/MainProcess] Task app.tasks.generate_video[...] received
stage_started stage=generate_script
stage_completed stage=generate_script
```

---

**Дата создания:** 13 ноября 2025
