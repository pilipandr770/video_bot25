"""
Approval Service для управления процессом утверждения этапов генерации видео.

Этот модуль предоставляет ApprovalManager для координации утверждений пользователем
различных этапов генерации (сценарий, изображения, видео) через Redis.
"""

import time
import logging
from typing import Optional
from redis import Redis

logger = logging.getLogger(__name__)


class ApprovalManager:
    """
    Менеджер для управления утверждениями этапов генерации видео.
    
    Использует Redis для хранения статусов утверждений с TTL 15 минут.
    Поддерживает три типа утверждений: 'script', 'images', 'videos'.
    """
    
    # Константы
    APPROVAL_TIMEOUT = 600  # 10 минут в секундах
    POLL_INTERVAL = 2  # 2 секунды между проверками
    REDIS_TTL = 900  # 15 минут в секундах
    
    # Возможные статусы
    STATUS_APPROVED = "approved"
    STATUS_CANCELLED = "cancelled"
    
    def __init__(self, redis_client: Redis):
        """
        Инициализация ApprovalManager с Redis клиентом.
        
        Args:
            redis_client: Экземпляр Redis клиента для хранения состояний
        """
        self.redis = redis_client
        logger.info("ApprovalManager initialized")
    
    def _get_redis_key(self, job_id: str, approval_type: str) -> str:
        """
        Генерация Redis ключа для утверждения.
        
        Args:
            job_id: Уникальный идентификатор задачи
            approval_type: Тип утверждения ('script', 'images', 'videos')
            
        Returns:
            Строка формата "approval:{job_id}:{type}"
        """
        return f"approval:{job_id}:{approval_type}"
    
    def wait_for_approval(
        self, 
        job_id: str, 
        approval_type: str, 
        timeout: int = None
    ) -> bool:
        """
        Ожидание утверждения от пользователя с polling Redis.
        
        Проверяет Redis каждые 2 секунды на наличие статуса утверждения.
        Возвращает True если утверждено, False если отменено или истек timeout.
        
        Args:
            job_id: Уникальный идентификатор задачи
            approval_type: Тип утверждения ('script', 'images', 'videos')
            timeout: Время ожидания в секундах (по умолчанию 10 минут)
            
        Returns:
            True если утверждено, False если отменено или timeout
        """
        if timeout is None:
            timeout = self.APPROVAL_TIMEOUT
        
        redis_key = self._get_redis_key(job_id, approval_type)
        start_time = time.time()
        
        logger.info(
            f"Waiting for approval: job_id={job_id}, type={approval_type}, timeout={timeout}s"
        )
        
        while True:
            elapsed_time = time.time() - start_time
            
            # Проверка timeout
            if elapsed_time >= timeout:
                logger.warning(
                    f"Approval timeout: job_id={job_id}, type={approval_type}, "
                    f"elapsed={elapsed_time:.1f}s"
                )
                return False
            
            # Проверка статуса в Redis
            status = self.redis.get(redis_key)
            
            if status:
                status_str = status.decode('utf-8') if isinstance(status, bytes) else status
                
                if status_str == self.STATUS_APPROVED:
                    logger.info(
                        f"Approval received: job_id={job_id}, type={approval_type}, "
                        f"elapsed={elapsed_time:.1f}s"
                    )
                    return True
                
                elif status_str == self.STATUS_CANCELLED:
                    logger.info(
                        f"Approval cancelled: job_id={job_id}, type={approval_type}, "
                        f"elapsed={elapsed_time:.1f}s"
                    )
                    return False
            
            # Ожидание перед следующей проверкой
            time.sleep(self.POLL_INTERVAL)
    
    def approve(self, job_id: str, approval_type: str) -> None:
        """
        Утверждение этапа генерации.
        
        Устанавливает статус "approved" в Redis с TTL 15 минут.
        
        Args:
            job_id: Уникальный идентификатор задачи
            approval_type: Тип утверждения ('script', 'images', 'videos')
        """
        redis_key = self._get_redis_key(job_id, approval_type)
        
        self.redis.setex(
            redis_key,
            self.REDIS_TTL,
            self.STATUS_APPROVED
        )
        
        logger.info(
            f"Approval set: job_id={job_id}, type={approval_type}, status=approved"
        )
    
    def cancel(self, job_id: str, approval_type: str) -> None:
        """
        Отмена задачи генерации.
        
        Устанавливает статус "cancelled" в Redis с TTL 15 минут.
        
        Args:
            job_id: Уникальный идентификатор задачи
            approval_type: Тип утверждения ('script', 'images', 'videos')
        """
        redis_key = self._get_redis_key(job_id, approval_type)
        
        self.redis.setex(
            redis_key,
            self.REDIS_TTL,
            self.STATUS_CANCELLED
        )
        
        logger.info(
            f"Approval cancelled: job_id={job_id}, type={approval_type}, status=cancelled"
        )
    
    def is_approved(self, job_id: str, approval_type: str) -> Optional[bool]:
        """
        Проверка текущего статуса утверждения.
        
        Args:
            job_id: Уникальный идентификатор задачи
            approval_type: Тип утверждения ('script', 'images', 'videos')
            
        Returns:
            True если утверждено, False если отменено, None если статус не установлен
        """
        redis_key = self._get_redis_key(job_id, approval_type)
        status = self.redis.get(redis_key)
        
        if status is None:
            return None
        
        status_str = status.decode('utf-8') if isinstance(status, bytes) else status
        
        if status_str == self.STATUS_APPROVED:
            return True
        elif status_str == self.STATUS_CANCELLED:
            return False
        
        return None
