# 🚀 Быстрый деплой Enhanced Pipeline

## Локальное тестирование

### 1. Применить миграцию БД

```bash
python apply_enhanced_migration.py
```

### 2. Проверить переменные окружения

```bash
# Проверить .env файл
cat .env | grep OPENAI_.*_ASSISTANT_ID
```

Должны быть все три:
```
OPENAI_SCRIPT_ASSISTANT_ID=asst_1Yu1uxDttuH0t3Oux7V09BZt
OPENAI_SEGMENT_ASSISTANT_ID=asst_bKhMND0deCZKS6IyPMbm6uW6
OPENAI_ANIMATION_ASSISTANT_ID=asst_HWZcPW86OtN7YgC1frNLhKuo
```

### 3. Обновить импорты в webhook.py

Откройте `app/bot/webhook.py` и замените:

```python
# Было:
from app.bot.handlers import handle_start, handle_message, handle_voice, handle_callback_query

# Стало:
from app.bot.handlers_enhanced import (
    handle_start, 
    handle_message, 
    handle_status, 
    handle_approve, 
    handle_reject
)
```

### 4. Запустить локально

```bash
# Терминал 1 - Web
python run_web.py

# Терминал 2 - Worker
python run_worker.py
```

### 5. Протестировать

1. Отправьте боту: "Реклама кофе"
2. Проверьте, что появились кнопки: Статус, Старт, Подтвердить, Отклонить
3. Нажмите "Статус" — должен показать прогресс
4. Дождитесь сценария и нажмите "Подтвердить"
5. Следите за прогрессом через кнопку "Статус"

---

## Деплой на Render

### 1. Закоммитить изменения

```bash
git add .
git commit -m "feat: Enhanced pipeline with 3 assistants and detailed tracking"
git push origin main
```

### 2. Применить миграцию на Render

Вариант A - через Shell:
1. Render Dashboard → Web Service → Shell
2. Выполнить:
```bash
python apply_enhanced_migration.py
```

Вариант B - через psql:
1. Render Dashboard → PostgreSQL → Connect
2. Скопировать External Database URL
3. Локально:
```bash
psql "postgresql://ittoken_db_user:...@dpg-.../ittoken_db" < migrations/create_enhanced_tables.sql
```

### 3. Проверить переменные окружения на Render

Render Dashboard → Web Service → Environment:

```
OPENAI_SCRIPT_ASSISTANT_ID=asst_1Yu1uxDttuH0t3Oux7V09BZt
OPENAI_SEGMENT_ASSISTANT_ID=asst_bKhMND0deCZKS6IyPMbm6uW6
OPENAI_ANIMATION_ASSISTANT_ID=asst_HWZcPW86OtN7YgC1frNLhKuo
```

Render Dashboard → Worker Service → Environment (те же переменные)

### 4. Перезапустить сервисы

Render автоматически перезапустит после git push, но можно вручную:
- Web Service → Manual Deploy → Deploy latest commit
- Worker Service → Manual Deploy → Deploy latest commit

### 5. Проверить логи

Web Service → Logs:
```
✅ Enhanced pipeline initialized
✅ 3 OpenAI assistants configured
✅ Database tables verified
```

Worker Service → Logs:
```
[INFO/MainProcess] celery@... ready.
[INFO/MainProcess] Connected to postgresql://...
```

### 6. Протестировать в продакшене

1. Отправьте боту сообщение
2. Проверьте кнопки
3. Проверьте статус
4. Дождитесь завершения генерации

---

## Проверка что всё работает

### ✅ Чеклист:

- [ ] Миграция БД применена (таблицы `video_jobs_enhanced`, `video_segments_enhanced` созданы)
- [ ] Все 3 ассистента настроены в .env и на Render
- [ ] Импорты обновлены в `webhook.py`
- [ ] Код закоммичен и запушен
- [ ] Web service запущен без ошибок
- [ ] Worker service запущен без ошибок
- [ ] Бот отвечает на сообщения
- [ ] Кнопки отображаются (Статус, Старт, Подтвердить, Отклонить)
- [ ] Кнопка "Статус" показывает прогресс
- [ ] Генерация проходит все этапы
- [ ] Финальное видео отправляется пользователю

---

## Быстрые команды

```bash
# Проверить статус сервисов
curl https://video-bot25.onrender.com/health

# Посмотреть последние задачи в БД
psql $DATABASE_URL -c "SELECT id, status, created_at FROM ai_video_bot.video_jobs_enhanced ORDER BY created_at DESC LIMIT 5;"

# Посмотреть прогресс по сегментам
psql $DATABASE_URL -c "SELECT job_id, COUNT(*) as total, SUM(CASE WHEN image_path IS NOT NULL THEN 1 ELSE 0 END) as images, SUM(CASE WHEN video_path IS NOT NULL THEN 1 ELSE 0 END) as videos FROM ai_video_bot.video_segments_enhanced GROUP BY job_id;"

# Очистить старые задачи (старше 24 часов)
psql $DATABASE_URL -c "DELETE FROM ai_video_bot.video_jobs_enhanced WHERE created_at < NOW() - INTERVAL '24 hours';"
```

---

## Откат на старую версию (если что-то пошло не так)

### 1. Вернуть старые импорты

```python
# В app/bot/webhook.py
from app.bot.handlers import handle_start, handle_message, handle_voice, handle_callback_query
```

### 2. Вернуть старую задачу

```python
# В app/bot/handlers.py
from app.tasks.video_generation import generate_video_task  # вместо generate_video_enhanced_task
```

### 3. Закоммитить и запушить

```bash
git add .
git commit -m "revert: Rollback to old pipeline"
git push origin main
```

Новые таблицы можно оставить — они не мешают старой версии.

---

**Готово!** 🎉

Теперь у вас:
- ✅ 3 специализированных ассистента
- ✅ Детальное отслеживание в БД
- ✅ Постоянные кнопки управления
- ✅ Пошаговая генерация с сохранением прогресса
