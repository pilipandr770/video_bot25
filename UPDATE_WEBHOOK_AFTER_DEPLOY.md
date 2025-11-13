# 🔄 Обновление Webhook после деплоя на Render

## После успешного деплоя на Render.com

### Шаг 1: Получите URL вашего сервиса

1. Откройте Render Dashboard
2. Перейдите в сервис **ai-video-bot-web**
3. Скопируйте URL (например: `https://ai-video-bot-web.onrender.com`)

### Шаг 2: Обновите переменную окружения

1. В Render Dashboard откройте **ai-video-bot-web**
2. Перейдите в раздел **Environment**
3. Найдите переменную `TELEGRAM_WEBHOOK_URL`
4. Измените значение на ваш Render URL:
   ```
   https://ai-video-bot-web.onrender.com
   ```
5. Нажмите **Save Changes**
6. Render автоматически перезапустит сервис (~30 секунд)

### Шаг 3: Проверьте webhook

Выполните команду:
```bash
python check_webhook.py
```

Или вручную:
```bash
curl https://api.telegram.org/bot<ВАШ_ТОКЕН>/getWebhookInfo
```

Вы должны увидеть:
```json
{
  "ok": true,
  "result": {
    "url": "https://ai-video-bot-web.onrender.com/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### Шаг 4: Проверьте health endpoint

```bash
curl https://ai-video-bot-web.onrender.com/health
```

Ожидаемый ответ:
```json
{"service":"ai-video-generator-bot","status":"healthy"}
```

### Шаг 5: Протестируйте бота

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте `/start`
4. Бот должен ответить приветствием

### Шаг 6: Проверьте логи

В Render Dashboard:
1. Откройте **ai-video-bot-web** → **Logs**
2. Вы должны увидеть:
   ```
   telegram_webhook_configured webhook_url=https://...
   incoming_request method=POST path=/webhook
   ```

---

## Troubleshooting

### Webhook не устанавливается

**Проблема:** После обновления `TELEGRAM_WEBHOOK_URL` webhook все еще не установлен.

**Решение:**
1. Проверьте, что URL правильный (HTTPS, не HTTP)
2. Проверьте логи Web Service на наличие ошибок
3. Вручную установите webhook:
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://ai-video-bot-web.onrender.com/webhook"
   ```

### Бот не отвечает

**Проблема:** Webhook установлен, но бот не отвечает на сообщения.

**Решение:**
1. Проверьте логи Web Service
2. Убедитесь, что все переменные окружения настроены
3. Проверьте, что Redis подключен
4. Перезапустите сервис вручную

### Ошибка "Webhook not found"

**Проблема:** Telegram не может достучаться до webhook URL.

**Решение:**
1. Убедитесь, что сервис запущен и доступен
2. Проверьте health endpoint
3. Проверьте, что порт 5000 открыт (Render делает это автоматически)

### Pending updates не обрабатываются

**Проблема:** Есть pending updates, но они не обрабатываются.

**Решение:**
1. Удалите webhook: `curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook"`
2. Установите заново: `curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://..."`
3. Или используйте `drop_pending_updates=true`:
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://...&drop_pending_updates=true"
   ```

---

## Автоматическая установка webhook

Приложение автоматически устанавливает webhook при запуске, если:
1. `TELEGRAM_WEBHOOK_URL` установлен в переменных окружения
2. URL доступен и валиден
3. Telegram API доступен

Проверьте логи при запуске:
```
configuration_validated
telegram_webhook_configured webhook_url=https://...
application_initialized
```

---

## Полезные команды

### Проверить webhook
```bash
python check_webhook.py
```

### Установить webhook вручную
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://ai-video-bot-web.onrender.com/webhook"
```

### Удалить webhook
```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

### Получить информацию о боте
```bash
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Получить pending updates
```bash
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
```

---

## Мониторинг

После настройки webhook следите за:

1. **Логи Web Service** - incoming webhook requests
2. **Логи Worker Service** - video generation tasks
3. **Redis Metrics** - connections и memory usage
4. **Response Time** - должно быть < 2 секунды

---

## Готово! 🎉

После выполнения всех шагов ваш бот должен:
- ✅ Получать сообщения через webhook
- ✅ Отвечать на команды
- ✅ Запускать генерацию видео
- ✅ Отправлять уведомления о прогрессе

Отправьте боту описание видео и проверьте работу!
