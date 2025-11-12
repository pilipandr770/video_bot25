# План Реализации

## Завершенные задачи

- [x] 1. Настройка базовой структуры проекта и конфигурации





  - Создать структуру директорий согласно дизайну (app/, bin/, temp/)
  - Создать requirements.txt с необходимыми зависимостями (Flask, python-telegram-bot, openai, celery, redis, gunicorn)
  - Создать app/config.py с классом Config для управления переменными окружения
  - Создать main.py как точку входа Flask приложения
  - _Requirements: 11.4, 11.5_

- [x] 2. Загрузка и настройка FFmpeg





  - Создать директорию bin/ffmpeg/
  - Создать скрипт для загрузки FFmpeg static build для Linux x64
  - Добавить README.md в bin/ffmpeg/ с инструкциями
  - Создать app/utils/ffmpeg.py с классом FFmpegUtil
  - Реализовать методы concatenate_videos, add_audio, compress_video, get_video_duration
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 3. Реализация File Manager для управления временными файлами




  - Создать app/utils/file_manager.py с классом FileManager
  - Реализовать create_job_directory для создания директорий задач
  - Реализовать save_file для сохранения файлов
  - Реализовать cleanup_job для удаления файлов задачи
  - Реализовать cleanup_old_files для автоматической очистки старых файлов
  - _Requirements: 12.1, 12.2, 10.5_

- [x] 4. Создание моделей данных




  - Создать app/models/video_job.py
  - Реализовать dataclass VideoJob с полями job_id, user_id, chat_id, prompt, status, timestamps
  - Реализовать dataclass ScriptSegment с полями index, text, start_time, end_time, prompts
  - Реализовать dataclass VideoSegment с полями index, paths, task_ids, status
  - Реализовать enum JobStatus с состояниями задачи
  - Реализовать enum SegmentStatus с состояниями сегмента
  - _Requirements: 3.3, 3.4_

- [x] 5. Интеграция с OpenAI API





  - Создать app/services/openai_service.py с классом OpenAIService
  - Реализовать __init__ с инициализацией OpenAI client (api_key, assistant_id)
  - Реализовать generate_script для генерации сценария через OpenAI Assistant
  - Реализовать transcribe_audio для транскрибации голосовых сообщений через Whisper
  - Реализовать generate_speech для генерации аудио через TTS API
  - Добавить retry логику с экспоненциальной задержкой (3 попытки)
  - Добавить обработку rate limits и ошибок API
  - _Requirements: 2.4, 2.5, 3.1, 3.5, 6.2, 6.3_

- [x] 6. Интеграция с Runway API





  - Создать app/services/runway_service.py с классом RunwayService
  - Реализовать __init__ с инициализацией Runway client (api_key)
  - Реализовать generate_image для создания изображения по промпту
  - Реализовать animate_image для анимации изображения
  - Реализовать check_task_status для polling статуса задачи
  - Реализовать download_result для скачивания готового результата
  - Добавить retry логику (2 попытки) и timeout (5 минут)
  - _Requirements: 4.2, 4.3, 4.7, 5.2, 5.3, 5.7_
-


- [x] 7. Реализация Script Service для обработки сценариев

















  - Создать app/services/script_service.py с классом ScriptService
  - Реализовать split_script для разделения сценария на 48 сегментов по 5 секунд
  - Реализовать generate_image_prompt для создания промпта изображения из сегмента
  - Реализовать generate_animation_prompt для создания промпта анимации из сегмента
  - Добавить логику расчета временных меток для каждого сегмента
  - _Requirements: 3.3, 3.4, 4.1, 5.1_

- [x] 8. Реализация Video Service для генерации видео сегментов




  - Создать app/services/video_service.py с классом VideoService
  - Реализовать generate_all_segments с параллельной обработкой (ThreadPoolExecutor, max_workers=3)
  - Реализовать generate_segment для генерации одного сегмента (изображение + анимация)
  - Добавить progress_callback для отправки обновлений каждые 10 сегментов
  - Интегрировать RunwayService и ScriptService
  - _Requirements: 4.4, 4.5, 4.6, 5.4, 5.5, 5.6_

- [x] 9. Реализация Audio Service для генерации озвучки





  - Создать app/services/audio_service.py с классом AudioService
  - Реализовать generate_audio для создания аудиофайла из полного сценария
  - Реализовать adjust_audio_duration для корректировки длительности через FFmpeg
  - Интегрировать OpenAIService для TTS
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 10. Настройка Celery и Redis для асинхронной обработки




  - Создать app/tasks/__init__.py с инициализацией Celery app
  - Настроить подключение к Redis через REDIS_URL
  - Настроить Celery broker и backend
  - Создать scheduled task для cleanup_old_files (каждый час)
  - _Requirements: 12.5_

- [x] 10A. Реализация системы утверждения этапов





  - Создать app/services/approval_service.py с классом ApprovalManager
  - Реализовать wait_for_approval с polling Redis каждые 2 секунды и timeout 10 минут
  - Реализовать approve для установки статуса "approved" в Redis
  - Реализовать cancel для установки статуса "cancelled" в Redis
  - Реализовать is_approved для проверки текущего статуса
  - Использовать Redis keys формата "approval:{job_id}:{type}" с TTL 15 минут
  - _Requirements: 3A.3, 3A.4, 3A.5, 4A.3, 4A.4, 4A.5, 5A.3, 5A.4, 5A.5_

- [x] 11. Реализация главной Celery задачи генерации видео с утверждениями





  - Создать app/tasks/video_generation.py
  - Реализовать generate_video_task как главную Celery задачу
  - Добавить этап 1: генерация сценария через OpenAI Assistant
  - Добавить этап 2: отправка сценария на утверждение и ожидание ответа (wait_for_approval)
  - Добавить проверку: если отменено, остановить задачу и очистить файлы
  - Добавить этап 3: генерация изображений через Runway API
  - Добавить этап 4: отправка превью изображений (первые 5) на утверждение и ожидание ответа
  - Добавить проверку: если отменено, остановить задачу и очистить файлы
  - Добавить этап 5: анимация изображений через Runway API
  - Добавить этап 6: отправка превью видео (первые 3) на утверждение и ожидание ответа
  - Добавить проверку: если отменено, остановить задачу и очистить файлы
  - Добавить этап 7: генерация аудио через OpenAI TTS
  - Добавить этап 8: сборка финального видео через FFmpeg
  - Добавить этап 9: отправка готового видео пользователю
  - Добавить этап 10: финальная очистка временных файлов
  - Интегрировать все сервисы (OpenAI, Runway, Script, Video, Audio, FFmpeg, Approval)
  - Добавить отправку статусных обновлений пользователю на каждом этапе
  - Добавить обработку ошибок и retry логику (max_retries=3)
  - _Requirements: 3.1, 3.2, 3A.1-3A.5, 4.1-4.7, 4A.1-4A.5, 5.1-5.7, 5A.1-5A.5, 6.1-6.5, 7.1-7.5, 8.5, 9.1-9.5_

- [x] 12. Реализация Telegram Bot handlers





  - Создать app/bot/handlers.py
  - Реализовать handle_start для команды /start с приветственным сообщением
  - Реализовать handle_message для обработки текстовых сообщений
  - Реализовать handle_voice для обработки голосовых сообщений
  - Реализовать handle_callback_query для обработки нажатий на inline кнопки
  - Добавить парсинг callback_data (approve_script, cancel_script, approve_images, cancel_images, approve_videos, cancel_videos)
  - Добавить вызов ApprovalManager.approve() или ApprovalManager.cancel() в зависимости от действия
  - Добавить валидацию типа сообщения (текст или голос)
  - Добавить запуск Celery задачи generate_video_task
  - Добавить отправку подтверждения пользователю с оценкой времени
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3A.2, 3A.3, 3A.4, 4A.2, 4A.3, 4A.4, 5A.2, 5A.3, 5A.4, 9.1_

- [x] 13. Реализация системы уведомлений с утверждениями





  - Создать app/bot/notifications.py
  - Реализовать send_status_update для отправки обновлений статуса
  - Реализовать send_progress_update для отправки процента выполнения
  - Реализовать send_error_message для отправки понятных сообщений об ошибках
  - Реализовать send_final_video для отправки готового видео пользователю
  - Реализовать send_script_approval для отправки сценария с inline кнопками (✅ Утвердить, ❌ Отменить)
  - Реализовать send_images_approval для отправки галереи из первых 5 изображений с inline кнопками
  - Реализовать send_videos_approval для отправки первых 3 видео сегментов с inline кнопками
  - Добавить словарь ERROR_MESSAGES с понятными текстами ошибок
  - Использовать InlineKeyboardMarkup и InlineKeyboardButton для создания кнопок
  - _Requirements: 3A.1, 3A.2, 4A.1, 4A.2, 5A.1, 5A.2, 8.1, 8.2, 8.4, 9.2, 9.3, 9.4, 9.5, 10.2, 10.3_

- [x] 14. Настройка Telegram webhook





  - Создать app/bot/webhook.py с Flask endpoint для webhook
  - Реализовать обработку входящих updates от Telegram
  - Добавить валидацию webhook запросов
  - Настроить маршрутизацию к соответствующим handlers
  - _Requirements: 1.1, 2.1_

- [x] 15. Реализация валидаторов





  - Создать app/utils/validators.py
  - Реализовать validate_message для проверки типа сообщения
  - Реализовать validate_voice_size для проверки размера голосового сообщения (макс 20 МБ)
  - _Requirements: 1.2, 2.2_

- [x] 16. Добавление rate limiting




  - Установить flask-limiter в requirements.txt
  - Настроить Limiter в main.py (5 запросов в минуту, 20 в час на пользователя)
  - Добавить обработку превышения лимита с уведомлением пользователя
  - _Requirements: 12.3, 12.4_

- [x] 17. Настройка логирования и мониторинга





  - Настроить structlog в main.py
  - Добавить логирование всех ключевых операций (старт задачи, генерация сегментов, ошибки)
  - Добавить логирование метрик (время выполнения, размер файлов)
  - Настроить уровни логирования (INFO для production, DEBUG для development)
  - _Requirements: 10.1, 11.5_

- [x] 18. Создание Dockerfile





  - Создать Dockerfile с базовым образом python:3.11-slim
  - Добавить копирование requirements.txt и установку зависимостей
  - Добавить копирование приложения и FFmpeg бинарников
  - Добавить создание директории temp/
  - Добавить установку прав на выполнение для FFmpeg
  - Настроить gunicorn как CMD с параметрами (workers=2, timeout=300)
  - _Requirements: 11.1, 11.3_

- [x] 19. Создание конфигурации для Render.com





  - Создать render.yaml с конфигурацией для трех сервисов
  - Настроить web service (Flask app) с gunicorn
  - Настроить worker service (Celery worker)
  - Настроить redis service
  - Добавить переменные окружения (TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, OPENAI_ASSISTANT_ID, RUNWAY_API_KEY)
  - Настроить disk storage для temp файлов (10 GB для web, 20 GB для worker)
  - Настроить автоматическое развертывание при push в main ветку
  - _Requirements: 11.1, 11.2, 11.4_

- [x] 20. Интеграция всех компонентов в main.py




  - Создать Flask app с инициализацией всех компонентов
  - Зарегистрировать webhook endpoint
  - Настроить Telegram bot с webhook URL
  - Добавить health check endpoint для Render.com
  - Добавить graceful shutdown для очистки ресурсов
  - _Requirements: 11.1_

- [x] 21. Создание .gitignore и README.md





  - Создать .gitignore с исключением temp/, .env, __pycache__, *.pyc
  - Создать README.md с описанием проекта, инструкциями по установке и развертыванию
  - Добавить инструкции по настройке переменных окружения
  - Добавить инструкции по загрузке FFmpeg бинарников
  - _Requirements: 11.1_

- [x] 22. Финальная интеграция и проверка pipeline
  - Проверить полный flow от получения сообщения до отправки видео
  - Проверить обработку ошибок на каждом этапе
  - Проверить очистку временных файлов после завершения
  - Проверить rate limiting и ограничение одновременных задач
  - Проверить сжатие видео если размер превышает 50 МБ
  - _Requirements: 8.3, 10.5, 12.3_

## Оставшиеся задачи

- [ ] 23. Загрузка FFmpeg бинарников
  - Выполнить скрипт bin/ffmpeg/download_ffmpeg.sh для загрузки FFmpeg static build
  - Проверить наличие ffmpeg и ffprobe бинарников в bin/ffmpeg/
  - Установить права на выполнение (chmod +x)
  - Проверить работу FFmpeg командой ./bin/ffmpeg/ffmpeg -version
  - _Requirements: 7.1, 7.2_

- [ ] 24. Интеграция notification service в video generation task
  - Заменить placeholder функции (_send_status_notification, _send_progress_notification и т.д.) в app/tasks/video_generation.py
  - Импортировать NotificationService из app.bot.notifications
  - Создать экземпляр NotificationService в generate_video_task
  - Использовать реальные методы NotificationService вместо placeholder логирования
  - Добавить async/await обработку для всех notification вызовов
  - _Requirements: 8.1, 8.2, 8.4, 9.2, 9.3, 9.4, 9.5_

- [ ] 25. Реализация обработки голосовых сообщений в video generation task
  - Добавить проверку на специальный маркер "__VOICE_MESSAGE__|{file_id}" в prompt
  - Если обнаружен маркер, загрузить голосовой файл через Telegram API
  - Вызвать openai_service.transcribe_audio для распознавания речи
  - Использовать распознанный текст как prompt для дальнейшей обработки
  - Добавить обработку ошибок транскрибации с понятным сообщением пользователю
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 26. Разделение генерации изображений и анимации в video service
  - Модифицировать VideoService.generate_segment для раздельной генерации изображений и анимации
  - Создать метод generate_images_only для генерации только изображений (этап 3)
  - Создать метод animate_images_only для анимации существующих изображений (этап 5)
  - Обновить generate_video_task для использования раздельных методов
  - Сохранять промежуточные результаты (image_path) перед анимацией
  - _Requirements: 4.1-4.7, 5.1-5.7_

- [x] 27. Создание файлов конфигурации окружения


  - Создать .env.example файл с примерами всех необходимых переменных для GitHub
  - Создать .env файл для локальной разработки с placeholder значениями
  - Документировать процесс получения TELEGRAM_BOT_TOKEN (через @BotFather)
  - Документировать процесс получения OPENAI_API_KEY и OPENAI_ASSISTANT_ID
  - Документировать процесс получения RUNWAY_API_KEY
  - Добавить инструкции по настройке TELEGRAM_WEBHOOK_URL
  - _Requirements: 11.4_

- [ ] 28. Локальное тестирование в Docker
  - Запустить Redis контейнер для локального тестирования
  - Собрать Docker образ приложения
  - Запустить Flask web контейнер
  - Запустить Celery worker контейнер
  - Проверить health check endpoint
  - Проверить подключение к Redis
  - Проверить логи всех контейнеров
  - Протестировать базовую функциональность (если API ключи настроены)
  - _Requirements: 11.1, 11.3_

- [ ] 29. Deployment на Render.com
  - Создать аккаунт на Render.com и подключить GitHub репозиторий
  - Настроить три сервиса согласно render.yaml (web, worker, redis)
  - Добавить все необходимые environment variables в настройках Render
  - Настроить disk storage для временных файлов
  - Дождаться успешного build и deployment всех сервисов
  - Проверить health check endpoint (https://your-app.onrender.com/health)
  - Настроить Telegram webhook через API (setWebhook)
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 30. Финальное тестирование в production
  - Отправить тестовое текстовое сообщение боту
  - Проверить получение и утверждение сценария
  - Проверить получение и утверждение изображений
  - Проверить получение и утверждение видео
  - Проверить получение финального видео
  - Отправить тестовое голосовое сообщение боту
  - Проверить транскрибацию и генерацию видео
  - Проверить rate limiting (отправить > 5 сообщений в минуту)
  - Проверить обработку ошибок (отправить невалидные данные)
  - Проверить автоматическую очистку временных файлов
  - Мониторить логи в Render.com для выявления проблем
  - _Requirements: 1.1-1.3, 2.1-2.3, 8.1-8.5, 9.1-9.5, 10.1-10.5, 12.1-12.5_
