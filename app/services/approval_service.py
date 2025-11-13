"""
Approval Service для управления процессом утверждения этапов генерации видео.

Этот модуль предоставляет ApprovalManager для координации утверждений пользователем
различных этапов генерации (сценарий, изображения, видео) через PostgreSQL.
"""

import time
import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import Config

logger = logging.getLogger(__name__)

Base = declarative_base()


class ApprovalStatus(Base):
    """Модель для хранения статусов утверждений в PostgreSQL."""
    __tablename__ = 'approval_statuses'
    __table_args__ = {'schema': Config.DATABASE_SCHEMA}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), nullable=False, index=True)
    approval_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # 'approved' or 'cancelled'
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class ApprovalManager:
    """
    Менеджер для управления утверждениями этапов генерации видео.
    
    Использует PostgreSQL для хранения статусов утверждений с TTL 15 минут.
    Поддерживает три типа утверждений: 'script', 'images', 'videos'.
    """
    
    # Константы
    APPROVAL_TIMEOUT = 600  # 10 минут в секундах
    POLL_INTERVAL = 2  # 2 секунды между проверками
    APPROVAL_TTL_MINUTES = 15  # 15 минут TTL
    
    # Возможные статусы
    STATUS_APPROVED = "approved"
    STATUS_CANCELLED = "cancelled"
    
    def __init__(self, db_session: Session = None):
        """
        Инициализация ApprovalManager с PostgreSQL сессией.
        
        Args:
            db_session: SQLAlchemy сессия (опционально, создается автоматически)
        """
        if db_session:
            self.session = db_session
            self._owns_session = False
        else:
            engine = create_engine(Config.DATABASE_URL)
            # Создаем таблицу если не существует
            Base.metadata.create_all(engine, checkfirst=True)
            SessionLocal = sessionmaker(bind=engine)
            self.session = SessionLocal()
            self._owns_session = True
        
        logger.info("ApprovalManager initialized with PostgreSQL")
    
    def __del__(self):
        """Закрытие сессии при удалении объекта."""
        if self._owns_session and hasattr(self, 'session'):
            self.session.close()
    
    def _cleanup_expired(self):
        """Удаление истекших записей из базы данных."""
        try:
            now = datetime.utcnow()
            self.session.query(ApprovalStatus).filter(
                ApprovalStatus.expires_at < now
            ).delete()
            self.session.commit()
        except Exception as e:
            logger.error(f"Error cleaning up expired approvals: {e}")
            self.session.rollback()
    
    def wait_for_approval(
        self, 
        job_id: str, 
        approval_type: str, 
        timeout: int = None
    ) -> bool:
        """
        Ожидание утверждения от пользователя с polling PostgreSQL.
        
        Проверяет базу данных каждые 2 секунды на наличие статуса утверждения.
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
            
            # Проверка статуса в базе данных
            try:
                approval = self.session.query(ApprovalStatus).filter(
                    ApprovalStatus.job_id == job_id,
                    ApprovalStatus.approval_type == approval_type,
                    ApprovalStatus.expires_at > datetime.utcnow()
                ).first()
                
                if approval:
                    if approval.status == self.STATUS_APPROVED:
                        logger.info(
                            f"Approval received: job_id={job_id}, type={approval_type}, "
                            f"elapsed={elapsed_time:.1f}s"
                        )
                        return True
                    
                    elif approval.status == self.STATUS_CANCELLED:
                        logger.info(
                            f"Approval cancelled: job_id={job_id}, type={approval_type}, "
                            f"elapsed={elapsed_time:.1f}s"
                        )
                        return False
            
            except Exception as e:
                logger.error(f"Error checking approval status: {e}")
                self.session.rollback()
            
            # Ожидание перед следующей проверкой
            time.sleep(self.POLL_INTERVAL)
    
    def approve(self, job_id: str, approval_type: str) -> None:
        """
        Утверждение этапа генерации.
        
        Устанавливает статус "approved" в PostgreSQL с TTL 15 минут.
        
        Args:
            job_id: Уникальный идентификатор задачи
            approval_type: Тип утверждения ('script', 'images', 'videos')
        """
        try:
            # Удаляем старую запись если существует
            self.session.query(ApprovalStatus).filter(
                ApprovalStatus.job_id == job_id,
                ApprovalStatus.approval_type == approval_type
            ).delete()
            
            # Создаем новую запись
            expires_at = datetime.utcnow() + timedelta(minutes=self.APPROVAL_TTL_MINUTES)
            approval = ApprovalStatus(
                job_id=job_id,
                approval_type=approval_type,
                status=self.STATUS_APPROVED,
                expires_at=expires_at
            )
            self.session.add(approval)
            self.session.commit()
            
            logger.info(
                f"Approval set: job_id={job_id}, type={approval_type}, status=approved"
            )
            
            # Очистка истекших записей
            self._cleanup_expired()
            
        except Exception as e:
            logger.error(f"Error setting approval: {e}")
            self.session.rollback()
            raise
    
    def cancel(self, job_id: str, approval_type: str) -> None:
        """
        Отмена задачи генерации.
        
        Устанавливает статус "cancelled" в PostgreSQL с TTL 15 минут.
        
        Args:
            job_id: Уникальный идентификатор задачи
            approval_type: Тип утверждения ('script', 'images', 'videos')
        """
        try:
            # Удаляем старую запись если существует
            self.session.query(ApprovalStatus).filter(
                ApprovalStatus.job_id == job_id,
                ApprovalStatus.approval_type == approval_type
            ).delete()
            
            # Создаем новую запись
            expires_at = datetime.utcnow() + timedelta(minutes=self.APPROVAL_TTL_MINUTES)
            approval = ApprovalStatus(
                job_id=job_id,
                approval_type=approval_type,
                status=self.STATUS_CANCELLED,
                expires_at=expires_at
            )
            self.session.add(approval)
            self.session.commit()
            
            logger.info(
                f"Approval cancelled: job_id={job_id}, type={approval_type}, status=cancelled"
            )
            
            # Очистка истекших записей
            self._cleanup_expired()
            
        except Exception as e:
            logger.error(f"Error setting cancellation: {e}")
            self.session.rollback()
            raise
    
    def is_approved(self, job_id: str, approval_type: str) -> Optional[bool]:
        """
        Проверка текущего статуса утверждения.
        
        Args:
            job_id: Уникальный идентификатор задачи
            approval_type: Тип утверждения ('script', 'images', 'videos')
            
        Returns:
            True если утверждено, False если отменено, None если статус не установлен
        """
        try:
            approval = self.session.query(ApprovalStatus).filter(
                ApprovalStatus.job_id == job_id,
                ApprovalStatus.approval_type == approval_type,
                ApprovalStatus.expires_at > datetime.utcnow()
            ).first()
            
            if approval is None:
                return None
            
            if approval.status == self.STATUS_APPROVED:
                return True
            elif approval.status == self.STATUS_CANCELLED:
                return False
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking approval status: {e}")
            self.session.rollback()
            return None
