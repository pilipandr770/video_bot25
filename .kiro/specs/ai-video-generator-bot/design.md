# Документ Дизайна

## Обзор

Система представляет собой Flask веб-приложение, развернутое на Render.com, которое автоматически генерирует 50-секундные рекламные видеоролики на основе текстового или голосового описания пользователя через Telegram бота. Архитектура построена на асинхронной обработке запросов с использованием внешних AI-сервисов (OpenAI, Runway) и FFmpeg для финальной сборки видео.

**Тестовая версия:** 10 сегментов × 5 секунд = 50 секунд (intro: 15 сек, main: 25 сек, outro: 10 сек)

### Ключевые Технологии

- **Backend**: Flask (Python 3.11+)
- **Telegram Integration**: python-telegram-bot
- **AI Services**: OpenAI API (Assistant, Whisper, TTS), Runway API
- **Video Processing**: FFmpeg
- **Deployment**: Render.com
- **Storage**: Временное файловое хранилище
- **Task Queue**: Celery + Redis (для асинхронной обработки)

## Архитектура

### Высокоуровневая Архитектура

```
┌─────────────┐
│  Telegram   │
│    User     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Telegram Bot API                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Flask Web Application              │
│  ┌────────────────────────────────┐    │
│  │   Webhook Handler              │    │
│  └────────────┬───────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌────────────────────────────────┐    │
│  │   Message Processor            │    │
│  └────────────┬───────────────────┘    │
│               │                         │
│               ▼                         │
│  ┌────────────────────────────────┐    │
│  │   Celery Task Queue            │    │
│  └────────────┬───────────────────┘    │
└───────────────┼─────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│         Video Generation Pipeline         │
│                                           │
│  ┌─────────────────────────────────┐    │
│  │  1. Script Generator            │    │
│  │     (OpenAI Assistant)          │    │
│  └──────────┬──────────────────────┘    │
│             │                            │
│             ▼                            │
│  ┌─────────────────────────────────┐    │
│  │  2. Image Generator             │    │
│  │     (Runway API)                │    │
│  └──────────┬──────────────────────┘    │
│             │                            │
│             ▼                            │
│  ┌─────────────────────────────────┐    │
│  │  3. Video Animator              │    │
│  │     (Runway API)                │    │
│  └──────────┬──────────────────────┘    │
│             │                            │
│             ▼                            │
│  ┌─────────────────────────────────┐    │
│  │  4. Audio Generator             │    │
│  │     (OpenAI TTS)                │    │
│  └──────────┬──────────────────────┘    │
│             │                            │
│             ▼                            │
│  ┌─────────────────────────────────┐    │
│  │  5. Video Assembler             │    │
│  │     (FFmpeg)                    │    │
│  └──────────┬──────────────────────┘    │
└─────────────┼───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│      Telegram Bot API                   │
│   (Send Final Video to User)            │
└─────────────────────────────────────────┘
```

### Структура Проекта

```
ai-video-generator-bot/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Конфигурация приложения
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py           # Обработчики Telegram команд
│   │   ├── webhook.py            # Webhook endpoint
│   │   └── notifications.py      # Отправка статусных сообщений
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py    # OpenAI API интеграция
│   │   ├── runway_service.py    # Runway API интеграция
│   │   ├── script_service.py    # Генерация и разбивка сценария
│   │   ├── video_service.py     # Генерация видео сегментов
│   │   └── audio_service.py     # Генерация аудио
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── video_generation.py  # Celery задачи
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── ffmpeg.py            # FFmpeg операции
│   │   ├── file_manager.py      # Управление временными файлами
│   │   └── validators.py        # Валидация входных данных
│   └── models/
│       ├── __init__.py
│       └── video_job.py         # Модель задачи генерации
├── bin/
│   └── ffmpeg/                  # FFmpeg бинарники
│       ├── ffmpeg               # (Linux x64)
│       ├── ffprobe              # (Linux x64)
│       └── README.md            # Инструкции по загрузке
├── temp/                        # Временные файлы
├── requirements.txt
├── Dockerfile
├── render.yaml                  # Конфигурация Render.com
└── main.py                      # Точка входа приложения
```

## Компоненты и Интерфейсы

### 1. Telegram Bot Handler

**Назначение**: Прием и валидация входящих сообщений от пользователей

**Основные Методы**:
```python
class TelegramHandler:
    def handle_message(update: Update, context: CallbackContext) -> None:
        """Обработка текстовых сообщений"""
        
    def handle_voice(update: Update, context: CallbackContext) -> None:
        """Обработка голосовых сообщений"""
        
    def handle_start(update: Update, context: CallbackContext) -> None:
        """Обработка команды /start"""
        
    def handle_callback_query(update: Update, context: CallbackContext) -> None:
        """Обработка нажатий на inline кнопки (утверждение/отмена)"""
```

**Интерфейс**:
- Входные данные: Telegram Update объект
- Выходные данные: Подтверждение получения, запуск Celery задачи

**Callback Data Format**:
```python
# Формат callback_data для inline кнопок
"approve_script:{job_id}"
"cancel_script:{job_id}"
"approve_images:{job_id}"
"cancel_images:{job_id}"
"approve_videos:{job_id}"
"cancel_videos:{job_id}"
```

### 2. Message Processor

**Назначение**: Валидация и подготовка данных для обработки

**Основные Методы**:
```python
class MessageProcessor:
    def validate_message_type(message: Message) -> MessageType:
        """Определение типа сообщения (текст/голос)"""
        
    def extract_text(message: Message) -> str:
        """Извлечение текста из сообщения"""
        
    def transcribe_voice(voice_file: File) -> str:
        """Транскрибация голосового сообщения через Whisper"""
```

### 3. OpenAI Service

**Назначение**: Интеграция с OpenAI API для генерации сценария, транскрибации и TTS

**Основные Методы**:
```python
class OpenAIService:
    def __init__(self, api_key: str, script_assistant_id: str, segment_assistant_id: str, animation_assistant_id: str):
        """Инициализация с API ключом и тремя специализированными Assistant IDs"""
        
    def generate_script(self, prompt: str) -> str:
        """Генерация сценария через Script Assistant"""
        
    def split_and_generate_prompts(self, script: str) -> List[SegmentWithPrompts]:
        """Разбивка сценария и генерация промптов через Segment Assistant"""
        
    def generate_animation_prompt(self, segment_text: str) -> str:
        """Генерация промпта анимации через Animation Assistant"""
        
    def transcribe_audio(self, audio_file: bytes) -> str:
        """Транскрибация аудио через Whisper API"""
        
    def generate_speech(self, text: str, voice: str = "alloy") -> bytes:
        """Генерация аудио через TTS API"""
```

**Обработка Ошибок**:
- Retry логика с экспоненциальной задержкой (3 попытки)
- Обработка rate limits
- Логирование всех запросов и ответов

### 4. Script Service

**Назначение**: Разбивка сценария на 5-секундные сегменты

**Основные Методы**:
```python
class ScriptService:
    def split_script(self, script: str, target_duration: int = 240) -> List[ScriptSegment]:
        """Разделение сценария на сегменты по 5 секунд"""
        
    def generate_image_prompt(self, segment: ScriptSegment) -> str:
        """Генерация промпта для изображения на основе сегмента"""
        
    def generate_animation_prompt(self, segment: ScriptSegment) -> str:
        """Генерация промпта для анимации на основе сегмента"""
```

**Логика Разбивки**:
- Целевая длительность: 50 секунд (тестовая версия)
- Количество сегментов: 10 (50 / 5)
- Структура: 3 intro (15 сек) + 4 main (20 сек) + 3 outro (15 сек)
- Каждый сегмент содержит: текст, порядковый номер, временную метку, тип (intro/main/outro)

### 5. Runway Service

**Назначение**: Интеграция с Runway API для генерации изображений и анимации

**Основные Методы**:
```python
class RunwayService:
    def __init__(self, api_key: str):
        """Инициализация с API ключом"""
        
    def generate_image(self, prompt: str) -> str:
        """Генерация изображения, возвращает task_id"""
        
    def animate_image(self, image_url: str, animation_prompt: str) -> str:
        """Анимация изображения, возвращает task_id"""
        
    def check_task_status(self, task_id: str) -> TaskStatus:
        """Проверка статуса задачи (polling)"""
        
    def download_result(self, task_id: str, output_path: str) -> str:
        """Скачивание готового результата"""
```

**Асинхронная Обработка**:
- Polling каждые 5 секунд для проверки статуса
- Timeout: 5 минут на задачу
- Retry логика: 2 попытки при ошибке

### 6. Video Service

**Назначение**: Координация генерации всех видео сегментов

**Основные Методы**:
```python
class VideoService:
    def __init__(self, runway_service: RunwayService, script_service: ScriptService):
        """Инициализация с зависимостями"""
        
    def generate_all_segments(
        self, 
        segments: List[ScriptSegment],
        progress_callback: Callable
    ) -> List[VideoSegment]:
        """Генерация всех видео сегментов с отслеживанием прогресса"""
        
    def generate_segment(self, segment: ScriptSegment) -> VideoSegment:
        """Генерация одного видео сегмента (изображение + анимация)"""
```

**Оптимизация**:
- Параллельная генерация до 3 сегментов одновременно
- Кэширование промежуточных результатов
- Прогресс-бар для пользователя (каждые 5 сегментов для 10-сегментной версии)

### 7. Audio Service

**Назначение**: Генерация аудиодорожки для видео

**Основные Методы**:
```python
class AudioService:
    def __init__(self, openai_service: OpenAIService):
        """Инициализация с OpenAI сервисом"""
        
    def generate_audio(self, script: str, target_duration: int = 50) -> str:
        """Генерация аудио файла с целевой длительностью (50 сек для тестовой версии)"""
        
    def adjust_audio_duration(self, audio_path: str, target_duration: int) -> str:
        """Корректировка длительности аудио через FFmpeg"""
```

### 8. FFmpeg Utility

**Назначение**: Сборка финального видео из сегментов и аудио

**Основные Методы**:
```python
class FFmpegUtil:
    def __init__(self, ffmpeg_path: str = None):
        """
        Инициализация с путем к FFmpeg бинарнику
        По умолчанию использует ./bin/ffmpeg/ffmpeg
        """
        self.ffmpeg_path = ffmpeg_path or self._get_ffmpeg_path()
        self.ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
        
    @staticmethod
    def _get_ffmpeg_path() -> str:
        """Определение пути к FFmpeg бинарнику"""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_dir, 'bin', 'ffmpeg', 'ffmpeg')
    
    def concatenate_videos(self, video_paths: List[str], output_path: str) -> str:
        """Объединение видео сегментов в один файл"""
        
    def add_audio(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Добавление аудиодорожки к видео"""
        
    def compress_video(self, input_path: str, output_path: str, max_size_mb: int = 50) -> str:
        """Сжатие видео до указанного размера"""
        
    def get_video_duration(self, video_path: str) -> float:
        """Получение длительности видео"""
```

**FFmpeg Команды**:
```bash
# Объединение видео (используя локальный бинарник)
./bin/ffmpeg/ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4

# Добавление аудио
./bin/ffmpeg/ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4

# Сжатие видео
./bin/ffmpeg/ffmpeg -i input.mp4 -vcodec libx264 -crf 28 -preset fast output.mp4
```

**Установка FFmpeg**:
FFmpeg бинарники должны быть загружены в директорию `bin/ffmpeg/` перед развертыванием. Для Linux x64 (Render.com):
```bash
# Скачивание FFmpeg static build
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*-amd64-static/ffmpeg bin/ffmpeg/
cp ffmpeg-*-amd64-static/ffprobe bin/ffmpeg/
chmod +x bin/ffmpeg/ffmpeg bin/ffmpeg/ffprobe
```

### 9. File Manager

**Назначение**: Управление временными файлами

**Основные Методы**:
```python
class FileManager:
    def __init__(self, temp_dir: str = "temp"):
        """Инициализация с директорией для временных файлов"""
        
    def create_job_directory(self, job_id: str) -> str:
        """Создание директории для задачи"""
        
    def save_file(self, job_id: str, filename: str, content: bytes) -> str:
        """Сохранение файла"""
        
    def cleanup_job(self, job_id: str) -> None:
        """Удаление всех файлов задачи"""
        
    def cleanup_old_files(self, max_age_hours: int = 1) -> None:
        """Удаление файлов старше указанного времени"""
```

### 10. Approval System

**Назначение**: Управление процессом утверждения этапов генерации

**Основные Компоненты**:
```python
class ApprovalManager:
    def __init__(self, redis_client):
        """Инициализация с Redis для хранения состояния утверждений"""
        self.redis = redis_client
        
    def wait_for_approval(self, job_id: str, approval_type: str, timeout: int = 600) -> bool:
        """
        Ожидание утверждения от пользователя
        approval_type: 'script', 'images', 'videos'
        timeout: 10 минут по умолчанию
        Возвращает True если утверждено, False если отменено или timeout
        """
        
    def approve(self, job_id: str, approval_type: str) -> None:
        """Утверждение этапа"""
        
    def cancel(self, job_id: str, approval_type: str) -> None:
        """Отмена задачи"""
        
    def is_approved(self, job_id: str, approval_type: str) -> Optional[bool]:
        """Проверка статуса утверждения"""
```

**Redis Keys**:
```python
# Ключи для хранения статусов утверждений
f"approval:{job_id}:script"  # "approved", "cancelled", или None
f"approval:{job_id}:images"
f"approval:{job_id}:videos"
```

### 11. Notification Service

**Назначение**: Отправка статусных сообщений и запросов на утверждение

**Основные Методы**:
```python
class NotificationService:
    def send_status_update(self, chat_id: int, status: JobStatus) -> None:
        """Отправка обновлений статуса"""
        
    def send_progress_update(self, chat_id: int, current: int, total: int) -> None:
        """Отправка процента выполнения"""
        
    def send_error_message(self, chat_id: int, error_type: str) -> None:
        """Отправка понятных сообщений об ошибках"""
        
    def send_final_video(self, chat_id: int, video_path: str) -> None:
        """Отправка готового видео пользователю"""
        
    def send_script_approval(self, chat_id: int, job_id: str, script: str) -> None:
        """Отправка сценария с кнопками утверждения"""
        
    def send_images_approval(self, chat_id: int, job_id: str, image_paths: List[str]) -> None:
        """Отправка превью изображений (первые 3) с кнопками утверждения"""
        
    def send_videos_approval(self, chat_id: int, job_id: str, video_paths: List[str]) -> None:
        """Отправка превью видео (первые 2) с кнопками утверждения"""
```

**Inline Keyboards**:
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Кнопки утверждения сценария
keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ Утвердить", callback_data=f"approve_script:{job_id}"),
        InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_script:{job_id}")
    ]
])

# Кнопки утверждения изображений
keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ Утвердить изображения", callback_data=f"approve_images:{job_id}"),
        InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_images:{job_id}")
    ]
])

# Кнопки утверждения видео
keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ Утвердить видео", callback_data=f"approve_videos:{job_id}"),
        InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_videos:{job_id}")
    ]
])
```

### 12. Celery Tasks

**Назначение**: Асинхронная обработка генерации видео с точками утверждения

**Основная Задача**:
```python
@celery.task(bind=True, max_retries=3)
def generate_video_task(
    self,
    job_id: str,
    user_id: int,
    chat_id: int,
    prompt: str
) -> None:
    """
    Главная задача генерации видео с утверждениями
    
    Этапы:
    1. Генерация сценария
    2. ⏸️ ОЖИДАНИЕ УТВЕРЖДЕНИЯ СЦЕНАРИЯ
    3. Генерация изображений
    4. ⏸️ ОЖИДАНИЕ УТВЕРЖДЕНИЯ ИЗОБРАЖЕНИЙ
    5. Анимация изображений
    6. ⏸️ ОЖИДАНИЕ УТВЕРЖДЕНИЯ ВИДЕО
    7. Генерация аудио
    8. Сборка финального видео
    9. Отправка пользователю
    10. Очистка временных файлов
    """
```

## Модели Данных

### VideoJob

```python
@dataclass
class VideoJob:
    job_id: str
    user_id: int
    chat_id: int
    prompt: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    script: Optional[str] = None
    segments: List[ScriptSegment] = field(default_factory=list)
    video_segments: List[VideoSegment] = field(default_factory=list)
    audio_path: Optional[str] = None
    final_video_path: Optional[str] = None
    error_message: Optional[str] = None
```

### ScriptSegment

```python
@dataclass
class ScriptSegment:
    index: int
    text: str
    start_time: float
    end_time: float
    image_prompt: str
    animation_prompt: str
```

### VideoSegment

```python
@dataclass
class VideoSegment:
    index: int
    script_segment: ScriptSegment
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    runway_image_task_id: Optional[str] = None
    runway_video_task_id: Optional[str] = None
    status: SegmentStatus = SegmentStatus.PENDING
```

### JobStatus

```python
class JobStatus(Enum):
    PENDING = "pending"
    GENERATING_SCRIPT = "generating_script"
    AWAITING_SCRIPT_APPROVAL = "awaiting_script_approval"
    SCRIPT_APPROVED = "script_approved"
    GENERATING_IMAGES = "generating_images"
    AWAITING_IMAGES_APPROVAL = "awaiting_images_approval"
    IMAGES_APPROVED = "images_approved"
    ANIMATING_VIDEOS = "animating_videos"
    AWAITING_VIDEOS_APPROVAL = "awaiting_videos_approval"
    VIDEOS_APPROVED = "videos_approved"
    GENERATING_AUDIO = "generating_audio"
    ASSEMBLING_VIDEO = "assembling_video"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
```

## Обработка Ошибок

### Стратегия Retry

1. **OpenAI API**:
   - Retry: 3 попытки
   - Backoff: Экспоненциальный (1s, 2s, 4s)
   - Обработка rate limits: Ожидание согласно Retry-After header

2. **Runway API**:
   - Retry: 2 попытки
   - Backoff: Линейный (5s, 10s)
   - Timeout: 5 минут на задачу

3. **FFmpeg**:
   - Retry: 1 попытка
   - Fallback: Сжатие с более агрессивными параметрами

### Логирование Ошибок

```python
import logging

logger = logging.getLogger(__name__)

# Структурированное логирование
logger.error(
    "Failed to generate video segment",
    extra={
        "job_id": job_id,
        "segment_index": segment.index,
        "error": str(e),
        "retry_count": retry_count
    }
)
```

### Уведомления Пользователя

```python
ERROR_MESSAGES = {
    "openai_rate_limit": "⏳ Сервис временно перегружен. Пожалуйста, попробуйте через несколько минут.",
    "runway_timeout": "⚠️ Генерация видео заняла слишком много времени. Попробуйте упростить описание.",
    "ffmpeg_error": "❌ Ошибка при сборке видео. Пожалуйста, попробуйте еще раз.",
    "general_error": "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз или обратитесь в поддержку."
}
```

## Стратегия Тестирования

### Unit Tests

- Тестирование отдельных сервисов с mock объектами
- Тестирование утилит (FFmpeg, FileManager)
- Тестирование валидаторов

### Integration Tests

- Тестирование взаимодействия с Telegram Bot API (с test bot)
- Тестирование Celery задач
- Тестирование pipeline генерации (с mock AI сервисами)

### End-to-End Tests

- Полный цикл генерации видео с реальными API (в staging окружении)
- Тестирование различных сценариев ошибок
- Тестирование производительности

### Тестовые Данные

```python
# Пример тестового промпта
TEST_PROMPT = "Создай рекламу для нового смартфона с акцентом на камеру и батарею"

# Mock ответ от OpenAI Assistant
MOCK_SCRIPT = """
Сегмент 1: Открывающий кадр с логотипом
Сегмент 2: Демонстрация камеры
...
Сегмент 48: Призыв к действию
"""
```

## Развертывание на Render.com

### Конфигурация render.yaml

```yaml
services:
  - type: web
    name: ai-video-bot
    env: python
    region: oregon
    plan: standard
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn main:app
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: OPENAI_ASSISTANT_ID
        sync: false
      - key: RUNWAY_API_KEY
        sync: false
      - key: REDIS_URL
        fromService:
          type: redis
          name: ai-video-redis
          property: connectionString
    disk:
      name: temp-storage
      mountPath: /app/temp
      sizeGB: 10

  - type: redis
    name: ai-video-redis
    region: oregon
    plan: starter
    maxmemoryPolicy: allkeys-lru

  - type: worker
    name: ai-video-worker
    env: python
    region: oregon
    plan: standard
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.tasks.celery worker --loglevel=info
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: OPENAI_ASSISTANT_ID
        sync: false
      - key: RUNWAY_API_KEY
        sync: false
      - key: REDIS_URL
        fromService:
          type: redis
          name: ai-video-redis
          property: connectionString
    disk:
      name: worker-temp-storage
      mountPath: /app/temp
      sizeGB: 20
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание директории для временных файлов
RUN mkdir -p /app/temp

# Установка прав на выполнение для FFmpeg бинарников
RUN chmod +x /app/bin/ffmpeg/ffmpeg /app/bin/ffmpeg/ffprobe

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "main:app"]
```

**Примечание**: FFmpeg бинарники должны быть добавлены в репозиторий в директорию `bin/ffmpeg/` перед сборкой Docker образа. Это позволяет использовать FFmpeg без установки через apt-get и обеспечивает полный контроль над версией.

### Переменные Окружения

```python
# app/config.py
import os

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
    
    # Runway
    RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Application
    TEMP_DIR = os.getenv("TEMP_DIR", "/app/temp")
    MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))
    FILE_CLEANUP_HOURS = int(os.getenv("FILE_CLEANUP_HOURS", "1"))
    
    # FFmpeg
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "/app/bin/ffmpeg/ffmpeg")
    FFPROBE_PATH = os.getenv("FFPROBE_PATH", "/app/bin/ffmpeg/ffprobe")
    
    # Video Settings (already defined above, remove duplicates)
    MAX_VIDEO_SIZE_MB = 50  # Лимит Telegram
```

## Оптимизация Производительности

### 1. Параллельная Генерация

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_all_segments(segments: List[ScriptSegment]) -> List[VideoSegment]:
    video_segments = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(generate_segment, seg): seg 
            for seg in segments
        }
        
        for future in as_completed(futures):
            video_segment = future.result()
            video_segments.append(video_segment)
            
            # Отправка прогресса каждые 10 сегментов
            if len(video_segments) % 10 == 0:
                send_progress_update(len(video_segments), len(segments))
    
    return sorted(video_segments, key=lambda x: x.index)
```

### 2. Кэширование

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def generate_image_prompt(segment_text: str) -> str:
    """Кэширование промптов для похожих сегментов"""
    return f"Professional advertising image: {segment_text}"
```

### 3. Оптимизация FFmpeg

```python
# Использование hardware acceleration если доступно
FFMPEG_HWACCEL = "-hwaccel auto"

# Оптимизированные параметры кодирования
FFMPEG_ENCODE_PARAMS = "-c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k"
```

## Мониторинг и Логирование

### Структура Логов

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "video_generation_started",
    job_id=job_id,
    user_id=user_id,
    prompt_length=len(prompt)
)

logger.info(
    "segment_generated",
    job_id=job_id,
    segment_index=segment.index,
    duration_seconds=duration
)

logger.info(
    "video_generation_completed",
    job_id=job_id,
    total_duration_seconds=total_duration,
    final_video_size_mb=file_size
)
```

### Метрики

- Время генерации на каждом этапе
- Количество успешных/неудачных задач
- Размер финальных видео
- Использование дискового пространства
- Количество активных задач

## Безопасность

### 1. Валидация Входных Данных

```python
def validate_message(message: Message) -> bool:
    # Проверка типа сообщения
    if not (message.text or message.voice):
        return False
    
    # Проверка размера голосового сообщения (макс 20 МБ)
    if message.voice and message.voice.file_size > 20 * 1024 * 1024:
        return False
    
    return True
```

### 2. Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.json.get("message", {}).get("from", {}).get("id"),
    default_limits=["5 per minute", "20 per hour"]
)
```

### 3. Защита API Ключей

- Все ключи хранятся в переменных окружения
- Никогда не логируются в plaintext
- Используется Render.com secret management

### 4. Очистка Временных Файлов

```python
# Scheduled task для очистки старых файлов
@celery.task
def cleanup_old_files():
    file_manager = FileManager()
    file_manager.cleanup_old_files(max_age_hours=1)
```

## Масштабирование

### Горизонтальное Масштабирование

- Увеличение количества Celery workers на Render.com
- Использование Redis для координации между workers
- Stateless архитектура Flask приложения

### Вертикальное Масштабирование

- Увеличение ресурсов worker instances (CPU, RAM)
- Увеличение дискового пространства для временных файлов
- Оптимизация параллельной обработки

### Ограничения

- Максимум 5 одновременных задач генерации
- Очередь задач в Redis
- Уведомление пользователя о времени ожидания

## Будущие Улучшения

1. **Кэширование Результатов**: Сохранение готовых видео для похожих промптов
2. **Webhook для Runway**: Замена polling на webhook для быстрой обработки
3. **Предпросмотр**: Отправка превью первых сегментов до завершения всего видео
4. **Пользовательские Настройки**: Выбор голоса TTS, стиля видео, длительности
5. **База Данных**: PostgreSQL для хранения истории задач и аналитики
6. **CDN**: Использование S3 + CloudFront для хранения и доставки видео
7. **Мультиязычность**: Поддержка генерации видео на разных языках
