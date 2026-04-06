# ✅ ИСПРАВЛЕННЫЙ ФАЙЛ: bot/middleware/topic_discoverer.py

from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Dict, Any, Awaitable
import logging

logger = logging.getLogger(__name__)

class TopicDiscovererMiddleware(BaseMiddleware):
    """
    Middleware, который автоматически обнаруживает темы форума
    и использует названия из конфига или БД.
    """
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        try:
            # Проверяем тип события
            if hasattr(event, 'message') and event.message is not None:
                message = event.message
                
                # Проверяем, есть ли в сообщении информация о теме
                if hasattr(message, 'message_thread_id') and message.message_thread_id:
                    message_thread_id = message.message_thread_id
                    
                    # Получаем название темы из конфига или генерируем
                    topic_name = self._get_topic_name(message_thread_id)
                    
                    # Сохраняем тему
                    from database import save_forum_topic
                    await save_forum_topic(message_thread_id, topic_name)
                    logger.info(f"✅ Обнаружена тема: '{topic_name}' (ID: {message_thread_id})")
        except Exception as e:
            logger.error(f"❌ Ошибка в middleware: {e}", exc_info=True)
        
        return await handler(event, data)
    
    def _get_topic_name(self, thread_id: int) -> str:
        """
        Получает название темы из конфига.
        """
        try:
            from topics_config import TOPICS_MAPPING
            
            if thread_id in TOPICS_MAPPING:
                name = TOPICS_MAPPING[thread_id]
                logger.info(f"Используется название из конфига: {name}")
                return name
            else:
                logger.warning(f"ID темы {thread_id} не в конфиге, используется ID как название")
                return f"Тема {thread_id}"
        except ImportError:
            logger.warning("topics_config.py не найден, используется ID как название")
            return f"Тема {thread_id}"
        except Exception as e:
            logger.warning(f"Ошибка при получении названия: {e}")
            return f"Тема {thread_id}"